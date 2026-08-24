"""Sources management web routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.source import Source
from app.web import web_bp


@web_bp.route('/sources')
@login_required
def sources_list():
    """List all newspaper sources."""
    sources = Source.query.order_by(Source.created_at.desc()).all()
    return render_template('sources/list.html', sources=sources)


@web_bp.route('/sources/add', methods=['POST'])
@login_required
def add_source():
    """Add a new newspaper source."""
    name = request.form.get('name', '').strip()
    base_url = request.form.get('base_url', '').strip()
    source_type = request.form.get('source_type', 'html')
    frequency = request.form.get('scrape_frequency_minutes', 60, type=int)
    article_selector = request.form.get('article_selector', '').strip()

    if not name or not base_url:
        flash('Name and URL are required.', 'danger')
        return redirect(url_for('web.sources_list'))

    # Check for duplicate URL
    existing = Source.query.filter_by(base_url=base_url).first()
    if existing:
        flash('A source with this URL already exists.', 'warning')
        return redirect(url_for('web.sources_list'))

    selectors_config = {}
    if article_selector:
        selectors_config['article_selector'] = article_selector

    source = Source(
        name=name,
        base_url=base_url,
        source_type=source_type,
        scrape_frequency_minutes=frequency,
        selectors_config=selectors_config,
        is_active=True
    )
    db.session.add(source)
    db.session.commit()

    flash(f'Source "{name}" added successfully.', 'success')
    return redirect(url_for('web.sources_list'))


@web_bp.route('/sources/<int:source_id>/toggle', methods=['POST'])
@login_required
def toggle_source(source_id):
    """Toggle source active/inactive."""
    source = Source.query.get_or_404(source_id)
    source.is_active = not source.is_active
    db.session.commit()

    status = 'activated' if source.is_active else 'deactivated'
    flash(f'Source "{source.name}" {status}.', 'info')
    return redirect(url_for('web.sources_list'))


@web_bp.route('/sources/<int:source_id>/delete', methods=['POST'])
@login_required
def delete_source(source_id):
    """Soft-delete a source."""
    source = Source.query.get_or_404(source_id)
    source.is_active = False
    db.session.commit()

    flash(f'Source "{source.name}" deactivated.', 'warning')
    return redirect(url_for('web.sources_list'))
