"""MPVISH Website — Main Flask Application."""
import os
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, g, redirect, url_for, jsonify
from config import Config
from extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from routes.main import main_bp
    from routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_globals():
        from models import Setting, Notification
        settings = {}
        try:
            for s in Setting.query.all():
                settings[s.key] = s.value
        except Exception:
            pass

        from flask_login import current_user
        notif_count = 0
        if current_user.is_authenticated:
            notif_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count() + Notification.query.filter_by(
                user_id=None, is_read=False
            ).count()

        return dict(
            site_name=settings.get('site_name', app.config.get('SITE_NAME', 'MPVISH')),
            site_tagline=settings.get('site_tagline', app.config.get('SITE_TAGLINE', 'MP Ki Padhai, Ek Jagah')),
            site_url=app.config.get('SITE_URL', ''),
            contact_email=settings.get('contact_email', app.config.get('CONTACT_EMAIL', '')),
            telegram_url=settings.get('telegram_url', ''),
            youtube_url=settings.get('youtube_url', ''),
            instagram_url=settings.get('instagram_url', ''),
            whatsapp_number=settings.get('whatsapp_number', ''),
            telegram_channel_url=settings.get('telegram_channel_url', ''),
            show_ads=settings.get('show_ads', '1') == '1',
            adsterra_code=settings.get('adsterra_code', ''),
            monetag_code=settings.get('monetag_code', ''),
            adsense_code=settings.get('adsense_code', ''),
            adsense_publisher_id=app.config.get('ADSENSE_PUBLISHER_ID', ''),
            premium_ads=settings.get('premium_ads', '0') == '1',
            google_search_console_code=settings.get('google_search_console_code', ''),
            google_analytics_id=settings.get('google_analytics_id', ''),
            upi_id=settings.get('upi_id', ''),
            payment_instructions=settings.get('payment_instructions', ''),
            notif_count=notif_count,
            google_oauth_enabled=bool(app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET')),
            now=datetime.utcnow(),
        )

    @app.before_request
    def before_request():
        from flask_login import current_user
        g.user = current_user if current_user.is_authenticated else None

        path = request.path
        if not path.startswith('/static') and not path.startswith('/admin') \
                and path not in ('/sitemap.xml', '/robots.txt') and request.method == 'GET':
            try:
                from models import PageView
                ip_hash = hash_ip(request.remote_addr or '0.0.0.0')
                pv = PageView(
                    path=path,
                    user_id=current_user.id if current_user.is_authenticated else None,
                    ip_hash=ip_hash,
                    referrer=request.referrer[:500] if request.referrer else None
                )
                db.session.add(pv)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template('403.html'), 403

    @app.errorhandler(413)
    def too_large_error(e):
        return render_template('500.html', error_msg="File too large. Maximum 50MB allowed."), 413

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.template_filter('human_size')
    def human_size_filter(size):
        from utils import human_file_size
        return human_file_size(size)

    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        from utils import time_ago
        return time_ago(dt)

    @app.template_filter('format_date')
    def format_date_filter(dt):
        if not dt:
            return ''
        return dt.strftime('%d %b %Y')

    @app.template_filter('from_json')
    def from_json_filter(text):
    
        import json
        try:
            return json.loads(text) if text else []
        except (ValueError, TypeError):
            return []

    @app.template_filter('truncate_text')
    def truncate_text_filter(text, length=150):
        if not text:
            return ''
        text = str(text)
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '...'
    @app.template_filter('floatformat')
    def floatformat_filter(value, decimals=0):
        try:
            return f'{value:.{decimals}f}'
        except (TypeError, ValueError):
            return str(value)


    with app.app_context():
        db.create_all()
        _ensure_default_settings()

    return app


def hash_ip(ip_string):
    salt = 'mpvish-salt-v1'
    return hashlib.sha256((ip_string + salt).encode()).hexdigest()[:32]


def _ensure_default_settings():
    from models import Setting
    defaults = {
        'site_name': 'MPVISH',
        'site_tagline': 'MP Ki Padhai, Ek Jagah',
        'contact_email': '',
        'telegram_url': '',
        'youtube_url': '',
        'instagram_url': '',
        'whatsapp_number': '',
        'telegram_channel_url': '',
        'show_ads': '1',
        'adsterra_code': '',
        'monetag_code': '',
        'adsense_code': '',
        'premium_ads': '0',
        'google_search_console_code': '',
        'google_analytics_id': '',
        'upi_id': '',
        'payment_instructions': '',
    }
    for key, value in defaults.items():
        existing = Setting.query.filter_by(key=key).first()
        if not existing:
            s = Setting(key=key, value=value)
            db.session.add(s)
    db.session.commit()


app = create_app()

# === Monetag service worker (ads ke liye) ===
@app.route('/sw.js')
def monetag_sw():
    js = '''self.options = {
    "domain": "3nbf4.com",
    "zoneId": 11813071
}
self.lary = ""
importScripts('https://3nbf4.com/act/files/service-worker.min.js?r=sw')'''
    return js, 200, {'Content-Type': 'application/javascript'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
