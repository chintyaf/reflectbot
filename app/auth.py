from flask import Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    return render_template("auth/login.html")

@auth.route("/register", methods=['GET', 'POST'])
def register():
    print("register")
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmed_password = request.form.get('confirmed_password')
        
        if len(email) < 4 :
            flash('Email must be greater than 4 characters', category='error')
        elif len(name) < 2 :
            flash('Name must be greater than 1 character', category='error')
        elif password != confirmed_password :
            flash('Passwords don\'t match', category='error')
        elif len(password) < 7 :
            flash('Password must be at least 7 characters', category='error')
        else : 
            flash('Account created!', category='success')   

    return render_template("auth/register.html")

@auth.route('/logout')
def logout():
    return "<p>logout</p>"