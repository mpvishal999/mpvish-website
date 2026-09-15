"""Main public routes for MPVISH Website."""
import os
import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, \
    abort, send_from_directory, current_app, flash
from sqlalchemy import or_, desc
from extensions import db
from models import (Note, Paper, Update, Result, PremiumPlan, PremiumPurchase, HeroImage, \
                    Notification, Page, Yojna, SearchLog, DownloadHistory, User)
from utils import paginate, slugify, ensure_unique_slug, get_file_path, hash_ip
from flask_login import current_user, login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    latest_updates = Update.query.filter_by(is_published=True, is_deleted=False).order_by(
        desc(Update.is_pinned), desc(Update.created_at)
    ).limit(5).all()
    latest_notes = Note.query.filter_by(is_published=True, is_deleted=False).order_by(
        desc(Note.created_at)
    ).limit(6).all()
    latest_papers = Paper.query.filter_by(is_published=True, is_deleted=False).order_by(
        desc(Paper.created_at)
    ).limit(6).all()
    trending = Note.query.filter_by(is_published=True, is_deleted=False).order_by(
        desc(Note.downloads)
    ).limit(5).all()
    hero_images = HeroImage.query.filter_by(is_active=True).order_by(
        HeroImage.display_order, HeroImage.id
    ).all()

    featured_yojnas = Yojna.query.filter_by(is_published=True, is_deleted=False).order_by(
        desc(Yojna.is_featured), Yojna.display_order
    ).limit(4).all()

    return render_template('index.html',
                           hero_images=hero_images,
                           latest_updates=latest_updates,
                           latest_notes=latest_notes,
                           latest_papers=latest_papers,
                           trending=trending,
                           featured_yojnas=featured_yojnas,
                           meta_title='MPVISH - MP Board Notes, Old Papers, Results, Jobs 2026',
                           meta_description='MPVISH - MP Ki Padhai, Ek Jagah. Download MP Board 10th & 12th notes, old papers, check results and sarkari job updates for Madhya Pradesh.')


# ============ NOTES ============

@main_bp.route('/notes')
def notes():
    page = request.args.get('page', 1, type=int)
    class_filter = request.args.get('class', '')
    stream_filter = request.args.get('stream', '')
    subject_filter = request.args.get('subject', '')
    search_q = request.args.get('q', '').strip()

    query = Note.query.filter_by(is_published=True, is_deleted=False)
    if class_filter:
        query = query.filter(Note.class_level == class_filter)
    if stream_filter:
        query = query.filter(Note.stream == stream_filter)
    if subject_filter:
        query = query.filter(Note.subject.ilike(f'%{subject_filter}%'))
    if search_q:
        query = query.filter(or_(
            Note.title.ilike(f'%{search_q}%'),
            Note.subject.ilike(f'%{search_q}%'),
            Note.chapter.ilike(f'%{search_q}%'),
        ))
    query = query.order_by(desc(Note.is_featured), desc(Note.created_at))

    items, pagination = paginate(query, page, 12)

    subjects = db.session.query(Note.subject).filter_by(is_published=True, is_deleted=False).distinct().all()
    subjects = sorted([s[0] for s in subjects])

    return render_template('notes.html',
                           notes=items, pagination=pagination, subjects=subjects,
                           current_class=class_filter, current_stream=stream_filter,
                           current_subject=subject_filter, search_q=search_q,
                           meta_title='MP Board Notes - Class 10th & 12th PDF Download - MPVISH',
                           meta_description='Download MP Board Class 10th and 12th notes PDF for free. All subjects, chapter-wise notes in Hindi.')


@main_bp.route('/notes/<slug>')
@login_required
def note_detail(slug):
    """View note detail — LOGIN REQUIRED."""
    note = Note.query.filter_by(slug=slug, is_published=True, is_deleted=False).first()
    if not note:
        abort(404)

    # Premium check
    if note.is_premium and not current_user.has_active_premium():
        flash('Ye premium content hai. Premium subscription lein.', 'warning')
        return redirect(url_for('main.premium'))

    note.views = (note.views or 0) + 1
    db.session.commit()

    related = Note.query.filter_by(
        is_published=True, is_deleted=False, subject=note.subject
    ).filter(Note.id != note.id).limit(4).all()

    return render_template('note_detail.html', note=note, related=related,
                           meta_title=note.get_meta_title(),
                           meta_description=note.get_meta_description())


# ============ PAPERS ============

@main_bp.route('/papers')
def papers():
    page = request.args.get('page', 1, type=int)
    exam_filter = request.args.get('exam', '')
    year_filter = request.args.get('year', '')
    search_q = request.args.get('q', '').strip()

    query = Paper.query.filter_by(is_published=True, is_deleted=False)
    if exam_filter:
        query = query.filter(Paper.exam_type == exam_filter)
    if year_filter:
        query = query.filter(Paper.year == year_filter)
    if search_q:
        query = query.filter(or_(
            Paper.title.ilike(f'%{search_q}%'),
            Paper.subject.ilike(f'%{search_q}%'),
        ))
    query = query.order_by(desc(Paper.is_featured), desc(Paper.created_at))

    items, pagination = paginate(query, page, 12)

    years = db.session.query(Paper.year).filter_by(is_published=True, is_deleted=False).distinct().all()
    years = sorted([y[0] for y in years], reverse=True)

    return render_template('papers.html',
                           papers=items, pagination=pagination, years=years,
                           current_exam=exam_filter, current_year=year_filter,
                           search_q=search_q,
                           meta_title='MP Board Old Papers - Previous Year Question Papers PDF - MPVISH',
                           meta_description='Download MP Board, Patwari, Police, Vyapam, CPCT previous year question papers PDF.')


@main_bp.route('/papers/<slug>')
@login_required
def paper_detail(slug):
    """View paper detail — LOGIN REQUIRED."""
    paper = Paper.query.filter_by(slug=slug, is_published=True, is_deleted=False).first()
    if not paper:
        abort(404)

    if paper.is_premium and not current_user.has_active_premium():
        flash('Ye premium content hai. Premium subscription lein.', 'warning')
        return redirect(url_for('main.premium'))

    paper.views = (paper.views or 0) + 1
    db.session.commit()

    related = Paper.query.filter_by(
        is_published=True, is_deleted=False, exam_type=paper.exam_type
    ).filter(Paper.id != paper.id).limit(4).all()

    return render_template('paper_detail.html', paper=paper, related=related,
                           meta_title=paper.get_meta_title(),
                           meta_description=paper.get_meta_description())


# ============ RESULTS ============

@main_bp.route('/results')
def results():
    status_filter = request.args.get('status', '')
    query = Result.query.filter_by(is_published=True, is_deleted=False)
    if status_filter:
        query = query.filter(Result.status == status_filter)
    results_list = query.order_by(desc(Result.created_at)).all()
    return render_template('results.html', results=results_list,
                           current_status=status_filter,
                           meta_title='MP Board Results 2026 - Check 10th & 12th Result - MPVISH',
                           meta_description='Check MP Board results, Patwari, Police, Vyapam, CPCT exam results.')


# ============ GOVT / JOBS ============

@main_bp.route('/govt')
def govt():
    category_filter = request.args.get('category', '')
    search_q = request.args.get('q', '').strip()
    query = Update.query.filter_by(is_published=True, is_deleted=False)
    if category_filter:
        query = query.filter(Update.category == category_filter)
    if search_q:
        query = query.filter(or_(
            Update.title.ilike(f'%{search_q}%'),
            Update.content.ilike(f'%{search_q}%'),
        ))
    updates = query.order_by(desc(Update.is_pinned), desc(Update.created_at)).all()
    return render_template('govt.html', updates=updates,
                           current_category=category_filter, search_q=search_q,
                           meta_title='MP Sarkari Job Updates 2026 - Notifications, Syllabus, Admit Cards - MPVISH',
                           meta_description='Latest MP Sarkari job updates, notifications, admit cards, syllabus, results and government schemes for Madhya Pradesh.')


# ============ MP YOJNA / INFO ============

@main_bp.route('/mp-yojna')
def mp_yojna():
    """MP Yojna & Info page — public, no login required."""
    category_filter = request.args.get('category', '')
    search_q = request.args.get('q', '').strip()
    query = Yojna.query.filter_by(is_published=True, is_deleted=False)
    if category_filter:
        query = query.filter(Yojna.category == category_filter)
    if search_q:
        query = query.filter(or_(
            Yojna.title.ilike(f'%{search_q}%'),
            Yojna.description.ilike(f'%{search_q}%'),
            Yojna.department.ilike(f'%{search_q}%'),
        ))
    yojnas = query.order_by(desc(Yojna.is_featured), Yojna.display_order, desc(Yojna.created_at)).all()
    categories = db.session.query(Yojna.category).filter_by(is_published=True, is_deleted=False).distinct().all()
    categories = sorted([c[0] for c in categories])

    return render_template('mp_yojna.html', yojnas=yojnas, categories=categories,
                           current_category=category_filter, search_q=search_q,
                           meta_title='MP Yojna & Info - Madhya Pradesh Government Schemes - MPVISH',
                           meta_description='MP Sarkari Yojna, government schemes, helpline numbers, and important links for Madhya Pradesh citizens.')


# ============ SEARCH ============

@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    notes_results = []
    papers_results = []

    if q:
        log = SearchLog(query=q[:200],
                        user_id=current_user.id if current_user.is_authenticated else None)
        db.session.add(log)
        db.session.commit()

        notes_results = Note.query.filter_by(is_published=True, is_deleted=False).filter(or_(
            Note.title.ilike(f'%{q}%'),
            Note.subject.ilike(f'%{q}%'),
            Note.chapter.ilike(f'%{q}%'),
        )).order_by(desc(Note.downloads)).limit(20).all()

        papers_results = Paper.query.filter_by(is_published=True, is_deleted=False).filter(or_(
            Paper.title.ilike(f'%{q}%'),
            Paper.subject.ilike(f'%{q}%'),
            Paper.exam_type.ilike(f'%{q}%'),
        )).order_by(desc(Paper.downloads)).limit(20).all()

    return render_template('search.html', query=q,
                           notes_results=notes_results, papers_results=papers_results,
                           meta_title=f'Search: {q} - MPVISH' if q else 'Search - MPVISH',
                           meta_description='Search for notes, papers, and study materials on MPVISH.')


# ============ PREMIUM ============

@main_bp.route('/premium')
def premium():
    plans = PremiumPlan.query.filter_by(is_active=True, is_deleted=False).order_by(PremiumPlan.price_inr).all()
    premium_notes = Note.query.filter_by(is_published=True, is_deleted=False, is_premium=True).order_by(desc(Note.created_at)).limit(12).all()
    premium_papers = Paper.query.filter_by(is_published=True, is_deleted=False, is_premium=True).order_by(desc(Paper.created_at)).limit(12).all()
    has_premium = current_user.is_authenticated and current_user.has_active_premium()

    return render_template('premium.html', plans=plans,
                           premium_notes=premium_notes, premium_papers=premium_papers,
                           has_premium=has_premium,
                           meta_title='Premium Content - Test Series, Mock Tests, Premium Notes - MPVISH',
                           meta_description='Get MPVISH premium access. Download premium notes, test series, and mock tests for MP Board and competitive exams.')


@main_bp.route('/premium/purchase/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def purchase_premium(plan_id):
    from forms import PremiumPurchaseForm
    plan = PremiumPlan.query.get_or_404(plan_id)
    form = PremiumPurchaseForm()
    if form.validate_on_submit():
        purchase = PremiumPurchase(
            user_id=current_user.id,
            plan_id=plan.id,
            amount_paid=plan.price_inr,
            transaction_id=form.transaction_id.data,
            status='pending'
        )
        db.session.add(purchase)
        db.session.commit()
        flash('Payment submitted! Admin approval ka wait karein.', 'success')
        return redirect(url_for('main.premium'))
    return render_template('purchase_premium.html', plan=plan, form=form)


# ============ CMS PAGES ============

@main_bp.route('/page/<slug>')
def cms_page(slug):
    page = Page.query.filter_by(slug=slug, is_published=True, is_deleted=False).first()
    if not page:
        abort(404)
    return render_template('page.html', page=page,
                           meta_title=page.meta_title or page.title,
                           meta_description=page.meta_description or page.title)

@main_bp.route('/about')
def about():
    return redirect(url_for('main.cms_page', slug='about'))

@main_bp.route('/privacy')
def privacy():
    return redirect(url_for('main.cms_page', slug='privacy'))

@main_bp.route('/disclaimer')
def disclaimer():
    return redirect(url_for('main.cms_page', slug='disclaimer'))

@main_bp.route('/contact')
def contact():
    return redirect(url_for('main.cms_page', slug='contact'))

@main_bp.route('/terms')
def terms():
    return redirect(url_for('main.cms_page', slug='terms'))


# ============ DOWNLOAD (ALL REQUIRE LOGIN) ============

@main_bp.route('/download/note/<int:note_id>')
@login_required
def download_note(note_id):
    note = Note.query.filter_by(id=note_id, is_published=True, is_deleted=False).first_or_404()

    if note.is_premium and not current_user.has_active_premium():
        flash('Premium content download karne ke liye premium subscription chahiye.', 'warning')
        return redirect(url_for('main.premium'))

    file_path = get_file_path(note.filename, 'notes')
    if not os.path.exists(file_path):
        abort(404)

    note.downloads = (note.downloads or 0) + 1
    db.session.commit()

    dh = DownloadHistory(
        user_id=current_user.id,
        note_id=note.id,
        ip_hash=hash_ip(request.remote_addr or '0.0.0.0'),
        user_agent=request.headers.get('User-Agent', '')[:300]
    )
    db.session.add(dh)
    db.session.commit()

    return send_from_directory(
        os.path.dirname(file_path),
        os.path.basename(file_path),
        as_attachment=True,
        download_name=note.original_filename or note.filename
    )


@main_bp.route('/download/paper/<int:paper_id>')
@login_required
def download_paper(paper_id):
    paper = Paper.query.filter_by(id=paper_id, is_published=True, is_deleted=False).first_or_404()

    if paper.is_premium and not current_user.has_active_premium():
        flash('Premium content download karne ke liye premium subscription chahiye.', 'warning')
        return redirect(url_for('main.premium'))

    file_path = get_file_path(paper.filename, 'papers')
    if not os.path.exists(file_path):
        abort(404)

    paper.downloads = (paper.downloads or 0) + 1
    db.session.commit()

    dh = DownloadHistory(
        user_id=current_user.id,
        paper_id=paper.id,
        ip_hash=hash_ip(request.remote_addr or '0.0.0.0'),
        user_agent=request.headers.get('User-Agent', '')[:300]
    )
    db.session.add(dh)
    db.session.commit()

    return send_from_directory(
        os.path.dirname(file_path),
        os.path.basename(file_path),
        as_attachment=True,
        download_name=paper.original_filename or paper.filename
    )


# ============ UPLOAD SERVING (hero images etc) ============

@main_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


# ============ SITEMAP & ROBOTS ============

@main_bp.route('/sitemap.xml')
def sitemap():
    site_url = current_app.config.get('SITE_URL', 'http://127.0.0.1:5000').rstrip('/')
    urls = [
        {'loc': f'{site_url}/', 'priority': '1.0'},
        {'loc': f'{site_url}/notes', 'priority': '0.9'},
        {'loc': f'{site_url}/papers', 'priority': '0.9'},
        {'loc': f'{site_url}/results', 'priority': '0.8'},
        {'loc': f'{site_url}/govt', 'priority': '0.8'},
        {'loc': f'{site_url}/mp-yojna', 'priority': '0.8'},
        {'loc': f'{site_url}/premium', 'priority': '0.7'},
    ]
    for note in Note.query.filter_by(is_published=True, is_deleted=False).all():
        urls.append({'loc': f'{site_url}/notes/{note.slug}', 'priority': '0.6'})
    for paper in Paper.query.filter_by(is_published=True, is_deleted=False).all():
        urls.append({'loc': f'{site_url}/papers/{paper.slug}', 'priority': '0.6'})

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f'  <url><loc>{u["loc"]}</loc><priority>{u["priority"]}</priority></url>\n'
    xml += '</urlset>'
    from flask import Response
    return Response(xml, mimetype='application/xml')


@main_bp.route('/robots.txt')
def robots():
    from flask import Response
    return Response(
        'User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: ' +
        current_app.config.get('SITE_URL', '') + '/sitemap.xml',
        mimetype='text/plain'
    )
