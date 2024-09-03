from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField


class EmptyForm(FlaskForm):
    submit = SubmitField('Подтвердить')


from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed, FileRequired


class PostForm(FlaskForm):
    """Post form class"""
    title = TextAreaField('Место', validators=[
        DataRequired(), Length(min=1, max=100)])
    post = TextAreaField('Расскажите о поездке', validators=[
        DataRequired(), Length(min=1, max=300)])
    price = TextAreaField('Цена', validators=[
        DataRequired(), Length(min=1, max=20)])
    places = TextAreaField('Места для посещения', validators=[
        DataRequired(), Length(min=1, max=300)])

    main_photo = FileField("Основное Фото", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])

    additional_photos = MultipleFileField("Дополнительные Фото", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])

    main_video = FileField("Основное Видео", validators=[
        FileAllowed(['mp4', 'avi', 'mov'], 'Только видеофайлы!')])

    additional_videos = MultipleFileField("Дополнительные Видео", validators=[
        FileAllowed(['mp4', 'avi', 'mov'], 'Только видеофайлы!')])

    submit = SubmitField('Опубликовать')
