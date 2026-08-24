"""Disputes web routes — list, detail, and filtering."""
from flask import render_template, request
from flask_login import login_required
from datetime import datetime
from app.models.dispute import Dispute
from app.models.extracted_notice import ExtractedNotice
from app.web import web_bp


@web_bp.route('/disputes')
@login_required
def disputes_list():
    """Paginated dispute list with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Dispute.query

    # Filters
    severity = request.args.get('severity', '')
    if severity:
        query = query.filter(Dispute.severity == severity)

    status = request.args.get('status', '')
    if status:
        query = query.filter(Dispute.status == status)

    location = request.args.get('location', '')
    if location:
        query = query.filter(Dispute.location.ilike(f'%{location}%'))

    dispute_type = request.args.get('type', '')
    if dispute_type:
        query = query.filter(Dispute.dispute_type == dispute_type)

    date_from = request.args.get('date_from', '')
    if date_from:
        try:
            query = query.filter(Dispute.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass

    date_to = request.args.get('date_to', '')
    if date_to:
        try:
            query = query.filter(Dispute.created_at <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    pagination = query.order_by(Dispute.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('disputes/list.html',
                           disputes=pagination.items,
                           pagination=pagination,
                           filters={
                               'severity': severity,
                               'status': status,
                               'location': location,
                               'type': dispute_type,
                               'date_from': date_from,
                               'date_to': date_to
                           })


@web_bp.route('/disputes/<int:dispute_id>')
@login_required
def dispute_detail(dispute_id):
    """Single dispute detail view with related notice and OCR text."""
    dispute = Dispute.query.get_or_404(dispute_id)

    # Get the associated extracted notice
    notice = ExtractedNotice.query.get(dispute.extracted_notice_id) if dispute.extracted_notice_id else None

    # Get cluster mates if cluster_id exists
    cluster_disputes = []
    if dispute.cluster_id:
        cluster_disputes = Dispute.query.filter(
            Dispute.cluster_id == dispute.cluster_id,
            Dispute.id != dispute.id
        ).limit(10).all()

    return render_template('disputes/detail.html',
                           dispute=dispute,
                           notice=notice,
                           cluster_disputes=cluster_disputes)
