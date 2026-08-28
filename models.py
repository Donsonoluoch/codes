# models.py

from datetime import date, datetime
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(128), nullable=False)
    email         = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type     = db.Column(db.String(10), nullable=False)  # 'admin' or 'student'
    def set_password(self, password):
        """Hash & store the given plaintext password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the given plaintext password matches."""
        return check_password_hash(self.password_hash, password)
    # One-to-one: each User may have one Student profile
      # Consolidate the two relationships into a single one
    student_profile = db.relationship(
        'Student',
        back_populates='user',
        uselist=False,
        # This includes the cascade rule from your original 'student_profile'
        cascade='all, delete-orphan'
    )

    student = db.relationship('Student', back_populates='user', uselist=False)
class Student(db.Model):
    __tablename__ = 'student'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dob            = db.Column(db.Date, nullable=False)
    address        = db.Column(db.String(256))
    qualifications = db.Column(db.String(256))
    reg_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    marks = db.relationship('Mark', backref='student', lazy=True)
     # Link back to User, with back_populates pointing to the single relationship
    user = db.relationship(
        'User',
        back_populates='student_profile'
    )
    user = db.relationship('User', back_populates='student')
    # Enrollment relationship
    enrollments = db.relationship(
        'Enrollment',
        back_populates='student',
        cascade='all, delete-orphan'
    )
    # Submissions relationships
    submissions = db.relationship('ReportSubmission', back_populates='student')
   
    # Deferement requests
    deferments     = db.relationship('DefermentRequest', back_populates='student')
    # Optional proxy for convenient .courses access:
    courses = association_proxy(
        'enrollments',
        'course',
        creator=lambda course: Enrollment(course=course)
    )
    # NEW: mark if the student is currently deferred/paused
    is_deferred    = db.Column(db.Boolean, default=False, nullable=False)
    # Deferement requests
    deferments     = db.relationship('DefermentRequest', back_populates='student')
    
    @property
    def full_name(self):
        return self.user.name


class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)   # e.g. "Spring 2025"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    marks = db.relationship('Mark', backref='semester', lazy=True)
    reports = db.relationship('SemesterReport', back_populates='semester')

    def __repr__(self):
        return f"<Semester {self.name}>"
class Course(db.Model):
    __tablename__ = 'course'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(128), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date   = db.Column(db.Date, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    faculty = db.relationship(
        'Faculty',
        back_populates='courses'
    )
    marks = db.relationship('Mark', backref='course', lazy=True)
    enrollments = db.relationship(
        'Enrollment',
        back_populates='course',
        cascade='all, delete-orphan'
    )

    # Optional proxy for .students
    students = association_proxy('enrollments', 'student')

    def is_active(self):
        return date.today() <= self.end_date

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    courses = db.relationship('Course', back_populates='faculty')
class Enrollment(db.Model):
    __tablename__ = 'enrollment'

    student_id  = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey('course.id'),  primary_key=True)
    enroll_date = db.Column(db.Date,   nullable=False, default=date.today)
    expiry_date = db.Column(db.Date,   nullable=False)

    student = db.relationship('Student', back_populates='enrollments')
    course  = db.relationship('Course',  back_populates='enrollments')

    def __init__(self, course, enroll_date=None, expiry_date=None):
        # Always associate the course
        self.course      = course
        # Use provided enroll_date or default to today
        self.enroll_date = enroll_date or date.today()
        # If no expiry_date, default to the course’s end_date
        self.expiry_date = expiry_date or course.end_date

    @property
    def is_active(self):
        return date.today() <= self.expiry_date

    @property
    def days_until_expiry(self):
        return (self.expiry_date - date.today()).days

    @property
    def days_elapsed(self):
        return (date.today() - self.enroll_date).days

    @property
    def total_duration(self):
        return (self.expiry_date - self.enroll_date).days


class AcademicIssue(db.Model):
    __tablename__ = 'academic_issue'

    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    issue_type    = db.Column(db.String(64), nullable=False)
    reported_date = db.Column(db.Date, nullable=False, default=date.today)
    status        = db.Column(db.String(20), nullable=False, default='open')  # open/in-progress/resolved

    student = db.relationship('Student', backref='academic_issues')

class ReportingPeriod(db.Model):
    __tablename__ = 'reporting_period'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)   # e.g. “Fall 2025 Kickoff”
    start_date = db.Column(db.Date, nullable=False)
    end_date   = db.Column(db.Date, nullable=False)
    active     = db.Column(db.Boolean, default=True)         # toggle on/off
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

class ReportSubmission(db.Model):
    __tablename__ = 'report_submission'
    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    period_id    = db.Column(db.Integer, db.ForeignKey('reporting_period.id'), nullable=False)
    content      = db.Column(db.Text, nullable=False)                # free-text report
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='submissions')
    period  = db.relationship('ReportingPeriod', backref='submissions')

from sqlalchemy import Enum

class DefermentRequest(db.Model):
    __tablename__ = 'deferment_request'
    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    submitted_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # NEW: reason enum
    reason        = db.Column(
                     Enum('medical','financial','personal', name='defer_reason'),
                     nullable=False
                   )

    status        = db.Column(
                     db.Enum('pending','approved','declined', name='defer_status'),
                     default='pending', nullable=False
                   )
    student_notes = db.Column(db.Text)
    admin_notes   = db.Column(db.Text)
    resolved_at   = db.Column(db.DateTime)

    evidence_files = db.relationship(
                       'DefermentFile',
                       back_populates='request',
                       cascade='all, delete-orphan'
                     )
    student        = db.relationship('Student', back_populates='deferments')


class DefermentFile(db.Model):
    __tablename__  = 'deferment_file'
    id             = db.Column(db.Integer, primary_key=True)
    request_id     = db.Column(db.Integer, db.ForeignKey('deferment_request.id'), nullable=False)
    filename       = db.Column(db.String(200), nullable=False)  # stored filename
    original_name  = db.Column(db.String(200), nullable=False)  # original upload name

    request        = db.relationship('DefermentRequest', back_populates='evidence_files')

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action       = db.Column(db.String(50), nullable=False)  
    details      = db.Column(db.JSON, nullable=False)
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)

class SemesterReport(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('student.id'))
    semester_id  = db.Column(db.Integer, db.ForeignKey('semester.id'))
    mean_score   = db.Column(db.Float)
    letter_grade = db.Column(db.String(1))
    recommendation = db.Column(db.String(30))

    # THIS is the missing piece:
    semester = db.relationship('Semester', back_populates='reports')
    # (and if you want to navigate back: student = relationship('Student', back_populates='reports'))
