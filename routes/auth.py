"""Auth routes for MPVISH Website."""
import os, secrets, hashlib
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, abort
from extensions import db
from models import User, Notification
from forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm
from flask_login import login_user, logout_user, login_required, current_user
from utils import hash_ip

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None:
            flash('Email galat hai. Registration karein.', 'danger')
            return render_template('login.html', form=form)
        if user.is_locked():
            flash('Account temporarily locked. Thodi der baad try karein.', 'danger')
            return render_template('login.html', form=form)
        if not user.is_active:
            flash('Account deactivated hai. Admin se sampark karein.', 'danger')
            return render_template('login.html', form=form)
        if not user.check_password(form.password.data):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()
            flash('Password galat hai.', 'danger')
            return render_template('login.html', form=form)

        # Success — track login
        user.last_login = datetime.utcnow()
        user.last_login_ip = hash_ip(request.remote_addr or '0.0.0.0')
        user.login_count = (user.login_count or 0) + 1
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('main.index'))
    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if request.method == 'GET':
        return redirect(url_for('auth.login') + '#register')
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Ye email already registered hai. Login karein.', 'warning')
            return redirect(url_for('auth.login'))
        user = User(name=form.name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Welcome notification
        notif = Notification(user_id=user.id, title='MPVISH me swagat hai!',
                             message='Registration successful! Ab aap notes, papers download kar sakte hain.')
        db.session.add(notif)
        db.session.commit()

        login_user(user)
        flash(f'Welcome to MPVISH, {user.name}!', 'success')
        return redirect(url_for('main.index'))
    return render_template('register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Aap safaltapoorvak logout ho gaye.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('profile.html', form=form)


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    from models import DownloadHistory, PremiumPurchase
    downloads = DownloadHistory.query.filter_by(user_id=current_user.id).order_by(
        DownloadHistory.created_at.desc()
    ).limit(10).all()
    purchases = PremiumPurchase.query.filter_by(user_id=current_user.id).order_by(
        PremiumPurchase.created_at.desc()
    ).all()
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(5).all()
    return render_template('user_dashboard.html', downloads=downloads, purchases=purchases, notifs=notifs)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password galat hai.', 'danger')
            return render_template('change_password.html', form=form)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password change ho gaya!', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('change_password.html', form=form)


@auth_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()
    broadcast = Notification.query.filter_by(user_id=None).order_by(
        Notification.created_at.desc()
    ).all()
    return render_template('notifications.html', notifs=notifs, broadcast=broadcast)


@auth_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    Notification.query.filter_by(user_id=None, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('auth.notifications'))


# ============ Google OAuth (optional) ============

@auth_bp.route('/login/google')
def google_login():
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        flash('Google login abhi available nahi hai.', 'info')
        return redirect(url_for('auth.login'))

    from requests_oauthlib import OAuth2Session
    redirect_uri = current_app.config.get('SITE_URL', '').rstrip('/') + '/login/google/callback'
    scope = ['openid', 'email', 'profile']
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        access_type='offline', prompt='select_account'
    )
    session['oauth_state'] = state
    return redirect(authorization_url)


@auth_bp.route('/login/google/callback')
def google_callback():
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        flash('Google login abhi available nahi hai.', 'info')
        return redirect(url_for('auth.login'))

    from requests_oauthlib import OAuth2Session
    if request.args.get('state') != session.pop('oauth_state', None):
        abort(400, 'Invalid state')

    redirect_uri = current_app.config.get('SITE_URL', '').rstrip('/') + '/login/google/callback'
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
    token = oauth.fetch_token(
        'https://oauth2.googleapis.com/token',
        authorization_response=request.url,
        client_secret=client_secret
    )
    resp = oauth.get('https://www.googleapis.com/oauth2/v3/userinfo')
    user_info = resp.json()

    email = user_info.get('email', '').lower().strip()
    name = user_info.get('name', email.split('@')[0])
    if not email:
        flash('Google se email nahi mila.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, is_email_verified=True)
        import secrets as s
        user.set_password(s.token_urlsafe(32))
        db.session.add(user)
        db.session.commit()
        notif = Notification(user_id=user.id, title='MPVISH me swagat hai!',
                             message='Google ke through registration successful!')
        db.session.add(notif)
        db.session.commit()

    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    user.last_login_ip = hash_ip(request.remote_addr or '0.0.0.0')
    db.session.commit()
    login_user(user)
    flash(f'Welcome, {user.name}!', 'success')
    return redirect(url_for('main.index'))
