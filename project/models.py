from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_login import UserMixin


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)

    # Form fields
    class RestaurantForm(FlaskForm):
        name = StringField('Name', validators=[DataRequired()])
        submit = SubmitField('Create')

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'name'         : self.name,
            'id'           : self.id,
        }
    
class MenuItem(db.Model):
    name = db.Column(db.String(80), nullable = False)
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.String(250))
    price = db.Column(db.String(8))
    course = db.Column(db.String(250))
    restaurant_id = db.Column(db.Integer,db.ForeignKey('restaurant.id'))
    restaurant = db.    relationship(Restaurant)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name'       : self.name,
            'description' : self.description,
            'id'         : self.id,
            'price'      : self.price,
            'course'     : self.course,
        }

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = StringField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')

    class RegistrationForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = StringField('Password', validators=[DataRequired()])
        confirm_password = StringField('Confirm Password', validators=[DataRequired()])
        submit = SubmitField('Register')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    



