import logging
from functools import wraps

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from database import db, User, Course, Enrollment, Gig, Application, Lesson

log = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("signin"))
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    uid  = session["user"]["user_id"]
    user = User.query.get_or_404(uid)

    all_enrollments = (
        Enrollment.query
        .filter_by(user_id=uid)
        .join(Course, Enrollment.course_id == Course.course_id)
        .order_by(Enrollment.enroll_id.desc())
        .all()
    )

    enrollments = all_enrollments[:3]

    recent_lessons = (
        Lesson.query
        .join(Course, Lesson.course_id == Course.course_id)
        .order_by(Lesson.created_at.desc(), Lesson.lesson_id.desc())
        .limit(8)
        .all()
    )

    video_items = [
        {
            "lesson_id": lesson.lesson_id,
            "title": lesson.title,
            "instructor": f"{lesson.course.creator.first_name} {lesson.course.creator.last_name}",
            "course_title": lesson.course.title,
            "tags": [lesson.course.title.split()[0] if lesson.course.title else "Course"],
            "duration": lesson.duration_seconds,
        }
        for lesson in recent_lessons
    ]

    recent_gigs = (
        Gig.query
        .order_by(Gig.gig_id.desc())
        .limit(3)
        .all()
    )

    apps = Application.query.filter_by(user_id=uid).all()
    stats = {
        "active_courses": len(all_enrollments),
        "gigs_applied":   len(apps),
        "hours_learned":  sum(
            round((e.progress / 100) * (e.course.duration_hours or 6))
            for e in all_enrollments
        ),
    }

    session_user = {
        "user_id":    user.user_id,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "email":      user.email,
        "role":       user.role,
        "speciality": user.speciality,
    }

    return render_template(
        "dashboard.html",
        user=session_user,
        enrollments=enrollments,
        video_items=video_items,
        gigs=recent_gigs,
        stats=stats,
    )


@dashboard_bp.route("/video-library")
@login_required
def video_library():
    uid  = session["user"]["user_id"]
    user = User.query.get_or_404(uid)

    enrolled_course_ids = [
        e.course_id for e in Enrollment.query.filter_by(user_id=uid).all()
    ]

    if enrolled_course_ids:
        lessons = (
            Lesson.query
            .filter(Lesson.course_id.in_(enrolled_course_ids))
            .join(Course, Lesson.course_id == Course.course_id)
            .order_by(Lesson.created_at.desc(), Lesson.lesson_id.desc())
            .all()
        )
    else:
        lessons = (
            Lesson.query
            .join(Course, Lesson.course_id == Course.course_id)
            .order_by(Lesson.created_at.desc(), Lesson.lesson_id.desc())
            .limit(20)
            .all()
        )

    video_items = []
    for lesson in lessons:
        secs    = lesson.duration_seconds or 0
        dur_str = f"{secs // 60:02d}:{secs % 60:02d}" if secs else "00:00"
        category = getattr(lesson.course, 'category', None) or lesson.course.title.split()[0]
        video_items.append({
            "lesson_id":    lesson.lesson_id,
            "title":        lesson.title,
            "instructor":   f"{lesson.course.creator.first_name} {lesson.course.creator.last_name}",
            "course_title": lesson.course.title,
            "course_id":    lesson.course_id,
            "category":     category,
            "duration":     dur_str,
            "video_path":   lesson.video_path or "",
        })

    categories = sorted(set(v["category"] for v in video_items))

    session_user = {
        "user_id":    user.user_id,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "email":      user.email,
        "role":       user.role,
    }

    return render_template(
        "video_library.html",
        user=session_user,
        video_items=video_items,
        categories=categories,
        total_videos=len(video_items),
    )
