from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from .models import Restaurant, MenuItem, User, SearchForm, Rating
from . import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from markupsafe import escape
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import asc
import re
import logging
from werkzeug.serving import WSGIRequestHandler

main = Blueprint('main', __name__)
csrf = CSRFProtect()

WSGIRequestHandler.log = lambda *args, **kwargs: None

# Create a logger and set its level to the desired logging level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and set its level to the desired logging level
file_handler = logging.FileHandler('log_file.txt')
file_handler.setLevel(logging.INFO)

# Create a formatter for the log messages
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Set the formatter for the file handler
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

#input sanitisation code to prevent injection sequences 
def sanitise_input(input_string):
    sanitised_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return sanitised_string

@main.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@main.route('/')
@main.route('/restaurant/')
def showRestaurants():
    restaurants = Restaurant.query.order_by(Restaurant.name.asc())

    # Calculate average ratings for each restaurant
    average_ratings = {}
    for restaurant in restaurants:
        ratings = Rating.query.filter_by(restaurant_id=restaurant.id).all()
        average_rating = sum(rating.rating for rating in ratings) / len(ratings) if ratings else 0
        average_ratings[restaurant.id] = average_rating

    return render_template('restaurants.html', restaurants=restaurants, average_ratings=average_ratings, ratings=ratings)



#Fixed the below code that broke during other implementations 
#Create a new restaurant
@main.route('/restaurant/new/', methods=['GET', 'POST'])
@login_required 
def newRestaurant():
    if request.method == 'POST':
        newRestaurant = Restaurant(name=sanitise_input(request.form['name']), ownerid=current_user.id)   
        db.session.add(newRestaurant)
        db.session.commit()

        if current_user.role != 'admin':
            current_user.role = 'owner'
            db.session.commit()

        logger.info('Restaurant created by %s (ID: %s): %s' % (current_user.username, current_user.id, newRestaurant.name))

        flash('Hi %s, You\'ve successfully created the New Restaurant %s' % (current_user.username, newRestaurant.name))
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template('newRestaurant.html')


# Security for input sanitisation + error caused by changes  that i couldn't fix without the db.commit
@main.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
@login_required
def editRestaurant(restaurant_id):
    editedRestaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    if editedRestaurant.ownerid == current_user.id or current_user.role == 'admin':
        if request.method == 'POST':
            if request.form['name']:
                print("Old Name:", editedRestaurant.name)
                editedRestaurant.name = escape(request.form['name'])
                print("New Name:", editedRestaurant.name)
                flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
                
                logger.info('Restaurant edited by %s (ID: %s): %s' % (current_user.username, current_user.id, editedRestaurant.name))
                db.session.commit()
                return redirect(url_for('main.showRestaurants'))
        else:
            return render_template('editRestaurant.html', restaurant=editedRestaurant)
        
    else: 
        logger.info('Failed attempt to edit restaurant by %s (ID: %s): %s' % (current_user.username, current_user.id, editedRestaurant.name))
        flash('Sorry  %s You do not have permission to delete  %s' % (current_user.username, editedRestaurant.name))
        return render_template('menu.html',items =items, restaurant = editedRestaurant)

@main.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteRestaurant(restaurant_id):
    restaurantToDelete = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    if restaurantToDelete.ownerid == current_user.id or current_user.role == 'admin':
        if request.method == 'POST':
            if 'delete' in request.form:
                db.session.delete(restaurantToDelete)
                flash('%s Successfully Deleted' % restaurantToDelete.name)
                logger.info('Restaurant deleted by %s (ID: %s): %s' % (current_user.username, current_user.id, restaurant_id))
                db.session.commit()               
            return redirect(url_for('main.showRestaurants'))
        else:
            return render_template('deleteRestaurant.html', restaurant=restaurantToDelete)
    else: 
        logger.info('Failed attempt to delete restaurant by %s (ID: %s): %s' % (current_user.username, current_user.id, restaurant_id))
        flash('Sorry  %s You do not have permission to delete  %s' % (current_user.username, restaurantToDelete.name))
        return render_template('menu.html',items =items, restaurant = restaurantToDelete)
    


# Show a restaurant menu
@main.route('/restaurant/<int:restaurant_id>/menu', methods=['GET'])
def showMenu(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return render_template('menu.html', items=items, restaurant=restaurant)



#Create a new menu item
@main.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
@login_required
def newMenuItem(restaurant_id):
  restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
  if restaurant.ownerid == current_user.id or current_user.role == 'admin':
    if request.method == 'POST':
        #implemented input sanitsation again
        newItem = MenuItem(name = escape(request.form['name']), description = sanitise_input(request.form['description']), price = "$"+escape(request.form['price']), course = escape(request.form['course']), restaurant_id = restaurant_id)
        db.session.add(newItem)
        logger.info('Menu Item created by %s (ID: %s): %s' % (current_user.username, current_user.id, newItem.name))
        db.session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id = restaurant_id)
  else: 
      logger.info('Failed attempt to create menu item  by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
      flash('Sorry  %s You do not have permission to add a menu item to  %s' % (current_user.username, restaurant.name))
      return render_template('menu.html',items =items, restaurant = restaurant)

#Edit a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
@login_required
def editMenuItem(restaurant_id, menu_id):
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    editedItem = db.session.query(MenuItem).filter_by(id = menu_id).one()
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    if restaurant.ownerid == current_user.id or current_user.role == 'admin':
        if request.method == 'POST':
            #implemented input sanitsation again
            if request.form['name']:
                editedItem.name = escape(request.form['name'])
                logger.info('Menu item name edited by %s (ID: %s): %s' % (current_user.username, current_user.id, editedItem.name))
            if request.form['description']:
                editedItem.description = sanitise_input(request.form['description']) # no special characters needed so used custom function to keep it alpha numeric
                logger.info('Menu item description edited by %s (ID: %s): %s' % (current_user.username, current_user.id, editedItem.description))
            if request.form['price']:
                editedItem.price = escape(request.form['price'])
                logger.info('Menu item price edited by %s (ID: %s): %s' % (current_user.username, current_user.id, editedItem.price))
            if request.form['course']:
                editedItem.course = escape(request.form['course'])
                logger.info('Menu item course edited by %s (ID: %s): %s' % (current_user.username, current_user.id, editedItem.course))
            db.session.add(editedItem)
            db.session.commit() 
            flash('Menu Item Successfully Edited')
            return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
        else:
            return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)
    else: 
        logger.info('Failed attempt to edit menu item  by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry  %s You do not have permission to edit a menu item in   %s' % (current_user.username, restaurant.name))
        return render_template('menu.html',items =items, restaurant = restaurant)

#Delete a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDelete = db.session.query(MenuItem).filter_by(id=menu_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    if restaurant.ownerid == current_user.id or current_user.role == 'admin':
    
        if request.method == 'POST':
            if 'delete' in request.form:
                db.session.delete(itemToDelete)
                logger.info('Menu item deleted by %s (ID: %s): %s' % (current_user.username, current_user.id, itemToDelete.name))
                db.session.commit()
                flash('Menu Item Successfully Deleted')
            return redirect(url_for('main.showMenu', restaurant_id=restaurant_id))
        return render_template('deleteMenuItem.html', item=itemToDelete, restaurant=restaurant)
    else: 
        logger.info('Failed attempt to delete menu item by %s (ID: %s): %s' % (current_user.username, current_user.id, itemToDelete.name))
        flash('Sorry  %s You do not have permission to delete a menu item in  %s' % (current_user.username, restaurant.name))
        return render_template('menu.html',items =items, restaurant = restaurant)
    


#start of admin panel 
@main.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        logger.info('Failed attempt to access admin panel by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, %s. You do not have permission to access this part of the website.' % current_user.username, 'error')
        return redirect(url_for('main.showRestaurants'))

    users = User.query.all()
    restaurants = Restaurant.query.all()

    return render_template('admin.html', Users=users, restaurants=restaurants, User=User)
   
class EditUserForm(FlaskForm):
        role = SelectField('Role', choices=[('owner', 'Owner'), ('admin', 'Admin'), ('public', 'Public User')], validators=[DataRequired()])

class EditRestaurantOwnerForm(FlaskForm):
    ownerid = SelectField('Owner', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Owner')

    def __init__(self, *args, **kwargs):
        super(EditRestaurantOwnerForm, self).__init__(*args, **kwargs)
        self.ownerid.choices = [(user.id, user.username) for user in User.query.all()]




#adminPanel user edit interface
@main.route('/admin/edituser/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        logger.info('Failed attempt to edit user roles by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, %s. You do not have permission to edit user roles.' % current_user.username, 'error')
        return redirect(url_for('main.showRestaurants'))
    

    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        logger.info('Failed attempt to edit admin user by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, you cannot edit the role of the admin user.', 'error')
        return redirect(url_for('main.admin'))
    
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.role = form.role.data
        logger.info('user role updated by %s (ID: %s): %s' % (current_user.username, current_user.id, user.id))
        db.session.commit()
        flash('User role has been updated successfully.', 'success')
        return redirect(url_for('main.admin'))

    return render_template('edituser.html', form=form, user=user)

#admin panel delete user
@main.route('/admin/deleteuser/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        logger.info('Failed attempt to delete user by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, %s. You do not have permission to delete users.' % current_user.username, 'error')
        return redirect(url_for('main.showRestaurants'))
    
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        logger.info('Failed attempt to delete admin user by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, you cannot delete the admin user.', 'error')
        return redirect(url_for('main.admin'))
    
    # Update owner IDs of associated restaurants to the admin account
    restaurants = Restaurant.query.filter_by(ownerid=user.id).all()
    admin_user = User.query.filter_by(username='admin').first()

    for restaurant in restaurants:
        restaurant.ownerid = admin_user.id

    db.session.delete(user)
    logger.info('user deleted by %s (ID: %s): %s' % (current_user.username, current_user.id, user.id))
    db.session.commit()
    flash('User has been deleted successfully.', 'success')
    return redirect(url_for('main.admin'))

#admin panel for editing restaurant
@main.route('/admin/editrestaurant/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def edit_restaurant_owner(restaurant_id):
    if current_user.role != 'admin':
        logger.info('Failed attempt to edit restaurant owner by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, %s. You do not have permission to edit restaurant owners.' % current_user.username, 'error')
        return redirect(url_for('main.admin'))

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    form = EditRestaurantOwnerForm()

    if form.validate_on_submit():
        new_owner_id = form.ownerid.data

        if new_owner_id == restaurant.ownerid:
            flash('The selected user is already the owner of this restaurant.', 'warning')
        else:
            new_owner = User.query.get(new_owner_id)
            if not new_owner:
                flash('Invalid user selected.', 'error')
            else:
                restaurant.ownerid = new_owner_id
                logger.info('Restaurant owner updated by %s (ID: %s): %s' % (current_user.username, current_user.id, new_owner_id))
                db.session.commit()
                flash('Restaurant owner has been updated successfully.', 'success')

        return redirect(url_for('main.admin'))

    return render_template('editrestaurantowner.html', form=form, restaurant=restaurant)

#easier to make new function
@main.route('/admin/delete-restaurant/<int:restaurant_id>', methods=['POST'])
@login_required
def delete_restaurant(restaurant_id):
    if current_user.role != 'admin':
        logger.info('Failed attempt to delete restaurant by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
        flash('Sorry, %s. You do not have permission to delete restaurants.' % current_user.username, 'error')
        return redirect(url_for('main.admin'))

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    db.session.delete(restaurant)
    logger.info('Restaurant deleted by %s (ID: %s): %s' % (current_user.username, current_user.id, ''))
    db.session.commit()
    flash('Restaurant %s has been deleted successfully.' % restaurant.name, 'success')
    return redirect(url_for('main.admin'))


class RatingForm(FlaskForm):
    rating = SelectField('Rating', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                         validators=[DataRequired()])
    submit = SubmitField('Submit')



@main.route('/restaurant/<int:restaurant_id>/ratings', methods=['GET', 'POST'])
@login_required
def showRatings(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    ratings = Rating.query.filter_by(restaurant_id=restaurant_id).all()

    # Check if the user has already rated the restaurant
    user_rating = Rating.query.filter_by(restaurant_id=restaurant_id, user_id=current_user.id).first()

    if current_user.id != restaurant.ownerid:
        if request.method == 'POST':
            rating = int(request.form['rating'])

            if user_rating:
                # User has already rated the restaurant, update the existing rating
                user_rating.rating = rating
            else:
                # User has not rated the restaurant, create a new rating object
                new_rating = Rating(restaurant_id=restaurant_id, user_id=current_user.id, rating=rating)
                db.session.add(new_rating)
                logger.info('Restaurant rated by %s (ID: %s): %s' % (current_user.username, current_user.id, restaurant_id))

            db.session.commit()

            return redirect(url_for('main.showRatings', restaurant_id=restaurant_id))

    return render_template('ratings.html', restaurant=restaurant, ratings=ratings, user_rating=user_rating)

#search bar request code
@main.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    items = MenuItem.query
    restaurants = Restaurant.query
    if form.validate_on_submit():
        # Receive input from submitted search
        text_searched = sanitise_input(form.searched.data)
        if text_searched:
            # Query the Database
            items = items.filter(MenuItem.name.like('%' + text_searched + '%')).all()
            restaurants = restaurants.filter(Restaurant.name.like('%' + text_searched + '%')).all()
        else:
            # Handle blank search query
            flash('Please enter valid a search query.', 'warning')
            return redirect(url_for('main.showRestaurants'))
        # Redirect to the search results page
        logger.info('Search ed term %s' % (text_searched))
        return redirect(url_for('main.search_results', searched=text_searched))
    
    flash('Please enter a valid search query.', 'warning')
    return redirect(url_for('main.showRestaurants'))


#search results code 
@main.route('/search_results/<searched>')
def search_results(searched):
    items = MenuItem.query.filter(MenuItem.name.like('%' + searched + '%')).all()
    restaurants = Restaurant.query.filter(Restaurant.name.like('%' + searched + '%')).all()
    return render_template("search_results.html", searched=searched, items=items, restaurants=restaurants)