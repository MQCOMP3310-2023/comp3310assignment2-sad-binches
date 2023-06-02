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
      newRestaurant = Restaurant(name = request.form['name'])   
      db.session.add(newRestaurant)
      flash('New Restaurant %s Successfully Created' % newRestaurant.name)
      db.session.commit()
      return redirect(url_for('main.showRestaurants'))
  else:
      return render_template('newRestaurant.html')


# Security for input sanitisation + error caused by changes  that i couldn't fix without the db.commit
@main.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    editedRestaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
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


@main.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurantToDelete = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if 'delete' in request.form:
            db.session.delete(restaurantToDelete)
            flash('%s Successfully Deleted' % restaurantToDelete.name)
            db.session.commit()
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template('deleteRestaurant.html', restaurant=restaurantToDelete)


#Show a restaurant menu
@main.route('/restaurant/<int:restaurant_id>/')
@main.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = db.session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return render_template('menu.html', items = items, restaurant = restaurant)
     


#Create a new menu item
@main.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
def newMenuItem(restaurant_id):
  restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      #implemented input sanitsation again
      newItem = MenuItem(name = escape(request.form['name']), description = sanitise_input(request.form['description']), price = "$"+escape(request.form['price']), course = escape(request.form['course']), restaurant_id = restaurant_id)
      db.session.add(newItem)
      db.session.commit()
      flash('New Menu %s Item Successfully Created' % (newItem.name))
      return redirect(url_for('main.showMenu', restaurant_id = restaurant_id))
  else:
      return render_template('newmenuitem.html', restaurant_id = restaurant_id)

#Edit a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):

    editedItem = db.session.query(MenuItem).filter_by(id = menu_id).one()
    restaurant = db.session.query(Restaurant).filter_by(id = restaurant_id).one()
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


#Delete a menu item
@main.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDelete = db.session.query(MenuItem).filter_by(id=menu_id).one()
    
    if request.method == 'POST':
        if 'delete' in request.form:
            db.session.delete(itemToDelete)
            db.session.commit()
            flash('Menu Item Successfully Deleted')
        return redirect(url_for('main.showMenu', restaurant_id=restaurant_id))
    
    return render_template('deleteMenuItem.html', item=itemToDelete, restaurant=restaurant)





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
