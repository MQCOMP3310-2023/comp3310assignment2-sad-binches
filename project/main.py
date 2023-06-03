from flask import Blueprint, app, render_template, request, flash, redirect, url_for, session, abort
from .models import Restaurant, MenuItem, User, SearchForm
from sqlalchemy import asc
from . import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
import re
from markupsafe import escape
from flask_login import login_user, login_required, logout_user, current_user
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Restaurant, MenuItem, SearchForm
from sqlalchemy import asc
from . import db
import re
from wtforms import SelectField

main = Blueprint('main', __name__)
csrf = CSRFProtect()

#input sanitisation code to prevent injection sequences 
def sanitise_input(input_string):
    sanitised_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return sanitised_string

@main.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

#Show all restaurants
@main.route('/')
@main.route('/restaurant/')
def showRestaurants():
  restaurants = db.session.query(Restaurant).order_by(asc(Restaurant.name))
  return render_template('restaurants.html', restaurants = restaurants)

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
                db.session.commit()
                return redirect(url_for('main.showRestaurants'))
        else:
            return render_template('editRestaurant.html', restaurant=editedRestaurant)
    else: 
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
                db.session.commit()
            return redirect(url_for('main.showRestaurants'))
        else:
            return render_template('deleteRestaurant.html', restaurant=restaurantToDelete)
    else: 
      flash('Sorry  %s You do not have permission to delete  %s' % (current_user.username, restaurantToDelete.name))
      return render_template('menu.html',items =items, restaurant = restaurantToDelete)
    


#Show a restaurant menu
@main.route('/restaurant/<int:restaurant_id>/')
@main.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return render_template('menu.html', items = items, restaurant = restaurant)
     


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
        db.session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id = restaurant_id)
  else: 
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
            if request.form['description']:
                editedItem.description = sanitise_input(request.form['description']) # no special characters needed so used custom function to keep it alpha numeric
            if request.form['price']:
                editedItem.price = escape(request.form['price'])
            if request.form['course']:
                editedItem.course = escape(request.form['course'])
            db.session.add(editedItem)
            db.session.commit() 
            flash('Menu Item Successfully Edited')
            return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
        else:
            return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)
    else: 
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
                db.session.commit()
                flash('Menu Item Successfully Deleted')
            return redirect(url_for('main.showMenu', restaurant_id=restaurant_id))
        return render_template('deleteMenuItem.html', item=itemToDelete, restaurant=restaurant)
    else: 
        flash('Sorry  %s You do not have permission to delete a menu item in  %s' % (current_user.username, restaurant.name))
        return render_template('menu.html',items =items, restaurant = restaurant)
    





@main.route('/admin/restaurant-owner/new', methods=['GET', 'POST'])
def newRestaurantOwner():
    if 'user_id' not in session:
        abort(401)  # Unauthorized access

    user = User.query.get(session['user_id'])
    if user.role != 'Administrator':
        abort(403)  # Access forbidden for non-administrators

    # Rest of the code for adding a new restaurant owner

    # Render the appropriate template or redirect as needed
    return render_template('new_restaurant_owner.html')



#start of admin panel 
@main.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
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
        flash('Sorry, %s. You do not have permission to edit user roles.' % current_user.username, 'error')
        return redirect(url_for('main.showRestaurants'))
    

    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Sorry, you cannot edit the role of the admin user.', 'error')
        return redirect(url_for('main.admin'))
    
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.role = form.role.data
        db.session.commit()
        flash('User role has been updated successfully.', 'success')
        return redirect(url_for('main.admin'))

    return render_template('edituser.html', form=form, user=user)


@main.route('/admin/deleteuser/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Sorry, %s. You do not have permission to delete users.' % current_user.username, 'error')
        return redirect(url_for('main.showRestaurants'))
    
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Sorry, you cannot delete the admin user.', 'error')
        return redirect(url_for('main.admin'))
    
    # Update owner IDs of associated restaurants to the admin account
    restaurants = Restaurant.query.filter_by(ownerid=user.id).all()
    admin_user = User.query.filter_by(username='admin').first()

    for restaurant in restaurants:
        restaurant.ownerid = admin_user.id

    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted successfully.', 'success')
    return redirect(url_for('main.admin'))

@main.route('/admin/editrestaurant/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def edit_restaurant_owner(restaurant_id):
    if current_user.role != 'admin':
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
                db.session.commit()
                flash('Restaurant owner has been updated successfully.', 'success')

        return redirect(url_for('main.admin'))

    return render_template('editrestaurantowner.html', form=form, restaurant=restaurant)

#easier to make new function
@main.route('/admin/delete-restaurant/<int:restaurant_id>', methods=['POST'])
@login_required
def delete_restaurant(restaurant_id):
    if current_user.role != 'admin':
        flash('Sorry, %s. You do not have permission to delete restaurants.' % current_user.username, 'error')
        return redirect(url_for('main.admin'))

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    db.session.delete(restaurant)
    db.session.commit()
    flash('Restaurant %s has been deleted successfully.' % restaurant.name, 'success')
    return redirect(url_for('main.admin'))







#Create search bar
@main.route('/search', methods=["POST"])
def search():
   form = SearchForm()
   items = MenuItem.query
   if form.validate_on_submit(): 
      #Recieve input from submitted search
      text_searched = sanitise_input(form.searched.data)
      #Query the Database
      items = items.filter(MenuItem.name.like('%' + text_searched + '%'))
      #items = items.order_by(MenuItem).all()
        
      return render_template("searchbar.html",
        form = form,
        searched = text_searched,
        items = items)
