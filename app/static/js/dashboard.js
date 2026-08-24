// Dashboard interactive scripts

document.addEventListener('DOMContentLoaded', function() {
    const dashboard = document.querySelector('[data-dashboard-controls]');

    function animateCounters() {
        document.querySelectorAll('[data-count-value]').forEach(counter => {
            const target = Number(counter.dataset.countValue || 0);
            const duration = 650;
            const started = performance.now();
            const tick = now => {
                const progress = Math.min((now - started) / duration, 1);
                counter.textContent = Math.round(target * (1 - Math.pow(1 - progress, 3)));
                if (progress < 1) requestAnimationFrame(tick);
            };
            requestAnimationFrame(tick);
        });
    }

    function filterRecentCases() {
        if (!dashboard) return;
        const term = (dashboard.querySelector('#caseSearch')?.value || '').toLowerCase().trim();
        const severity = dashboard.querySelector('[data-severity-filter].active')?.dataset.severityFilter || 'all';
        const rows = document.querySelectorAll('.recent-case-row');
        let visible = 0;
        rows.forEach(row => {
            const matchesText = !term || row.dataset.caseSearch.toLowerCase().includes(term);
            const matchesSeverity = severity === 'all' || row.dataset.severity === severity;
            row.hidden = !(matchesText && matchesSeverity);
            if (!row.hidden) visible += 1;
        });
        const empty = document.querySelector('.recent-case-empty');
        if (empty) empty.hidden = visible !== 0;
    }

    animateCounters();
    if (dashboard) {
        dashboard.querySelector('#caseSearch')?.addEventListener('input', filterRecentCases);
        dashboard.querySelectorAll('[data-severity-filter]').forEach(button => {
            button.addEventListener('click', () => {
                dashboard.querySelectorAll('[data-severity-filter]').forEach(item => item.classList.remove('active'));
                button.classList.add('active');
                filterRecentCases();
            });
        });
        dashboard.querySelector('[data-refresh-dashboard]')?.addEventListener('click', event => {
            const button = event.currentTarget;
            button.disabled = true;
            button.classList.add('is-refreshing');
            window.dispatchEvent(new CustomEvent('dashboard:refresh'));
            setTimeout(() => {
                button.disabled = false;
                button.classList.remove('is-refreshing');
            }, 700);
        });
    }

    // Handle AJAX for individual mark-read buttons in Alerts page
    const markReadForms = document.querySelectorAll('.alert-row form');
    markReadForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const actionUrl = this.getAttribute('action');
            const alertRow = this.closest('.alert-row');

            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alertRow.classList.remove('unread');
                    const dot = alertRow.querySelector('.unread-dot');
                    if (dot) {
                        dot.outerHTML = '<i class="bi bi-envelope-open text-muted"></i>';
                    }
                    this.remove();
                    
                    // Update badge count in navbars if present
                    const badges = document.querySelectorAll('.badge.bg-danger');
                    badges.forEach(b => {
                        let count = parseInt(b.innerText);
                        if (!isNaN(count) && count > 0) {
                            count -= 1;
                            if (count === 0) {
                                b.remove();
                            } else {
                                b.innerText = count;
                            }
                        }
                    });
                }
            })
            .catch(err => {
                console.error('Failed to mark alert as read:', err);
                // Fallback to normal form submit
                form.submit();
            });
        });
    });
});
