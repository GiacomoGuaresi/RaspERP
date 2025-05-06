from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from hashlib import sha256

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = 'remember' in request.form

        user = User.get_by_email(email)
        print(user.password)
        print(sha256(password.encode('utf-8')).hexdigest())

        if user and (user.password == sha256(password.encode('utf-8')).hexdigest()):
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


@auth_bp.route("/user", methods=["GET", "POST"])
@login_required
def user():
    user = User.load_user(g.selected_user)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        new_username = request.form.get("username")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")

        if not (user.password == sha256(current_password.encode('utf-8')).hexdigest()):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.user"))

        if new_username:
            user.username = new_username

        if new_password:
            user.password = sha256(new_password.encode('utf-8')).hexdigest()

        user.update()
        flash("User updated successfully.", "success")
        return redirect(url_for("auth.user"))

    return render_template("user.html", user=user)
