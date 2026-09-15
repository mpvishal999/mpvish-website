"""Utility functions for MPVISH."""
import os
import re
import hashlib
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


def slugify(text):
    """Convert text to URL-friendly slug."""
    if not text:
        return 'untitled'
    # Normalize
    text = str(text).lower().strip()
    # Replace Hindi/Devanagari chars with hyphens (keep ascii)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    if not text:
        # Fallback: use a short hash
        text = 'item-' + uuid.uuid4().hex[:8]
    return text


def ensure_unique_slug(model_class, slug, exclude_id=None):
    """Ensure slug is unique by appending -2, -3, etc. if needed."""
    base = slug
    counter = 1
    while True:
        query = model_class.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(model_class.id != exclude_id)
        if not query.first():
            break
        counter += 1
        slug = f"{base}-{counter}"
    return slug


def allowed_file(filename):
    """Check if file extension is allowed."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed


def save_uploaded_file(file, subdir='notes'):
    """Save an uploaded file with a unique name. Returns (filename, original_filename, file_size)."""
    if not file or not file.filename:
        return None, None, 0
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'pdf'
    unique_name = f"{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}.{ext}"

    upload_dir = current_app.config['UPLOAD_FOLDER']
    target_dir = os.path.join(upload_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, unique_name)

    file.save(target_path)
    file_size = os.path.getsize(target_path)

    return unique_name, original_filename, file_size


def get_file_path(filename, subdir='notes'):
    """Get absolute path of a stored file."""
    upload_dir = current_app.config['UPLOAD_FOLDER']
    return os.path.join(upload_dir, subdir, filename)


def delete_file(filename, subdir='notes'):
    """Delete a stored file if it exists."""
    path = get_file_path(filename, subdir)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def human_file_size(size_bytes):
    """Convert bytes to human readable size."""
    if not size_bytes:
        return '0 B'
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.0f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def hash_ip(ip_string):
    """Hash an IP address for privacy-conscious storage."""
    salt = current_app.config.get('SECRET_KEY', 'salt')[:16]
    return hashlib.sha256((ip_string + salt).encode()).hexdigest()[:32]


def time_ago(dt):
    """Human friendly time-ago string in Hinglish."""
    if not dt:
        return ''
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'abhi'
    elif seconds < 3600:
        return f"{int(seconds / 60)} min pehle"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} ghante pehle"
    elif seconds < 604800:
        return f"{int(seconds / 86400)} din pehle"
    else:
        return dt.strftime('%d %b %Y')


def paginate(query, page, per_page):
    """Paginate a SQLAlchemy query. Returns (items, pagination_info)."""
    page = max(1, page)
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pagination = {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else 1,
        'next_page': page + 1 if page < total_pages else total_pages,
    }
    return items, pagination


def log_audit(admin_user_id, action, entity_type=None, entity_id=None, details=''):
    """Create an audit log entry."""
    from models import AuditLog
    log = AuditLog(
        admin_user_id=admin_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )
    from extensions import db
    db.session.add(log)
    db.session.commit()


def sanitize_html(html_text):
    """Sanitize HTML content using bleach."""
    try:
        import bleach
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a', 'h2', 'h3', 'h4', 'blockquote']
        allowed_attrs = {'a': ['href', 'title', 'rel', 'target']}
        return bleach.clean(html_text, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    except ImportError:
        return html_text


def get_all_settings():
    """Load all settings from DB as a dict."""
    from models import Setting
    settings = {}
    for s in Setting.query.all():
        settings[s.key] = s.value
    return settings


def is_safe_url(target):
    """Check if a redirect URL is safe (same host)."""
    from urllib.parse import urljoin, urlparse
    from flask import request
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
