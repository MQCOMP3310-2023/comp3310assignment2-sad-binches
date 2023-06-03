from flask import Blueprint, jsonify
from .models import Restaurant, MenuItem
from sqlalchemy import text
from . import db
import json as pyjs
import logging

json = Blueprint('json', __name__)

# JSON APIs to view Restaurant Information
# Used named parameter to prevent sqli (Parameterised query)
@json.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    # Updated SQL query using named parameter
    query = "SELECT * FROM menu_item WHERE restaurant_id = :restaurant_id"
    
    # Executing the query with named parameter
    result = db.session.execute(text(query), {'restaurant_id': restaurant_id})
    
    # Converting rows to dictionaries
    items_list = [dict(row) for row in result]
    
    # Returning JSON response using Flask's jsonify function
    return jsonify(items_list)

# Used named parameter to prevent sqli (Parameterised query)
@json.route('/restaurant/<restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    # Updated SQL query using named parameter
    query = "SELECT * FROM menu_item WHERE id = :menu_id LIMIT 1"
    
    # Executing the query with named parameter
    result = db.session.execute(text(query), {'menu_id': menu_id})
    
    # Converting rows to dictionaries
    items_list = [dict(row) for row in result]
    
    # Returning JSON response using Flask's jsonify function
    return jsonify(items_list)

# Used Endpoint to retrieve all restaurant data as JSON (No user input used)
@json.route('/restaurant/JSON')
def restaurantsJSON():
    # Retrieve all restaurant objects from the database
    restaurants = Restaurant.query.all()

    # Convert each restaurant object to a dictionary representation
    rest_list = [restaurant.to_dict() for restaurant in restaurants]

    # Return the list of dictionaries as a JSON response
    return jsonify(rest_list)


