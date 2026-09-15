"""Seed data for MPVISH — creates demo notes, papers, updates, results, yojnas, pages."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import (User, Note, Paper, Update, Result, Yojna, PremiumPlan,
                    Page, Setting)
from utils import slugify, ensure_unique_slug

def seed():
    app = create_app()
    with app.app_context():
        # Create default settings
        defaults = {
            'site_name': 'MPVISH',
            'site_tagline': 'MP Ki Padhai, Ek Jagah',
        }
        for k, v in defaults.items():
            if not Setting.query.filter_by(key=k).first():
                db.session.add(Setting(key=k, value=v))
        db.session.commit()

        # Admin user
        if not User.query.filter_by(email='admin@mpvish.in').first():
            admin = User(name='Admin', email='admin@mpvish.in', role='superadmin', is_active=True)
            admin.set_password('Admin@12345')
            db.session.add(admin)

        # Demo user
        if not User.query.filter_by(email='student@example.com').first():
            student = User(name='Test Student', email='student@example.com', role='user')
            student.set_password('Student@123')
            db.session.add(student)

        # Notes
        if not Note.query.first():
            notes_data = [
                {'class_level': '10th', 'subject': 'Mathematics', 'chapter': 'Trigonometry', 'title': 'Trigonometry Notes - Class 10'},
                {'class_level': '10th', 'subject': 'Science', 'chapter': 'Light', 'title': 'Light Reflection and Refraction'},
                {'class_level': '12th', 'subject': 'Physics', 'chapter': 'Electrostatics', 'title': 'Electrostatics Notes - Class 12'},
                {'class_level': '12th', 'subject': 'Chemistry', 'chapter': 'Aldehydes', 'title': 'Aldehydes and Ketones Notes'},
            ]
            for nd in notes_data:
                n = Note(
                    class_level=nd['class_level'], subject=nd['subject'],
                    chapter=nd['chapter'], title=nd['title'],
                    filename='placeholder.pdf', slug=ensure_unique_slug(Note, slugify(nd['title'])),
                    description='Demo note for testing.'
                )
                db.session.add(n)

        # Papers
        if not Paper.query.first():
            papers_data = [
                {'exam_type': 'MP Board', 'year': '2024', 'subject': 'Mathematics', 'title': 'MP Board 10th Math Paper 2024'},
                {'exam_type': 'MP Board', 'year': '2023', 'subject': 'Science', 'title': 'MP Board 10th Science Paper 2023'},
                {'exam_type': 'Patwari', 'year': '2023', 'subject': 'General Knowledge', 'title': 'Patwari Exam Paper 2023'},
            ]
            for pd in papers_data:
                p = Paper(
                    exam_type=pd['exam_type'], year=pd['year'], subject=pd['subject'],
                    title=pd['title'], filename='placeholder.pdf',
                    slug=ensure_unique_slug(Paper, slugify(pd['title']))
                )
                db.session.add(p)

        # Updates
        if not Update.query.first():
            updates_data = [
                {'title': 'MP Patwari Recruitment 2026', 'content': 'MP Patwari bharti notification released. 5000+ posts.', 'category': 'notification', 'is_pinned': True, 'link': '#'},
                {'title': 'MP Police Constable Admit Card', 'content': 'MP Police Constable exam admit card released.', 'category': 'admit_card', 'link': '#'},
            ]
            for ud in updates_data:
                u = Update(**ud)
                db.session.add(u)

        # Results
        if not Result.query.first():
            db.session.add(Result(exam_name='MP Board 10th Result 2026', result_date='TBA', status='upcoming'))
            db.session.add(Result(exam_name='MP Board 12th Result 2026', result_date='TBA', status='upcoming'))

        # Yojnas
        if not Yojna.query.first():
            yojnas_data = [
                {'title': 'Mukhyamantri Ladli Behna Yojana', 'description': 'MP govt scheme for women financial assistance.', 'category': 'scheme', 'department': 'Department of Women and Child Development', 'eligibility': 'Women 21-60 years, MP resident', 'benefits': 'Rs 1250/month', 'link': '#', 'is_featured': True, 'helpline_number': '1800-XXX-XXXX'},
                {'title': 'Mukhyamantri Kisan Kalyan Yojana', 'description': 'Financial assistance for farmers in MP.', 'category': 'scheme', 'department': 'Agriculture Department', 'eligibility': 'MP farmers', 'benefits': 'Rs 4000/year', 'link': '#'},
                {'title': 'MP Citizen Helpline', 'description': '24x7 helpline for MP citizens.', 'category': 'helpline', 'helpline_number': '181'},
                {'title': 'MP e-District Portal', 'description': 'Online services for certificates and documents.', 'category': 'link', 'link': '#', 'link_text': 'Visit Portal'},
            ]
            for yd in yojnas_data:
                y = Yojna(**yd)
                db.session.add(y)

        # Premium plans
        if not PremiumPlan.query.first():
            db.session.add(PremiumPlan(name='Monthly', price_inr=49, duration_days=30, features_json='["Unlimited Downloads","Premium Notes Access","Test Series"]', is_active=True))
            db.session.add(PremiumPlan(name='Yearly', price_inr=499, duration_days=365, features_json='["Unlimited Downloads","Premium Notes Access","Test Series","Priority Support","Ad-Free"]', is_active=True))

        # Pages
        if not Page.query.first():
            for slug, title in [('about','About Us'), ('privacy','Privacy Policy'), ('contact','Contact Us'), ('disclaimer','Disclaimer'), ('terms','Terms & Conditions')]:
                db.session.add(Page(title=title, slug=slug, content=f'<p>{title} page content.</p>'))

        db.session.commit()
        print('Seed data created successfully!')

if __name__ == '__main__':
    seed()
