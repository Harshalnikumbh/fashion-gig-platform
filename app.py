import os
import uuid
import logging
from functools import wraps
from datetime import datetime
from pathlib import Path

from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify)
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

from database import db, User, Course, Lesson, Gig, Application, Enrollment, Order
from dashboard_routes import dashboard_bp

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")

UPLOAD_ROOT = Path(app.root_path) / "static" / "uploads"
VIDEO_DIR   = UPLOAD_ROOT / "videos"
THUMB_DIR   = UPLOAD_ROOT / "thumbnails"
for _d in (VIDEO_DIR, THUMB_DIR):
    _d.mkdir(parents=True, exist_ok=True)

ALLOWED_VIDEO = {"mp4", "mov", "avi", "mkv", "webm"}
ALLOWED_IMAGE = {"png", "jpg", "jpeg", "webp"}
MAX_VIDEO_MB  = 500

db.init_app(app)
bcrypt = Bcrypt(app)
app.register_blueprint(dashboard_bp)


def allowed_video(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE


def save_upload(file_obj, dest_dir, allowed_fn):
    if not file_obj or file_obj.filename == "":
        return None
    if not allowed_fn(file_obj.filename):
        return None
    ext  = file_obj.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = dest_dir / name
    file_obj.save(path)
    log.info("Saved upload: %s", path)
    return str(path.relative_to(Path(app.root_path) / "static"))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("signin"))
        return f(*args, **kwargs)
    return decorated


def creator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("signin"))
        if session["user"].get("role") != "creator":
            return redirect(url_for("dashboard.dashboard"))
        return f(*args, **kwargs)
    return decorated

def learner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("signin"))
        if session["user"].get("role") != "learner":
            return redirect(url_for("creator_dashboard"))
        return f(*args, **kwargs)
    return decorated


def dashboard_redirect_for(role):
    return "/creator-dashboard" if role == "creator" else "/dashboard"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET"])
def signup():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
    data       = request.get_json(silent=True) or request.form
    first_name = data.get("first_name", "").strip()
    last_name  = data.get("last_name",  "").strip()
    email      = data.get("email",      "").strip().lower()
    password   = data.get("password",   "")
    confirm_pw = data.get("confirm_password", "")
    role       = data.get("role", "learner")
    speciality = data.get("speciality") or None

    if not all([first_name, last_name, email, password]):
        return jsonify({"success": False, "message": "All fields are required."}), 400
    if password != confirm_pw:
        return jsonify({"success": False, "message": "Passwords do not match."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters."}), 400
    if role not in ("learner", "creator"):
        role = "learner"
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "An account with that email already exists."}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_pw,
        role=role,
        speciality=speciality if role == "creator" else None,
    )
    db.session.add(new_user)
    db.session.commit()
    log.info("New user registered: %s [%s]", email, role)

    session["user"] = {
        "user_id":    new_user.user_id,
        "first_name": new_user.first_name,
        "last_name":  new_user.last_name,
        "email":      new_user.email,
        "role":       new_user.role,
    }
    return jsonify({"success": True, "redirect": dashboard_redirect_for(new_user.role)})


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")

    data     = request.get_json(silent=True) or request.form
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        log.warning("Failed login attempt for: %s", email)
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    session["user"] = {
        "user_id":    user.user_id,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "email":      user.email,
        "role":       user.role,
    }
    log.info("User signed in: %s", email)
    return jsonify({"success": True, "redirect": dashboard_redirect_for(user.role)})


@app.route("/logout")
def logout():
    email = session.get("user", {}).get("email", "unknown")
    session.clear()
    log.info("User logged out: %s", email)
    return redirect(url_for("signin"))


@app.route("/profile", methods=["POST"])
@login_required
def update_profile():
    user = User.query.get_or_404(session["user"]["user_id"])
    first_name = request.form.get("first_name", "").strip()
    last_name  = request.form.get("last_name",  "").strip()
    email      = request.form.get("email",      "").strip().lower()
    speciality = request.form.get("speciality", "").strip() or None

    if not first_name or not last_name or not email:
        return redirect(request.form.get("next") or dashboard_redirect_for(user.role))

    existing = User.query.filter_by(email=email).first()
    if existing and existing.user_id != user.user_id:
        return redirect(request.form.get("next") or dashboard_redirect_for(user.role))

    user.first_name = first_name
    user.last_name  = last_name
    user.email      = email
    if user.role == "creator":
        user.speciality = speciality

    db.session.commit()
    log.info("Profile updated for user_id=%s", user.user_id)

    session["user"] = {
        "user_id":    user.user_id,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "email":      user.email,
        "role":       user.role,
    }
    return redirect(request.form.get("next") or dashboard_redirect_for(user.role))


@app.route("/my-courses")
@login_required
def my_courses():
    uid = session["user"]["user_id"]
    enrollments = (
        Enrollment.query
        .filter_by(user_id=uid)
        .join(Course, Enrollment.course_id == Course.course_id)
        .order_by(Enrollment.enroll_id.desc())
        .all()
    )
    total_hours = sum(
        round((e.progress / 100) * (e.course.duration_hours or 6))
        for e in enrollments
    )
    return render_template("my_courses.html", enrollments=enrollments, total_hours=total_hours)

@app.route("/browse-gigs")
@login_required
def browse_gigs():
    return render_template("brow_gigs.html")

@app.route("/my-applications")
@login_required
def my_applications():
    uid = session["user"]["user_id"]
    apps = (
        Application.query
        .filter_by(user_id=uid)
        .join(Gig, Application.gig_id == Gig.gig_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template("my_application.html", applications=apps)


@app.route("/api/gigs/<int:gig_id>/apply", methods=["POST"])
@login_required
def apply_to_gig(gig_id):
    uid  = session["user"]["user_id"]
    gig  = Gig.query.get_or_404(gig_id)

    existing = Application.query.filter_by(user_id=uid, gig_id=gig_id).first()
    if existing:
        return jsonify({"success": False, "message": "Already applied."}), 409

    cover = request.json.get("cover_letter", "") if request.is_json else request.form.get("cover_letter", "")
    app_obj = Application(user_id=uid, gig_id=gig_id, cover_letter=cover, status="pending")
    db.session.add(app_obj)
    db.session.commit()
    log.info("User %s applied to gig %s", uid, gig_id)
    return jsonify({"success": True, "message": f"Applied to '{gig.title}' successfully!"})


@app.route("/api/applications/<int:app_id>/withdraw", methods=["POST"])
@login_required
def withdraw_application(app_id):
    uid    = session["user"]["user_id"]
    app_obj = Application.query.get_or_404(app_id)
    if app_obj.user_id != uid:
        return jsonify({"success": False, "message": "Not authorised."}), 403
    db.session.delete(app_obj)
    db.session.commit()
    log.info("Application %s withdrawn by user %s", app_id, uid)
    return jsonify({"success": True})


@app.route("/course/<int:course_id>/learn")
@login_required
def course_learn(course_id):
    uid    = session["user"]["user_id"]
    course = Course.query.get_or_404(course_id)
    enroll = Enrollment.query.filter_by(user_id=uid, course_id=course_id).first()
    if not enroll:
        return redirect(url_for("browse_gigs"))
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.position).all()
    return render_template("course_learn.html", course=course, lessons=lessons, enrollment=enroll)


@app.route("/api/course/<int:course_id>/progress", methods=["POST"])
@login_required
def update_progress(course_id):
    uid    = session["user"]["user_id"]
    enroll = Enrollment.query.filter_by(user_id=uid, course_id=course_id).first_or_404()
    pct    = float(request.json.get("progress", enroll.progress))
    enroll.progress = min(pct, 100.0)
    db.session.commit()
    return jsonify({"success": True, "progress": enroll.progress})


@app.route("/creator-dashboard")
@creator_required
def creator_dashboard():
    uid     = session["user"]["user_id"]
    creator = User.query.get_or_404(uid)
    courses = Course.query.filter_by(creator_id=uid).order_by(Course.course_id.desc()).all()
    gigs    = Gig.query.filter_by(creator_id=uid).order_by(Gig.gig_id.desc()).all()
    orders  = (
        Order.query.join(Gig, Order.gig_id == Gig.gig_id)
        .filter(Gig.creator_id == uid)
        .count()
    )
    return render_template(
        "creator_dashboard.html",
        user=creator,
        courses=courses,
        gigs=gigs,
        stats={"courses": len(courses), "gigs": len(gigs), "orders": orders},
    )


@app.route("/upload-course", methods=["GET", "POST"])
@creator_required
def upload_course():
    creator = User.query.get_or_404(session["user"]["user_id"])

    if request.method == "POST":
        title       = request.form.get("course_title", "").strip()
        description = request.form.get("description",  "").strip()
        price_raw   = request.form.get("price", "0").strip()
        if not title or not description:
            return render_template("upload_course.html", user=creator,
                                   error_message="Title and description are required."), 400
        try:
            price = float(price_raw or 0)
        except ValueError:
            return render_template("upload_course.html", user=creator,
                                   error_message="Price must be a valid number."), 400

        course = Course(
            title=title, description=description, price=price,
            creator_id=creator.user_id,
        )
        db.session.add(course)
        db.session.flush()

        lesson_titles = request.form.getlist("lesson_title[]")
        lesson_videos = request.files.getlist("lesson_video[]")

        for pos, (l_title, l_file) in enumerate(zip(lesson_titles, lesson_videos), start=1):
            l_title = l_title.strip()
            if not l_title:
                continue
            vid_path = save_upload(l_file, VIDEO_DIR, allowed_video)
            lesson = Lesson(
                course_id=course.course_id,
                title=l_title,
                position=pos,
                video_path=vid_path,
            )
            db.session.add(lesson)

        db.session.commit()
        log.info("Course created: '%s' by creator %s", title, creator.user_id)
        return redirect(url_for("creator_dashboard"))

    return render_template("upload_course.html", user=creator)


@app.route("/post-a-gig", methods=["GET", "POST"])
@creator_required
def post_a_gig():
    creator = User.query.get_or_404(session["user"]["user_id"])

    if request.method == "POST":
        title       = request.form.get("gig_title",   "").strip()
        description = request.form.get("description", "").strip()
        category    = request.form.get("category",    "").strip()
        min_b_raw   = request.form.get("min_budget",  "0").strip()
        max_b_raw   = request.form.get("max_budget",  "0").strip()

        if not title or not description:
            return render_template("post_a_gig.html", user=creator,
                                   error_message="Title and description are required."), 400
        try:
            min_b = float(min_b_raw or 0)
            max_b = float(max_b_raw or 0)
        except ValueError:
            return render_template("post_a_gig.html", user=creator,
                                   error_message="Budget must be valid numbers."), 400

        gig = Gig(
            title=title, description=description,
            budget=max(max_b, min_b), category=category,
            creator_id=creator.user_id,
        )
        db.session.add(gig)
        db.session.commit()
        log.info("Gig posted: '%s' by creator %s", title, creator.user_id)
        return redirect(url_for("creator_dashboard"))

    return render_template("post_a_gig.html", user=creator)


@app.route("/api/gigs")
@login_required
def api_list_gigs():
    category = request.args.get("category", "").strip()
    q        = request.args.get("q", "").strip().lower()
    query    = Gig.query
    if category and category != "all":
        query = query.filter(Gig.category == category)
    if q:
        query = query.filter(Gig.title.ilike(f"%{q}%"))
    gigs = query.order_by(Gig.gig_id.desc()).all()
    return jsonify([
        {
            "gig_id":      g.gig_id,
            "title":       g.title,
            "description": g.description,
            "category":    g.category,
            "budget":      g.budget,
        }
        for g in gigs
    ])


@app.route("/api/enroll/<int:course_id>", methods=["POST"])
@login_required
def enroll_course(course_id):
    uid    = session["user"]["user_id"]
    course = Course.query.get_or_404(course_id)
    exists = Enrollment.query.filter_by(user_id=uid, course_id=course_id).first()
    if exists:
        return jsonify({"success": False, "message": "Already enrolled."}), 409
    enroll = Enrollment(user_id=uid, course_id=course_id, progress=0.0)
    db.session.add(enroll)
    db.session.commit()
    log.info("User %s enrolled in course %s", uid, course_id)
    return jsonify({"success": True})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        log.info("Tables created / verified.")
    app.run(debug=os.getenv("FLASK_DEBUG", "False") == "True")
