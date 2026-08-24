"""Dashboard overview routes."""
from flask import render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.dispute import Dispute
from app.models.alert import Alert
from app.models.source import Source
from app.models.extracted_notice import ExtractedNotice
from app.models.raw_article import RawArticle
from app.web import web_bp


@web_bp.route('/')
@login_required
def dashboard_home():
    """Main dashboard with KPI cards and charts."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # KPI stats
    total_disputes = Dispute.query.count()
    active_disputes = Dispute.query.filter_by(status='active').count()
    critical_disputes = Dispute.query.filter_by(severity='critical', status='active').count()
    total_sources = Source.query.filter_by(is_active=True).count()
    pending_ocr = RawArticle.query.filter_by(scrape_status='pending').count()

    unread_alerts = Alert.query.filter_by(
        client_id=current_user.id, is_read=False
    ).count()

    # Recent disputes
    recent_disputes = Dispute.query.order_by(
        desc(Dispute.created_at)
    ).limit(10).all()

    # Recent alerts for current user
    recent_alerts = Alert.query.filter_by(
        client_id=current_user.id
    ).order_by(desc(Alert.created_at)).limit(5).all()

    return render_template('dashboard/index.html',
                           total_disputes=total_disputes,
                           active_disputes=active_disputes,
                           critical_disputes=critical_disputes,
                           total_sources=total_sources,
                           pending_ocr=pending_ocr,
                           unread_alerts=unread_alerts,
                           recent_disputes=recent_disputes,
                           recent_alerts=recent_alerts)


@web_bp.route('/api/dashboard/chart-data')
@login_required
def chart_data():
    """Return chart data as JSON for AJAX chart rendering."""
    now = datetime.now(timezone.utc)

    # Severity distribution
    severity_counts = db.session.query(
        Dispute.severity, func.count(Dispute.id)
    ).group_by(Dispute.severity).all()
    severity_data = {s: c for s, c in severity_counts}

    # Disputes over last 30 days (by day)
    thirty_days_ago = now - timedelta(days=30)
    daily_counts = db.session.query(
        func.date(Dispute.created_at), func.count(Dispute.id)
    ).filter(
        Dispute.created_at >= thirty_days_ago
    ).group_by(func.date(Dispute.created_at)).all()

    timeline_labels = []
    timeline_values = []
    for date_val, count in sorted(daily_counts, key=lambda x: str(x[0])):
        timeline_labels.append(str(date_val))
        timeline_values.append(count)

    # Top locations
    location_counts = db.session.query(
        Dispute.location, func.count(Dispute.id)
    ).filter(
        Dispute.location.isnot(None),
        Dispute.location != ''
    ).group_by(Dispute.location).order_by(
        func.count(Dispute.id).desc()
    ).limit(10).all()

    location_labels = [loc for loc, _ in location_counts]
    location_values = [cnt for _, cnt in location_counts]

    # Status distribution
    status_counts = db.session.query(
        Dispute.status, func.count(Dispute.id)
    ).group_by(Dispute.status).all()
    status_data = {s: c for s, c in status_counts}

    return jsonify({
        'severity': {
            'labels': list(severity_data.keys()),
            'values': list(severity_data.values())
        },
        'timeline': {
            'labels': timeline_labels,
            'values': timeline_values
        },
        'locations': {
            'labels': location_labels,
            'values': location_values
        },
        'status': {
            'labels': list(status_data.keys()),
            'values': list(status_data.values())
        }
    })
