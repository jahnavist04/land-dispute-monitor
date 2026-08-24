"""Alerts web routes — inbox and mark-as-read."""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.alert import Alert
from app.web import web_bp


@web_bp.route('/alerts')
@login_required
def alerts_list():
    """Alert inbox for the current user."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Alert.query.filter_by(client_id=current_user.id)

    # Filter by read status
    read_filter = request.args.get('read', '')
    if read_filter == 'unread':
        query = query.filter_by(is_read=False)
    elif read_filter == 'read':
        query = query.filter_by(is_read=True)

    pagination = query.order_by(Alert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('alerts/list.html',
                           alerts=pagination.items,
                           pagination=pagination,
                           read_filter=read_filter)


@web_bp.route('/alerts/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    """Mark a single alert as read."""
    alert = Alert.query.get_or_404(alert_id)
    if alert.client_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('web.alerts_list'))

    alert.is_read = True
    db.session.commit()

    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Alert marked as read.', 'info')
    return redirect(url_for('web.alerts_list'))


@web_bp.route('/alerts/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all alerts as read for current user."""
    Alert.query.filter_by(
        client_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()

    flash('All alerts marked as read.', 'info')
    return redirect(url_for('web.alerts_list'))
