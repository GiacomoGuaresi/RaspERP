from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = 'remember' in request.form

        user = User.get_by_email(email)
        print(user.password)
        if user and (user.password is None): #TODO: implementare il controllo della password
            login_user(user, remember=remember)
            session.permanent = remember
            return redirect(url_for('home.index'))
        else:
            flash("Credenziali non valide", "danger")

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
