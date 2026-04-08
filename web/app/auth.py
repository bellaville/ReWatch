from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import User, Role
from app.db import db

"""
Authentication blueprint routes for logging users in, registering new accounts,
and logging out.
"""

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login')
def login():
    """
    Render the login page where users can enter their email and password.
    """
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    """
    Authenticate a submitted email/password pair and optionally remember
    the session. If credentials are invalid, flash an error message and
    redirect back to the login form. On success, log the user in and
    redirect to the main index page.
    """
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/signup')
def signup():
    """
    Render the signup page where new users can register for an account.
    """
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    """
    Create a new user account with the submitted name, email, password,
    and selected role. If the email already exists or the role selection
    is invalid, flash an error/redirect back to the signup form. On
    success, persist the user and redirect to the login page.
    """
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    new_user = User(email=email, name=name, password=generate_password_hash(password))

    role = Role.query.filter_by(id=int(request.form['options'])).first()
    if role:
        new_user.roles.append(role)
    else:
        msg = "Invalid role selection"
        return redirect(url_for('auth.signup'), msg=msg)

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    """
    Log out the currently authenticated user and redirect to the main
    index page. Requires the user to be logged in.
    """
    logout_user()
    return redirect(url_for('main.index'))