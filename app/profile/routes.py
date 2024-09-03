from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.models import User, Post
from flask import render_template, current_app, flash, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from app.profile import bp
from app.main.forms import PostForm, EmptyForm
from app.profile.forms import EditProfileForm


@bp.route('/user/<username>')
@login_required
def user(username):
    """
    Profile function
    :param username: str
    :return: render profile and data
    """
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('profile/user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Profile change function
    :return: redirect again or render edit page
    """
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Сохранено')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='О себе',
                           form=form)


def delete_file(file_name):
    """
    File Delete Function
    Args:
        file_name: string
    Returns:
    """
    if file_name:
        path_to_file = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
        if os.path.exists(path_to_file):
            os.remove(path_to_file)


@bp.route('/delete_post/<username>/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id, username):
    """
    Post Delete Function
    Args:
        post_id: integer
        username: string
    Returns: render or redirect
    """
    post = Post.query.get(post_id)
    if not post:
        flash('Ошибка удаления поста')
        return redirect(url_for('profile.user', username=current_user.username))

    delete_file(post.main_photo_url)

    if post.additional_photo_urls:
        for url in post.additional_photo_urls.split(','):
            delete_file(url.strip())

    delete_file(post.main_video_url)

    if post.additional_video_urls:
        for url in post.additional_video_urls.split(','):
            delete_file(url.strip())

    db.session.delete(post)
    db.session.commit()
    flash('Пост удален')
    return redirect(url_for('profile.user', username=current_user.username))


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}


def allowed_file(filename):
    """File extension check function"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/change_post/<username>/<post_id>', methods=['GET', 'POST'])
@login_required
def change_post(username, post_id):
    """
    Post changing function
    :param username: str
    :param post_id: str
    :return: redirect
    """

    def save_file(file):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return filename
        return None

    form = PostForm()
    if form.validate_on_submit():
        post = Post.query.get(post_id)

        if not post:
            flash('Ошибка изменения поста')
            return redirect(url_for('main.user', username=username))

        post.head = form.title.data
        post.body = form.post.data
        post.price = form.price.data
        post.places = form.places.data

        # Updating main photo
        delete_file(post.main_photo_url)
        post.main_photo_url = None
        if form.main_photo.data:
            delete_file(post.main_photo_url)
            post.main_photo_url = save_file(form.main_photo.data)

        # Updating additional photos
        for url in post.additional_photo_urls.split(','):
            delete_file(url.strip())
        post.additional_photo_urls = None
        if form.additional_photos.data:
            delete_file(post.additional_photo_urls)
            photos = [save_file(photo) for photo in form.additional_photos.data]
            post.additional_photo_urls = ','.join(filter(None, photos))

        # Updating main video
        delete_file(post.main_video_url)
        post.main_video_url = None
        if form.main_video.data:
            delete_file(post.main_video_url)
            post.main_video_url = save_file(form.main_video.data)

        # Updating additional videos
        for url in post.additional_video_urls.split(','):
            delete_file(url.strip())
        post.additional_video_urls = None
        if form.additional_videos.data:
            delete_file(post.additional_video_urls)
            videos = [save_file(video) for video in form.additional_videos.data]
            post.additional_video_urls = ','.join(filter(None, videos))

        db.session.commit()
        flash('Пост изменен')
        return redirect(url_for('profile.user', username=username))
    return render_template('profile/change_post.html', title='Изменить пост', form=form)
