from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from flask_bcrypt import Bcrypt
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember_password') else False

        user = User.query.filter_by(email=email).first()
        if user : 
            if bcrypt.check_password_hash(user.password, password) : 
                flash('Logged in successfully!', category='success')
                login_user(user, remember=remember) 
                return redirect(url_for("views.home"))
            else :
                flash('Incorrect password, try again.', category='error')
        else :
            flash('Email does not exist.', category='error')

    return render_template("auth/login.html")

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmed_password = request.form.get('confirmed_password')
        
        user = User.query.filter_by(email=email).first()
        if user : 
            flash('Email already exists.', category='error')
        elif len(email) < 4 :
            flash('Email must be greater than 4 characters', category='error')
        elif len(name) < 2 :
            flash('Name must be greater than 1 character', category='error')
        elif password != confirmed_password :
            flash('Passwords don\'t match', category='error')
        elif len(password) < 7 :
            flash('Password must be at least 7 characters', category='error')
        else : 
            new_user = User(
                email = email, 
                name = name, 
                password = bcrypt.generate_password_hash(password).decode('utf-8')
            )
            
            # create new user
            db.session.add(new_user)
            db.session.commit() # di save

            flash('Account created!', category='success')   
            login_user(user, remember=True) 

            return redirect(url_for("views.home"))

    return render_template("auth/register.html")

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))