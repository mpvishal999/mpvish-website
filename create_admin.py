"""Create admin user for MPVISH."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User

def create_admin():
    app = create_app()
    with app.app_context():
        name = os.environ.get('ADMIN_NAME', 'Admin')
        email = os.environ.get('ADMIN_EMAIL', '')
        password = os.environ.get('ADMIN_PASSWORD', '')

        if not email:
            email = input('Admin Email: ').strip()
        if not password:
            import getpass
            password = getpass.getpass('Admin Password: ')

        existing = User.query.filter_by(email=email.lower()).first()
        if existing:
            print(f'User already exists: {email}')
            existing.role = 'superadmin'
            existing.set_password(password)
            db.session.commit()
            print(f'Role set to superadmin.')
            return

        admin = User(
            name=name,
            email=email.lower(),
            role='superadmin',
            is_active=True,
            is_email_verified=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'\nAdmin user created!')
        print(f'  Name:  {name}')
        print(f'  Email: {email}')
        print(f'  Role:  superadmin')
        print(f'\nLogin at: /admin/login')

if __name__ == '__main__':
    create_admin()
