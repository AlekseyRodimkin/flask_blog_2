from flask import render_template
from app import db
from app.errors import bp


@bp.app_errorhandler(404)
def not_found_error(error):
    """
    Handler for the missing page error
    :param error: code
    :return: render page
    """
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    """
    Server-side error handler
    :param error: code
    :return: render page
    """
    db.session.rollback()
    return render_template('errors/500.html'), 500
