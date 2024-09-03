from app.auth.forms import LoginForm, RegistrationForm
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
import sqlalchemy as sa
from app import db
from app.models import User
from app.auth import bp


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Account register function
    :return: register or login pages
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        telegram_data = form.telegram.data.strip() or None
        user = User(username=form.username.data, email=form.email.data, telegram=telegram_data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Регистрация', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Account login function
    :return: index or login pages
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if not user:
            flash('Пройдите регистрацию')
            return redirect(url_for('auth.login'))
        if not user.check_password(form.password.data):
            flash('Не верное имя или пароль')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Вход', form=form)


@bp.route('/logout')
def logout():
    """
    Account logout function
    :return: index page
    """
    logout_user()
    return redirect(url_for('main.index'))
