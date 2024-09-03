from datetime import datetime
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User, Post
from flask import render_template, current_app, send_from_directory, flash, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from app.main import bp
from app.main.forms import PostForm, EmptyForm


@bp.before_request
def before_request():
    """The function of updating the last visit"""
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}


def allowed_file(filename):
    """File extension check function"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    def save_file(file):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return filename
        return None

    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            head=form.title.data,
            body=form.post.data,
            price=form.price.data,
            places=form.places.data,
            author=current_user
        )

        # Save main photo
        if form.main_photo.data:
            post.main_photo_url = save_file(form.main_photo.data)

        # Save additional photos
        if form.additional_photos.data:
            photos = [save_file(photo) for photo in form.additional_photos.data]
            post.additional_photo_urls = ','.join(filter(None, photos))

        # Save main video
        if form.main_video.data:
            post.main_video_url = save_file(form.main_video.data)

        # Save additional videos
        if form.additional_videos.data:
            videos = [save_file(video) for video in form.additional_videos.data]
            post.additional_video_urls = ','.join(filter(None, videos))

        db.session.add(post)
        db.session.commit()
        flash('Опубликовано')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url,
                           folder=current_app.config["UPLOAD_FOLDER"])


@bp.route('/uploads/<name>')
def uploads(name):
    return send_from_directory(os.path.join(current_app.config["UPLOAD_FOLDER"]), name)


@bp.route('/explore')
@login_required
def explore():
    """The function of the page of all posts"""
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('explore.html', title='Лента', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """
    Subscription function
    :param username: str
    :return: redirect
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Это вы')
            return redirect(url_for('profiles.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'Подписались на {username}')
        return redirect(url_for('profile.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    """
    Unsubscribe function
    :param username: str
    :return: redirect
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'Пользователь {username} не найден.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Это вы')
            return redirect(url_for('profile.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'Отписались от {username}.')
        return redirect(url_for('profile.user', username=username))
    else:
        return redirect(url_for('main.index'))
