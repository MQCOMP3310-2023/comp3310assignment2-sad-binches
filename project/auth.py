from flask import Blueprint, app, render_template, request, flash, redirect, url_for, session, abort
from .models import Restaurant, MenuItem, User
from sqlalchemy import asc
from . import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
import re
from markupsafe import escape
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__)




@auth.route('/register')
def register_standard():
    return render_template('register.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate the form data
        if password != confirm_password:
            flash('Passwords do not match. Please try again.')
            return redirect(url_for('auth.register'))

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, role='Public User')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now log in.')
        return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('auth.register'))
    


@auth.route('/login' , methods=['GET', 'POST'])
def login():
    form = User.LoginForm()  # Create an instance of the LoginForm
    logout_user()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))

        # Store user ID in the session to maintain the session
        login_user(user,True)

        flash('Logged in successfully.')
        return redirect(url_for('main.showRestaurants'))
    else:
        return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.showRestaurants'))