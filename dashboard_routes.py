import sqlite3
from pathlib import Path

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request

DB_PATH = Path(__file__).parent / "applications.db"

dashboard_bp = Blueprint('dashboard', __name__)
# helpers 
def login_required(f):
    """Simple session guard — swap for flask_login if you add that later."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('signin'))
        return f(*args, **kwargs)

    return decorated

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gig_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gig_id INTEGER NOT NULL,
                gig_title TEXT NOT NULL,
                applicant_name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# mock data (replace with real DB queries later) 

ENROLLED_COURSES = [
    {
        "id": 1,
        "title": "Fundamentals of Fabric Draping",
        "instructor": "Meera Kapoor",
        "tag": "Draping",
        "total_lessons": 12,
        "completed_lessons": 5,
        "progress": 42,
        "thumb_class": "ct1",
    },
    {
        "id": 2,
        "title": "Zero to Pro: Garment Patterns",
        "instructor": "Arjun Mehta",
        "tag": "Patterns",
        "total_lessons": 15,
        "completed_lessons": 2,
        "progress": 13,
        "thumb_class": "ct2",
    },
    {
        "id": 3,
        "title": "Fashion Illustration for Beginners",
        "instructor": "Divya Rao",
        "tag": "Illustration",
        "total_lessons": 10,
        "completed_lessons": 8,
        "progress": 80,
        "thumb_class": "ct3",
    },
]

VIDEO_LIBRARY = [
    {
        "id": 101,
        "title": "Advanced Saree Draping Techniques",
        "instructor": "Meera Kapoor",
        "rating": 4.9,
        "duration": "18:34",
        "tags": ["Draping", "Saree"],
        "thumb_class": "vt1",
    },
    {
        "id": 102,
        "title": "Reading & Grading Pattern Sheets",
        "instructor": "Arjun Mehta",
        "rating": 4.8,
        "duration": "24:10",
        "tags": ["Patterns", "Grading"],
        "thumb_class": "vt2",
    },
    {
        "id": 103,
        "title": "Croquis Figure Drawing — Fashion Poses",
        "instructor": "Divya Rao",
        "rating": 4.7,
        "duration": "12:55",
        "tags": ["Illustration", "Drawing"],
        "thumb_class": "vt3",
    },
    {
        "id": 104,
        "title": "Eco Fabrics & Sustainable Sourcing",
        "instructor": "Priya Nair",
        "rating": 4.9,
        "duration": "31:22",
        "tags": ["Sustainable", "Fabric"],
        "thumb_class": "vt4",
    },
]

GIG_LISTINGS = [
    {
        "id": 201,
        "title": "Bridal Collection Designer — 12 Looks",
        "category": "Bridal",
        "urgent": True,
        "days_left": 2,
        "description": (
            "Looking for a skilled draper for a bridal trousseau line. "
            "Must know lehenga silhouettes and blouse patterns."
        ),
        "budget_min": 25000,
        "budget_max": 40000,
        "location": "Mumbai",
        "remote": False,
        "duration": "3 weeks",
    },
    {
        "id": 202,
        "title": "Streetwear Pattern Maker — Men's Line",
        "category": "Pattern Making",
        "urgent": False,
        "days_left": 7,
        "description": (
            "Youth streetwear brand needs pattern drafts for drop-shoulder tees, "
            "cargo trousers & hoodies in 3 sizes."
        ),
        "budget_min": 8000,
        "budget_max": 15000,
        "location": "Remote",
        "remote": True,
        "duration": "1 week",
    },
    {
        "id": 203,
        "title": "Fashion Illustrator — Lookbook 2025",
        "category": "Illustration",
        "urgent": False,
        "days_left": 12,
        "description": (
            "Indie label needs 20 fashion illustrations for their upcoming "
            "spring/summer digital lookbook. Flat & croquis styles."
        ),
        "budget_min": 12000,
        "budget_max": 20000,
        "location": "Remote",
        "remote": True,
        "duration": "10 days",
    },
]

SKILL_PROGRESS = [
    {"name": "Fabric Draping",       "pct": 68},
    {"name": "Pattern Making",       "pct": 32},
    {"name": "Fashion Illustration", "pct": 81},
    {"name": "Stitching & Tailoring","pct": 45},
]

UPCOMING_SESSIONS = [
    {"day": "19", "month": "Apr", "title": "Live Q&A — Draping Masterclass",    "host": "Meera Kapoor",  "time": "4:00 PM IST"},
    {"day": "22", "month": "Apr", "title": "Workshop: Gig Portfolio Review",    "host": "AtelierX Team", "time": "11:00 AM IST"},
    {"day": "25", "month": "Apr", "title": "Pattern Grading — Hands-on Lab",    "host": "Arjun Mehta",   "time": "3:30 PM IST"},
]

# routes 
@dashboard_bp.route('/dashboard')
@login_required  
def dashboard():
    """Main learner dashboard page."""
    # In a real app, pull user from session / DB:
    user = session.get('user', {
        "first_name": "Sanjivani",
        "last_name": "Sharma",
        "role": "learner",
        "streak": 5,
        "hours_learned": 12,
        "gigs_applied": 2,
    })

    return render_template(
        'dashboard.html',
        user=user,
        courses=ENROLLED_COURSES,
        videos=VIDEO_LIBRARY,
        gigs=GIG_LISTINGS,
        skills=SKILL_PROGRESS,
        sessions=UPCOMING_SESSIONS,
    )


# API endpoints (AJAX / future mobile use) 

@dashboard_bp.route('/api/courses')
def api_courses():
    """Return enrolled courses as JSON."""
    return jsonify(ENROLLED_COURSES)


@dashboard_bp.route('/api/videos')
def api_videos():
    """Return video library as JSON. Supports ?tag= filter."""
    # from flask import request
    tag = request.args.get('tag', '').strip()
    results = (
        [v for v in VIDEO_LIBRARY if tag in v['tags']]
        if tag else VIDEO_LIBRARY
    )
    return jsonify(results)


@dashboard_bp.route('/api/gigs')
def api_gigs():
    """Return gig listings as JSON."""
    return jsonify(GIG_LISTINGS)


@dashboard_bp.route('/api/gigs/<int:gig_id>/apply', methods=['POST'])
# @login_required
def apply_gig(gig_id):
    """Record a gig application (stub — wire to DB later)."""
    gig = next((g for g in GIG_LISTINGS if g['id'] == gig_id), None)
    if not gig:
        return jsonify({"error": "Gig not found"}), 404

    applicant = session.get("user", {})
    applicant_name = " ".join(
        part for part in (applicant.get("first_name"), applicant.get("last_name")) if part
    ) or "Guest"
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO gig_applications (gig_id, gig_title, applicant_name) VALUES (?, ?, ?)",
            (gig["id"], gig["title"], applicant_name),
        )

    return jsonify({"success": True, "message": f"Applied to '{gig['title']}' successfully!"})
