import os
from app.models import User, Post
from flask import render_template, request, session
from app.admin import bp
from flask import flash, redirect, url_for
from sqlalchemy import select, update
from app import db
from app.admin.algorithms import get_top_words
from app.models import followers

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

classes = {
    'post': Post,
    'user': User
}


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login function"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.index'))
        else:
            flash('Неверный пароль!', 'danger')
    return render_template('admin/login.html')


@bp.route('/logout')
def logout():
    """Logout function"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


@bp.route('/')
def index():
    """The function of the main page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    total_users = User.query.count()
    total_posts = Post.query.count()
    top_words = get_top_words()

    return render_template('admin/index.html', total_users=total_users, total_posts=total_posts, top_words=top_words)


@bp.route('/users')
def users():
    """User Page function"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    sort_by = request.args.get('sort', 'id')  # Получение параметра сортировки из URL
    if sort_by not in ['id', 'username', 'email', 'telegram', 'password_hash', 'last_seen']:
        sort_by = 'id'
    users_list = User.query.order_by(getattr(User, sort_by)).all()  # Сортировка по выбранному полю
    return render_template('admin/users.html', users=users_list)


@bp.route('/delete/<string:object>/<int:id_object>')
def delete(object, id_object):
    """User deletion function"""
    if not session.get('admin_logged_in'):
        flash("Вы не авторизованы для выполнения этого действия", "error")
        return redirect(url_for('admin.login'))

    model_class = classes.get(object)
    if model_class is None:
        flash("Функция удаления для этого объекта еще не реализована", "error")
        return redirect(url_for('admin.index'))

    if object == 'user':
        try:
            user = db.session.execute(
                select(User).where(User.id == id_object)
            ).scalar_one_or_none()

            if user is None:
                flash("Пользователь не найден", "error")
                return redirect(url_for('admin.index'))

            # Delete all user posts
            db.session.query(Post).filter(Post.user_id == id_object).delete(synchronize_session=False)

            # update the number of subscribers
            followed_users = db.session.execute(
                select(followers.c.follower_id).where(followers.c.followed_id == id_object)
            ).scalars().all()

            for follower_id in followed_users:
                db.session.execute(
                    update(User)
                    .where(User.id == follower_id)
                    .values(followers_count=User.query.get(follower_id).followers_count() - 1)
                )

            # del user
            db.session.delete(user)
            db.session.commit()
            flash("Пользователь и его посты успешно удалены", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Произошла ошибка при удалении пользователя: {e}", "error")

    else:
        try:
            obj = db.session.execute(
                select(model_class).where(model_class.id == id_object)
            ).scalar_one_or_none()

            if obj is None:
                flash("Объект не найден", "error")
            else:
                db.session.delete(obj)
                db.session.commit()
                flash("Запись успешно удалена", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Произошла ошибка при удалении записи: {e}", "error")

    return redirect(url_for(f'admin.{object}s'))
