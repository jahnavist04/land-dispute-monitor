"""Compatibility routes for the public web dashboard."""
from flask import redirect, url_for
from flask_login import logout_user
from app.web import web_bp


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Keep old login links working without showing a login screen."""
    return redirect(url_for('web.dashboard_home'))


@web_bp.route('/logout')
def logout():
    """Return to the public dashboard."""
    logout_user()
    return redirect(url_for('web.dashboard_home'))
