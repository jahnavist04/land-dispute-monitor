"""Subscriptions management web routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.subscription import Subscription
from app.web import web_bp


@web_bp.route('/subscriptions')
@login_required
def subscriptions_list():
    """List current user's subscriptions."""
    subs = Subscription.query.filter_by(client_id=current_user.id).order_by(
        Subscription.created_at.desc()
    ).all()
    return render_template('subscriptions/list.html', subscriptions=subs)


@web_bp.route('/subscriptions/add', methods=['POST'])
@login_required
def add_subscription():
    """Create a new subscription."""
    regions_raw = request.form.get('tracked_regions', '').strip()
    properties_raw = request.form.get('tracked_properties', '').strip()
    min_severity = request.form.get('min_severity', 'medium')
    notification_method = request.form.get('notification_method', 'email')
    webhook_url = request.form.get('webhook_url', '').strip()

    tracked_regions = [r.strip() for r in regions_raw.split(',') if r.strip()] if regions_raw else []
    tracked_properties = [p.strip() for p in properties_raw.split(',') if p.strip()] if properties_raw else []

    if not tracked_regions and not tracked_properties:
        flash('Please specify at least one region or property to track.', 'danger')
        return redirect(url_for('web.subscriptions_list'))

    sub = Subscription(
        client_id=current_user.id,
        tracked_regions=tracked_regions,
        tracked_properties=tracked_properties,
        min_severity=min_severity,
        notification_method=notification_method,
        webhook_url=webhook_url if webhook_url else None,
        is_active=True
    )
    db.session.add(sub)
    db.session.commit()

    flash('Subscription created successfully.', 'success')
    return redirect(url_for('web.subscriptions_list'))


@web_bp.route('/subscriptions/<int:sub_id>/toggle', methods=['POST'])
@login_required
def toggle_subscription(sub_id):
    """Toggle subscription active/inactive."""
    sub = Subscription.query.get_or_404(sub_id)
    if sub.client_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('web.subscriptions_list'))

    sub.is_active = not sub.is_active
    db.session.commit()

    status = 'activated' if sub.is_active else 'paused'
    flash(f'Subscription {status}.', 'info')
    return redirect(url_for('web.subscriptions_list'))


@web_bp.route('/subscriptions/<int:sub_id>/delete', methods=['POST'])
@login_required
def delete_subscription(sub_id):
    """Deactivate a subscription."""
    sub = Subscription.query.get_or_404(sub_id)
    if sub.client_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('web.subscriptions_list'))

    sub.is_active = False
    db.session.commit()

    flash('Subscription deactivated.', 'warning')
    return redirect(url_for('web.subscriptions_list'))
