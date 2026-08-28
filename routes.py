# routes.py
import os
import requests
from datetime import datetime, date, timedelta
from flask import Blueprint, abort, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import DefermentFile, DefermentRequest, ReportSubmission, ReportingPeriod, Semester, SemesterReport, User, Student, Course, Enrollment, AcademicIssue, Mark, AuditLog, Faculty
from flask import current_app

# create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
student_bp = Blueprint('student', __name__)
admin_bp = Blueprint('admin', __name__)
admin_api_bp = Blueprint('admin_api', __name__)

# app/student/__init__.py

from flask import g

@main_bp.before_request
def load_current_student():
    if current_user.is_authenticated:
        # g.student is now available in any view
        g.student = Student.query.filter_by(user_id=current_user.id).first()
    else:
        g.student = None


@main_bp.route('/')
def index():
    # if you want to force login:
    # if current_user.is_authenticated:
    #     return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


# Authentication
# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.user_type == 'student':
            return redirect(url_for('main.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.user_type == 'student':
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

# @auth_bp.route('/register', methods=['GET', 'POST'])
# """
# The `register` function in a Flask application handles user registration, checking for existing
# users, creating a new user, and displaying appropriate messages.
# :return: The `register` function in the Flask route `/register` is returning different responses
# based on certain conditions:
# """
# def register():
#     if current_user.is_authenticated:
#         if current_user.user_type == 'student':
#             return redirect(url_for('main.dashboard'))
#         else:
#             return redirect(url_for('main.dashboard'))

#     if request.method == 'POST':
#         username = request.form['name']
#         email = request.form['email']
#         password = request.form['password']
#         user_type = request.form['user_type']
        
#         # Check if user already exists
#         existing_user = User.query.filter((User.name == username) | (User.email == email)).first()
#         if existing_user:
#             flash('Username or email already exists', 'error')
#             return render_template('register.html')
        
#         # Create new user
#         user = User(
#             name=username,
#             email=email,
#             user_type=user_type,
            
#         )
#         user.set_password(password)
        
#         db.session.add(user)
#         db.session.commit()
        
#         flash('Registration successful! Please log in.', 'success')
#         return redirect(url_for('auth.login'))

#     return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')    
@login_required
def dashboard():
    if current_user.user_type == 'admin':
        # you might load some admin stats here
        drequests = DefermentRequest.query.order_by(
        DefermentRequest.submitted_at.desc()
    ).all()

    # Pass them into the template
        return render_template('admin/dashboard.html', drequests=drequests)
        # return render_template('admin/dashboard.html')
    else:
        # or pass in whatever a student dashboard needs
        student = current_user.student
    if not student:
        flash('Please complete your profile first.', 'error')
        return redirect(url_for('student.profile'))

    # Total courses enrolled (past & present)
    total_courses = Course.query \
        .join(Enrollment) \
        .filter(Enrollment.student_id == student.id) \
        .count()

    # Active enrollments (expiry_date ≥ today)
    active_enrollments = Enrollment.query \
        .filter(
            Enrollment.student_id == student.id,
            Enrollment.expiry_date >= date.today()
        ) \
        .count()

    # Completed courses (expiry_date < today)
    completed_courses = total_courses - active_enrollments

    # Open academic issues (status ≠ 'resolved')
    open_issues = AcademicIssue.query \
        .filter(
            AcademicIssue.student_id == student.id,
            AcademicIssue.status != 'resolved'
        ) \
        .count()

    stats = {
        'total_courses': total_courses,
        'active_enrollments': active_enrollments,
        'completed_courses': completed_courses,
        'open_issues': open_issues
    }
    return render_template('student/dashboard.html', stats=stats)


@student_bp.before_app_request
def block_deferred_students():
    # Only run for logged-in student users
    if (
        current_user.is_authenticated
        and current_user.user_type == 'student'
        and current_user.student_profile  # make sure the relationship exists
        and current_user.student_profile.is_deferred
    ):
        # Allow them to see only the notice or to log out
        allowed = (
            'student.deferred_notice',
            'student.resume_studies',
            'static'
        )
        if request.endpoint not in allowed:
            return redirect(url_for('student.deferred_notice'))


#Student Profile
@student_bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    print("Current user:", current_user.id, current_user.user_type)

    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        dob_str = request.form.get('dob')
        address = request.form.get('address')
        qualifications = request.form.get('qualifications')

        errors = []

        # Basic validation
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Invalid date of birth; use YYYY-MM-DD.')
        
        # Check for duplicate email (if changed and not current user's email)
        existing_user_with_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user_with_email:
            errors.append('This email is already registered by another user.')

        if errors:
            for msg in errors:
                flash(msg, 'error')
            # Pass the submitted form data back to the template to pre-fill fields
            form_data = request.form
        else:
            # Update User table
            current_user.name = name
            current_user.email = email

            # Update Student table
            if student: # Ensure student profile exists
                student.dob = dob
                student.address = address
                student.qualifications = qualifications
            else:
                # This case should ideally not happen if a student user logs in
                # but good to have a fallback or error handling
                flash('Student profile not found. Please contact support.', 'error')
                db.session.rollback() # Rollback changes to user as well
                return redirect(url_for('main.dashboard')) # Redirect to prevent further issues

            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                # After successful update, you might want to redirect
                # or re-render the page with updated data.
                # If you re-render, pass the updated user/student data.
                # For simplicity, we'll fetch the updated data for form_data.
                form_data = {
                    'name': current_user.name,
                    'email': current_user.email,
                    'dob': student.dob.strftime('%Y-%m-%d') if student.dob else '',
                    'address': student.address,
                    'qualifications': student.qualifications
                }
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {e}', 'error')
                form_data = request.form # Keep submitted data in case of DB error
    else: # GET request
        if student:
            # Pre-populate form_data with current student and user info
            form_data = {
                'name': current_user.name,
                'email': current_user.email,
                'dob': student.dob.strftime('%Y-%m-%d') if student.dob else '',
                'address': student.address,
                'qualifications': student.qualifications
            }
        else:
            # If no student profile found (e.g., brand new student user, or data inconsistency)
            # You might want to create a blank form or show an error
            flash('Student profile not found. Please contact support to set up your profile.', 'error')
            form_data = {
                'name': current_user.name,
                'email': current_user.email,
                'dob': '',
                'address': '',
                'qualifications': ''
            }
    
    return render_template('student/profile.html', form_data=form_data)



# Import the NTLM authentication handler if using NTLM
# You MUST install this: pip install requests_ntlm
try:
    from requests_ntlm import HttpNtlmAuth
except ImportError:
    HttpNtlmAuth = None
    current_app.logger.warning("requests_ntlm not installed. NTLM authentication for Business Central will not work.")

# routes.py
import requests
from requests_ntlm import HttpNtlmAuth
from flask import current_app
# ... other imports (e.g., from datetime, etc.)

# --- Helper function to interact with BC API ---
def send_to_business_central(api_type, data):
    """
    Sends data to the specified Business Central ON-PREMISE API endpoint.
    Uses configuration from Flask's current_app.config.
    api_type: 'user' or 'student'
    data: Dictionary of data to send
    """
    config = current_app.config

    # **CORRECTION**: Get authentication details from the config
    bc_user = config['BC_USER']
    bc_pass = config['BC_PASS']
    bc_use_ntlm = config['BC_USE_NTLM']

    # Determine the correct API service name based on API type
    if api_type == 'user':
        service_name = config['BC_USER_API_SERVICE_NAME']
    elif api_type == 'student':
        service_name = config['BC_STUDENT_API_SERVICE_NAME']
    else:
        raise ValueError("Invalid API type. Must be 'user' or 'student'.")

    # Construct the correct ON-PREMISE OData V4 API URL
    # Example: http://donson:7048/BC200/ODataV4/Company('Donson')/StudentAPI
   # In your Flask code, where you build the URL
    # The 'service_name' should be 'personApi' or 'studentApi'
    base_url_components = [
        f"http://{config['BC_SERVER_NAME']}:{config['BC_ODATA_PORT']}",
        "BC200",  # You might need to make this dynamic if the instance name changes
        "ODataV4",
        f"Company('{config['BC_COMPANY_NAME_ENCODED']}')",
        service_name
    ]

    # The url will now be correctly built
    url = "/".join(base_url_components)
    current_app.logger.debug(f"BC POST URL -> {url}")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Important: For NTLM, typically you don't send Authorization header directly.
        # requests_ntlm handles it.
    }

    auth_handler = None
    if bc_use_ntlm and HttpNtlmAuth:
        auth_handler = HttpNtlmAuth(bc_user, bc_pass)
        current_app.logger.info(f"Attempting NTLM auth for {api_type} to {url}")
    else:
        # Fallback to basic auth if NTLM is not used or requests_ntlm not installed
        # This will likely fail if BC is configured for NTLM only.
        auth_handler = (bc_user, bc_pass)
        current_app.logger.info(f"Attempting Basic auth for {api_type} to {url}")
        current_app.logger.debug(f"BC POST URL → {url}")

    try:
        response = requests.post(url, json=data, headers=headers, auth=auth_handler, verify=config['BC_VERIFY_TLS'])
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        bc_response_data = response.json()
        current_app.logger.info(f"Successfully sent {api_type} data to BC. Response: {bc_response_data}")
        return bc_response_data
    except requests.exceptions.JSONDecodeError as json_err:
        current_app.logger.error(f"Failed to decode JSON from BC response: {json_err}")
        current_app.logger.error(f"Raw Response Content: '{response.text}'")
        raise # Re-raise the JSON error    
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"HTTP Error sending {api_type} data to BC: {e}")
        current_app.logger.error(f"URL: {url}")
        current_app.logger.error(f"Request data: {data}")
        current_app.logger.error(f"Response status code: {e.response.status_code}")
        current_app.logger.error(f"Response content: {e.response.text}")
        raise # Re-raise the exception to be caught in add_student
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Network or other error sending {api_type} data to BC: {e}")
        current_app.logger.error(f"URL: {url}")
        current_app.logger.error(f"Request data: {data}")
        raise # Re-raise the exception
# --- Modified add_student logic ---
@admin_bp.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    # 1) Only admins may add students
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    # 2) Load courses for the multi-select dropdown
    courses = Course.query.order_by(Course.title).all()

    form_data = {}
    selected_course_ids = []

    if request.method == 'POST':
        # 3) Pull data from the form
        reg_no = request.form.get('reg_no', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm', '')
        dob_str = request.form.get('dob', '').strip()
        address = request.form.get('address', '').strip()
        qualifications = request.form.get('qualifications', '').strip()
        selected_ids = request.form.getlist('courses')

        form_data = request.form.to_dict()
        form_data['dob'] = dob_str
        form_data['courses'] = selected_ids
        selected_course_ids = selected_ids

        # 4) Validate required fields
        errors = []
        if not reg_no:
            errors.append('Registration number is required.')
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        dob = None
        try:
            if dob_str:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            else:
                errors.append('Date of Birth is required.')
        except ValueError:
            errors.append('Invalid date of birth; use YYYY-MM-DD.')

        if User.query.filter((User.name == name) | (User.email == email)).first():
            errors.append('A user with that name or email already exists locally.')

        if errors:
            for msg in errors:
                flash(msg, 'error')
        else:
            try:
                # Flask DB Transaction (Local Data)
                # 5) Create the User in Flask DB
                user = User(name=name, email=email, user_type='student')
                user.set_password(password)
                db.session.add(user)
                db.session.flush() # give us user.id without committing

                # --- Corrected bc_user_data dictionary ---
              # This is the payload to send to the Business Central `people` API endpoint
                bc_user_data = {
                    # Do NOT include the personId. Business Central will create it.
                    "name": name,
                    "email": email,
                    "userType": "Student"
                }
                current_app.logger.info("Sending User data to Business Central...")
                bc_user_response = send_to_business_central('user', bc_user_data)
                bc_person_id = bc_user_response.get('id')  # This is BC's SystemId (GUID)
                # IMPORTANT: If BC's `usser` table's `ID` field is auto-generated and
                # you need to link by that BC-generated ID, store it here.
                # Example:
                # user.bc_user_id = bc_user_response.get('id') # Requires `bc_user_id` column in Flask User model
                # db.session.add(user) # Add user again to save the BC ID

                # 6) Create the Student profile in Flask DB
                student = Student(
                    user_id=user.id, # Local Flask user ID
                    reg_no=reg_no,
                    name=name,
                    dob=dob,
                    address=address,
                    qualifications=qualifications
                )
                db.session.add(student)
                db.session.flush() # get student.id for local enrollments if needed

               # routes.py
                    # --- Corrected bc_student_data dictionary ---
                bc_student_data = {
                    "studentId": reg_no,  # or another unique student code
                    "personId": bc_person_id,  # BC GUID, not Flask integer,
                    "registrationNo": reg_no,
                    "dateOfBirth": dob.isoformat(),
                    "address": address,
                    "qualifications": qualifications,
                    "isDeferred": False
                }
                current_app.logger.info("Sending Student data to Business Central...")
                bc_student_response = send_to_business_central('student', bc_student_data)
                # 7) Enroll in selected courses locally
                if selected_ids:
                    selected_courses = Course.query.filter(
                        Course.id.in_(selected_ids)
                    ).all()
                    student.courses.extend(selected_courses)

                # Final commit for all local DB changes (including potential bc_user_id update)
                db.session.commit()

                flash('Student added successfully and synchronized with Business Central.', 'success')
                return redirect(url_for('main.dashboard'))

            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while adding the student locally or to Business Central: {e}', 'error')
                current_app.logger.exception("Error during student creation/sync") # Log the full traceback

    else:
        pass

    return render_template(
        'admin/add_student.html',
        form_data=form_data,
        courses=courses,
        selected_course_ids=selected_course_ids
    )



# app/admin/routes.py
@admin_bp.route('/admin/manage-faculty', methods=['GET', 'POST'])
@login_required
def manage_faculty():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    errors = {}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            errors['name'] = 'Faculty name is required.'
        elif Faculty.query.filter_by(name=name).first():
            errors['name'] = 'That faculty already exists.'

        if not errors:
            fac = Faculty(name=name)
            db.session.add(fac)
            db.session.commit()
            flash('Faculty added.', 'success')
            return redirect(url_for('admin.manage_faculty'))

    faculties = Faculty.query.order_by(Faculty.name).all()
    return render_template(
        'admin/manage_faculty.html',
        faculties=faculties,
        errors=errors
    )

# we will manage faculties via this provided UI
@admin_bp.route('/admin/edit-faculty/<int:fac_id>', methods=['GET', 'POST'])
@login_required
def edit_faculty(fac_id):
    fac = Faculty.query.get_or_404(fac_id)
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    errors = {}
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        if not new_name:
            errors['name'] = 'Faculty name is required.'
        elif Faculty.query.filter(Faculty.id!=fac_id, Faculty.name==new_name).first():
            errors['name'] = 'Another faculty has that name.'

        if not errors:
            fac.name = new_name
            db.session.commit()
            flash('Faculty updated.', 'success')
            return redirect(url_for('admin.manage_faculty'))

    return render_template(
        'admin/edit_faculty.html',
        faculty=fac,
        errors=errors
    )


@admin_bp.route('/admin/manage-course', methods=['GET', 'POST'])
@login_required
def manage_course():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    faculties = Faculty.query.all()
    errors = {}

    if request.method == 'POST':
        # get & validate
        title       = request.form.get('title', '').strip()
        start_date  = request.form.get('start_date', '').strip()
        end_date    = request.form.get('end_date', '').strip()
        fac_id      = request.form.get('faculty_id', type=int)

        # title
        if not title:
            errors['title'] = 'Title is required.'

        # faculty
        if not fac_id:
            errors['faculty_id'] = 'Please select a faculty.'
        else:
            faculty = Faculty.query.get(fac_id)
            if not faculty:
                errors['faculty_id'] = 'Invalid faculty selected.'

        # dates
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            errors['start_date'] = 'Invalid start date (YYYY-MM-DD).'
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            errors['end_date'] = 'Invalid end date (YYYY-MM-DD).'

        # if valid, persist
        if not errors:
            course = Course(
                title=title,
                start_date=sd,
                end_date=ed,
                faculty_id=fac_id
            )
            db.session.add(course)
            db.session.commit()
            flash('Course created successfully.', 'success')
            return redirect(url_for('admin.manage_course'))

    # GET or validation errors
    courses = Course.query.all()
    selected_faculty_id = request.form.get('faculty_id', type=int)
    return render_template(
        'admin/manage_course.html',
        courses=courses,
        faculties=faculties,
        errors=errors,
        selected_faculty_id=selected_faculty_id
    )

# routes.py

@admin_bp.route('/admin/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    # Security: only admins
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))

    course = Course.query.get_or_404(course_id)
    errors = {}

    if request.method == 'POST':
        title      = request.form.get('title', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date   = request.form.get('end_date', '').strip()

        # Validation
        if not title:
            errors['title'] = 'Title is required.'
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            errors['start_date'] = 'Invalid start date (YYYY-MM-DD).'
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            errors['end_date'] = 'Invalid end date (YYYY-MM-DD).'

        # On success, update and redirect
        if not errors:
            course.title      = title
            course.start_date = sd
            course.end_date   = ed
            db.session.commit()
            flash('Course updated successfully.', 'success')
            return redirect(url_for('admin.manage_course'))

    # GET or invalid POST: render form with course data + errors
    return render_template(
        'admin/edit_course.html',
        course=course,
        errors=errors
    )

def acad_year_and_bracket(start_date):
    # Accept either date or datetime objects
    if isinstance(start_date, datetime):
        start_date = start_date.date()

    m, y = start_date.month, start_date.year

    if 8 <= m <= 12:
        bracket = 'Sem1'
        ay = f"{y}-{y+1}"
    elif 1 <= m <= 4:
        bracket = 'Sem2'
        ay = f"{y-1}-{y}"
    else:
        bracket = 'Holiday'
        ay = f"{y-1}-{y}"

    return ay, bracket


@admin_bp.route("/admin/semesters", methods=["GET", "POST"])
def manage_semesters():
    if request.method == "POST":
        start_str  = request.form.get("start_date", "")
        end_str    = request.form.get("end_date", "")

        if not (start_str and end_str):
            flash("Start and end dates are required", "error")
            return redirect(url_for("admin.manage_semesters"))

        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date   = datetime.strptime(end_str,   "%Y-%m-%d")
        except ValueError:
            flash("Dates must be in YYYY-MM-DD format", "error")
            return redirect(url_for("admin.manage_semesters"))

        if start_date >= end_date:
            flash("Start date must come before end date", "error")
            return redirect(url_for("admin.manage_semesters"))

        # Derive academic year & bracket, build the canonical name
        ay, bracket = acad_year_and_bracket(start_date)
        name = f"{bracket} {ay}"

        # Prevent exact duplicates
        if Semester.query.filter_by(name=name).first():
            flash(f"{name} already exists", "error")
            return redirect(url_for("admin.manage_semesters"))

        sem = Semester(name=name,
                       start_date=start_date.date(),
                       end_date=end_date.date())
        db.session.add(sem)
        db.session.commit()

        flash(f"Added {name}", "success")
        return redirect(url_for("admin.manage_semesters"))

    semesters = Semester.query.order_by(Semester.start_date).all()
    return render_template("admin/manage_semesters.html", semesters=semesters)

@admin_bp.route('/admin/reports', methods=['GET'])
@login_required
def reports():
    if current_user.user_type != 'admin':
        return redirect(url_for('main.dashboard'))

    # ——— Filters ———
    course_name = request.args.get('course_name', type=str)
    start_date  = request.args.get('start_date',  type=str)
    end_date    = request.args.get('end_date',    type=str)
    status      = request.args.get('status',      type=str)     # 'active'/'inactive'
    expiry_days = request.args.get('expiry_days', type=int)

    issue_type   = request.args.get('issue_type',   type=str)
    issue_status = request.args.get('issue_status', type=str)
    issue_start  = request.args.get('issue_start',  type=str)
    issue_end    = request.args.get('issue_end',    type=str)

    today = date.today()

    # ——— 1. Active Enrollment Report ———
    q1 = Enrollment.query.join(Student).join(Course)

    if course_name:
        q1 = q1.filter(Course.title == course_name)
    if start_date:
        q1 = q1.filter(Enrollment.enroll_date >= date.fromisoformat(start_date))
    if end_date:
        q1 = q1.filter(Enrollment.enroll_date <= date.fromisoformat(end_date))
    if status in ('active', 'inactive'):
        if status == 'active':
            q1 = q1.filter(Enrollment.expiry_date >= today)
        else:
            q1 = q1.filter(Enrollment.expiry_date < today)

    # Order active enrollments by soonest expiry first
    active_enrollments = q1.order_by(Enrollment.expiry_date.asc()).all()

    # ——— 2. Course Expiry Notification ———
    q2 = Enrollment.query.join(Student).join(Course)

    if expiry_days is not None:
        window_end = today + timedelta(days=expiry_days)
        q2 = q2.filter(
            Enrollment.expiry_date >= today,
            Enrollment.expiry_date <= window_end
        )

    expiry_notifications = q2.order_by(Enrollment.expiry_date.asc()).all()

    # ——— 3. Academic Issues ———
    q3 = AcademicIssue.query.join(Student)

    if issue_type:
        q3 = q3.filter(AcademicIssue.issue_type == issue_type)
    if issue_status:
        q3 = q3.filter(AcademicIssue.status == issue_status)
    if issue_start:
        q3 = q3.filter(AcademicIssue.reported_date >= date.fromisoformat(issue_start))
    if issue_end:
        q3 = q3.filter(AcademicIssue.reported_date <= date.fromisoformat(issue_end))

    # Order issues by most recent reports first
    issues = q3.order_by(AcademicIssue.reported_date.desc()).all()

    return render_template(
        'admin/reports.html',
        courses             = [c.title for c in Course.query.distinct(Course.title)],
        issue_types         = [i.issue_type for i in AcademicIssue.query.distinct(AcademicIssue.issue_type)],
        active_enrollments   = active_enrollments,
        expiry_notifications = expiry_notifications,
        issues               = issues,
        filters              = request.args,
        today                = today
    )

@admin_bp.route('/api/dashboard_metrics', methods=['GET'])
@login_required
def dashboard_metrics():
    if current_user.user_type != 'admin':
        # You might want to return a 403 Forbidden or a more specific error
        return jsonify({"error": "Unauthorized access"}), 403

    today = date.today()

    # Calculate Total Active Enrollments
    total_active_enrollments = Enrollment.query.filter(Enrollment.expiry_date >= today).count()

    # Calculate Courses Expiring Soon (e.g., in the next 30 days)
    # You can adjust the timedelta as needed
    future_date = today + timedelta(days=30)
    courses_expiring_soon = Enrollment.query.filter(
        Enrollment.expiry_date >= today,
        Enrollment.expiry_date <= future_date
    ).count()

    # Calculate Open Academic Issues
    open_academic_issues = AcademicIssue.query.filter_by(status='open').count()

    # Calculate Total Students
    total_students = Student.query.count()

    return jsonify({
        'total_active_enrollments': total_active_enrollments,
        'courses_expiring_soon': courses_expiring_soon,
        'open_academic_issues': open_academic_issues,
        'total_students': total_students
    })

# ... (rest of your route.py file)
# routes.py (or wherever your blueprint/views live)
# List all periods
@admin_bp.route('/report_periods')
@login_required
def list_periods():
    periods = ReportingPeriod.query.order_by(ReportingPeriod.start_date.desc()).all()
    return render_template('admin/report_periods.html', periods=periods)

# Create or edit a period
@admin_bp.route('/report_periods/<int:pid>/edit', methods=['GET','POST'])
@admin_bp.route('/report_periods/add', methods=['GET','POST'])
@login_required
def edit_period(pid=None):
    if current_user.user_type != 'admin':
        abort(403)
    period = ReportingPeriod.query.get(pid) if pid else ReportingPeriod()
    if request.method == 'POST':
        period.name       = request.form['name']
        period.start_date = datetime.strptime(request.form['start_date'],'%Y-%m-%d').date()
        period.end_date   = datetime.strptime(request.form['end_date'],  '%Y-%m-%d').date()
        period.active     = 'active' in request.form
        db.session.add(period)
        db.session.commit()
        flash('Reporting period saved.', 'success')
        return redirect(url_for('admin.list_periods'))
    return render_template('admin/edit_period.html', period=period)

# View submissions for a period
@admin_bp.route('/submissions/<int:pid>')
@login_required
def view_submissions(pid):
    if current_user.user_type != 'admin':
        abort(403)
    period = ReportingPeriod.query.get_or_404(pid)
    submissions = ReportSubmission.query\
                      .filter_by(period_id=pid)\
                      .order_by(ReportSubmission.submitted_at.desc())\
                      .all()
    return render_template('admin/view_submissions.html',
                           period=period,
                           submissions=submissions)

@student_bp.route('/report', methods=['GET','POST'])
@login_required
def submit_report():
    if current_user.user_type != 'student':
        abort(403)

    # Find the active period
    today  = date.today()
    period = ReportingPeriod.query.filter(
                 ReportingPeriod.active==True,
                 ReportingPeriod.start_date <= today,
                 ReportingPeriod.end_date   >= today
             ).first()

    if not period:
        flash('No active reporting period at this time.', 'info')
        return render_template('student/no_period.html')

    # Check existing submission
    student = current_user.student_profile
    submission = ReportSubmission.query.filter_by(
                     student_id=student.id,
                     period_id=period.id
                 ).first()

    if request.method == 'POST':
        content = request.form.get('content','').strip()
        if not content:
            flash('Report content cannot be empty.', 'error')
        else:
            if submission:
                submission.content = content
                flash('Report updated successfully.', 'success')
            else:
                submission = ReportSubmission(
                    student_id=student.id,
                    period_id=period.id,
                    content=content
                )
                db.session.add(submission)
                flash('Report submitted successfully.', 'success')
            db.session.commit()
            return redirect(url_for('student.submit_report'))

    # Pre-fill textarea if updating
    form_content = submission.content if submission else ''
    return render_template('student/report_form.html',
                           period=period,
                           content=form_content)

# deferment logic goes here
@student_bp.route('/defer', methods=['GET','POST'])
@login_required
def defer_request():
    
    if current_user.user_type != 'student':
        abort(403)

    student = Student.query.filter_by(user_id=current_user.id).first()
    recent  = DefermentRequest.query\
                .filter_by(student_id=student.id)\
                .order_by(DefermentRequest.submitted_at.desc())\
                .first()

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        notes  = request.form.get('notes', '').strip()
        files  = request.files.getlist('evidence')

        errors = []
        if reason not in ('medical','financial','personal'):
            errors.append('Please select a valid deferment reason.')
        if not files or all(f.filename == '' for f in files):
            errors.append('Please upload at least one evidence file.')

        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            dr = DefermentRequest(
                student_id    = student.id,
                reason        = reason,
                student_notes = notes
            )
            db.session.add(dr)
            db.session.flush()  # get dr.id
            
            # save files…
            for f in files:
                if f and f.filename:
                    fname     = secure_filename(f.filename)
                    save_path = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        'deferment', str(dr.id)
                    )
                    os.makedirs(save_path, exist_ok=True)
                    f.save(os.path.join(save_path, fname))

                    df = DefermentFile(
                        request_id   = dr.id,
                        filename     = fname,
                        original_name= f.filename
                    )
                    db.session.add(df)

            db.session.commit()
            flash('Your deferment request has been submitted.', 'success')
            # TODO: notify admins
            return redirect(url_for('student.defer_request'))

    return render_template(
        'student/defer_form.html',
        request=recent
    )

# app/student/routes.py
@student_bp.route('/deferred-notice')
@login_required
def deferred_notice():
    return render_template('student/deferred_notice.html')

@student_bp.route('/resume', methods=['POST', 'GET'])
@login_required
def resume_studies():
    # Confirm only deferred students get here
    if current_user.user_type != 'student' \
       or not current_user.student.is_deferred:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        current_user.student.is_deferred = False
        db.session.commit()
        flash('Welcome back! Your student access has been restored.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('student/resume_studies.html')


@admin_bp.route('/deferments/<int:rid>', methods=['GET','POST'])
@login_required
def review_deferment(rid):
    if current_user.user_type != 'admin':
        abort(403)
    dr = DefermentRequest.query.get_or_404(rid)

    if request.method == 'POST':
        decision = request.form['decision']           # 'approved' or 'declined'
        dr.status      = decision
        dr.admin_notes = request.form.get('admin_notes','').strip()
        dr.resolved_at = datetime.utcnow()

        # NEW: if approved, pause the student
        if decision == 'approved':
            dr.student.is_deferred = True
        # Optionally: if declined, ensure they remain active:
        elif decision == 'declined':
            dr.student.is_deferred = False

        db.session.commit()
        flash('Deferment request updated.', 'success')
        return redirect(url_for('admin.defer_list'))

    return render_template('admin/defer_review.html', dr=dr)

@admin_bp.route(
        '/deferments',
        endpoint='defer_list'
        )
@login_required
def list_deferments():
    if current_user.user_type != 'admin':
        abort(403)
    drequests = DefermentRequest.query\
        .order_by(DefermentRequest.submitted_at.desc())\
        .all()
    return render_template('admin/defer_list.html', drequests=drequests)

# Grade calculation logic goes here
def calculate_mean(scores):
    return sum(scores) / len(scores) if scores else 0

def letter_grade(mean):
    if mean >= 70: return 'A'
    if mean >= 60: return 'B'
    if mean >= 50: return 'C'
    if mean >= 40: return 'D'
    return 'E'

def recommendation_for_grade(grade):
    return 'Supplementary Eligible' if grade == 'E' else 'Pass'


@admin_bp.route('/upload_marks', methods=['GET','POST'])
@login_required
def upload_marks():
    semesters = Semester.query.order_by(Semester.start_date.desc()).all()
    courses   = Course.query.all()
    students  = Student.query.all()

    if request.method == 'POST':
        entries = []
        # 1. Save each Mark
        for idx in range(len(request.form.getlist('student_id'))):
            entry = {
                'student_id':   int(request.form['student_id'][idx]),
                'course_id':    int(request.form['course_id'][idx]),
                'semester_id':  int(request.form['semester_id'][idx]),
                'score':        float(request.form['score'][idx])
            }
            entries.append(entry)
            db.session.add(Mark(**entry))

        # Commit all raw marks first
        db.session.commit()

        # 2. Compute & persistence of SemesterReport for each student
        #    (This is the code you asked where to place.)
        #    We assume all entries share the same semester; pick one:
        selected_semester_id = entries[0]['semester_id']
        selected_students    = {e['student_id'] for e in entries}

        for student_id in selected_students:
            # gather that student’s scores for the semester
            scores = [
                m.score
                for m in Mark.query
                            .filter_by(student_id=student_id,
                                       semester_id=selected_semester_id)
                            .all()
            ]

            mean  = calculate_mean(scores)
            grade = letter_grade(mean)
            rec   = recommendation_for_grade(grade)

            # upsert the report
            rpt = SemesterReport.query.filter_by(
                      student_id=student_id,
                      semester_id=selected_semester_id
                  ).first() or SemesterReport(
                      student_id=student_id,
                      semester_id=selected_semester_id
                  )

            rpt.mean_score     = mean
            rpt.letter_grade   = grade
            rpt.recommendation = rec
            db.session.add(rpt)

        # Commit all SemesterReport changes
        db.session.commit()

        # 3. Audit log the entire batch
        db.session.add(AuditLog(
            user_id=current_user.id,
            action='upload_marks',
            details={'entries': entries}
        ))
        db.session.commit()

        flash('Marks uploaded, reports calculated, and logged.', 'success')
        return redirect(url_for('admin.upload_marks'))

    # GET: render the form
    return render_template(
        'admin/upload_marks.html',
        semesters=semesters,
        courses=courses,
        students=students
    )

@student_bp.route('/my_results')
@login_required
def my_results():
    student_id = current_user.student.id
    reports = SemesterReport.query\
        .filter_by(student_id=student_id)\
        .order_by(SemesterReport.semester_id.desc())\
        .all()
    return render_template('student/my_results.html', reports=reports)

@student_bp.route('/apply_supplementary/<int:report_id>', methods=['POST'])
@login_required
def apply_supplementary(report_id):
    rpt = SemesterReport.query.get_or_404(report_id)
    if rpt.student_id != current_user.student.id or rpt.letter_grade != 'E':
        abort(403)
    rpt.applied_supplementary = True
    db.session.commit()
    flash('Supplementary application submitted.', 'success')
    return redirect(url_for('student.my_results'))

@admin_bp.route('/audit_logs')
@login_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('admin/audit_logs.html', logs=logs)
