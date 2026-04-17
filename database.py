from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    user_id    = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50),  nullable=False)
    last_name  = db.Column(db.String(50),  nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(10),  nullable=False)
    speciality = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='applicant', lazy=True,
                                   cascade='all, delete-orphan')

    courses     = db.relationship('Course',     backref='creator',  lazy=True)
    gigs        = db.relationship('Gig',        backref='creator',  lazy=True)
    enrollments = db.relationship('Enrollment', backref='learner',  lazy=True)
    orders      = db.relationship('Order',      backref='learner',  lazy=True)
    reviews     = db.relationship('Review',     backref='reviewer', lazy=True)

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'

class Course(db.Model):
    __tablename__ = 'course'

    course_id   = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    price       = db.Column(db.Float,       nullable=False, default=0.0)
    creator_id  = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)

    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    lessons     = db.relationship('Lesson', backref='course', lazy=True,
                                  cascade='all, delete-orphan',
                                  order_by='Lesson.position')

    @property
    def lesson_count(self):
        return len(self.lessons)

    @property
    def duration_hours(self):
        total = sum(l.duration_seconds or 0 for l in self.lessons)
        return round(total / 3600, 1) or 6

    def __repr__(self):
        return f'<Course {self.title}>'


class Lesson(db.Model):
    __tablename__ = 'lesson'

    lesson_id        = db.Column(db.Integer, primary_key=True)
    course_id        = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    title            = db.Column(db.String(200), nullable=False)
    position         = db.Column(db.Integer, default=1)
    video_path       = db.Column(db.String(400), nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Lesson {self.title}>'

class Gig(db.Model):
    __tablename__ = 'gig'

    gig_id      = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    budget      = db.Column(db.Float,       nullable=False, default=0.0)
    creator_id  = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)

    orders       = db.relationship('Order',       backref='gig',       lazy=True)
    reviews      = db.relationship('Review',      backref='gig',       lazy=True)
    applications = db.relationship('Application', backref='gig',       lazy=True,
                                   cascade='all, delete-orphan')
    category     = db.Column(db.String(80),  nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Gig {self.title}>'


class Application(db.Model):
    __tablename__ = 'application'

    app_id      = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    gig_id      = db.Column(db.Integer, db.ForeignKey('gig.gig_id'),   nullable=False)
    cover_letter= db.Column(db.Text,    nullable=True)
    status      = db.Column(db.String(20), default='pending')
    applied_at  = db.Column(db.DateTime,  default=datetime.utcnow)

    def __repr__(self):
        return f'<Application user={self.user_id} gig={self.gig_id} [{self.status}]>'

class Enrollment(db.Model):
    __tablename__ = 'enrollment'

    enroll_id = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.user_id'),     nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)
    progress  = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Enrollment user={self.user_id} course={self.course_id}>'

class Order(db.Model):
    __tablename__ = 'order'

    order_id      = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    gig_id        = db.Column(db.Integer, db.ForeignKey('gig.gig_id'),   nullable=False)
    status        = db.Column(db.String(30), default='pending')
    delivery_date = db.Column(db.DateTime,  nullable=True)

    payment = db.relationship('Payment', backref='order', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Order {self.order_id} [{self.status}]>'

class Payment(db.Model):
    __tablename__ = 'payment'

    payment_id     = db.Column(db.Integer, primary_key=True)
    order_id       = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False, unique=True)
    amount         = db.Column(db.Float,   nullable=False)
    payment_status = db.Column(db.String(20), default='unpaid')
    created_at     = db.Column(db.DateTime,   default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment order={self.order_id} [{self.payment_status}]>'

class Review(db.Model):
    __tablename__ = 'review'

    review_id  = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    gig_id     = db.Column(db.Integer, db.ForeignKey('gig.gig_id'),   nullable=False)
    rating     = db.Column(db.Integer, nullable=False)
    comment    = db.Column(db.Text,    nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review gig={self.gig_id} rating={self.rating}>'