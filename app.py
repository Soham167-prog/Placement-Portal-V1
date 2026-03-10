from flask import Flask, render_template, request, redirect, session, url_for
from database import initialize_database, get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"
RESUMES_FOLDER = os.path.join("static", "resumes")
app.config["UPLOAD_FOLDER"] = RESUMES_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return filename and filename.lower().endswith(".pdf")

def save_resume(file, prefix=""):
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    base = secure_filename(file.filename) or "resume"
    if not base.lower().endswith(".pdf"):
        base = base + ".pdf"
    name = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{base}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], name)
    file.save(path)
    return path

initialize_database()

#Home page
@app.route('/')
def home():
    return render_template("home.html")

#Student register
@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '')
        is_active = 1
        created_at = datetime.now()
        resume_path = None
        if 'resume' in request.files:
            f = request.files['resume']
            if f.filename:
                if not allowed_file(f.filename):
                    return "Only PDF files are allowed for resume."
                resume_path = save_resume(f, prefix=email.replace("@", "_").replace(".", "_"))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return "Email already exists"

        hashed_password = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO student
            (name, email, password, phone, resume_path, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, hashed_password, phone, resume_path, is_active, created_at))
        conn.commit()
        conn.close()
        return redirect('/student/login')

    return render_template("student/register.html")

#Student login
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student WHERE email = ? AND is_active = 1", (email,))
        student = cursor.fetchone()
        conn.close()
        if student and check_password_hash(student['password'], password):
            session.clear()
            session['user_id'] = student['id']
            session['role'] = 'student'
            session['username'] = student['name']
            return redirect('/student/dashboard')
        # Debug on failed login
        print("[Student login] email entered:", repr(email))
        print("[Student login] user found:", student is not None)
        if student:
            print("[Student login] password check:", check_password_hash(student['password'], password))
        return "Invalid Student Credentials"
    return render_template("student/login.html")

#Company register
@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hr_contact = request.form['hr_contact']
        website = request.form['website']
        approval_status = "Pending"
        is_active = 1
        created_at = datetime.now()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM company WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return "Email already exists"

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO company
            (name, email, password, hr_contact, website,
             approval_status, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, hashed_password,
              hr_contact, website,
              approval_status, is_active, created_at))

        conn.commit()
        conn.close()

        return "Registered Successfully. Wait for Admin Approval."

    return render_template("company/register.html")

#Company login
@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM company 
            WHERE name = ? AND is_active = 1 AND approval_status = 'Approved'
        """, (name,))
        company = cursor.fetchone()
        conn.close()

        if company and check_password_hash(company['password'], password):
            session.clear()
            session['user_id'] = company['id']
            session['company_id'] = company['id']
            session['role'] = 'company'
            session['username'] = company['name']
            return redirect('/company/dashboard')

        return "Invalid Company Credentials or Not Approved"

    return render_template("company/login.html")

#Admin login
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admin WHERE username = ?", (name,))
        admin = cursor.fetchone()
        conn.close()

        # Since DB stores plain password, compare directly
        if admin and admin['password'] == password:
            session.clear()
            session['user_id'] = admin['id']
            session['role'] = 'admin'
            session['username'] = admin['username']
            session['admin'] = True 
            return redirect('/admin/dashboard')

        return "Invalid Admin Credentials"

    return render_template("admin/login.html")

#Admin granting permissions to the company
@app.route('/admin/companies')
def view_companies():
    if session.get('role') != 'admin':
        return redirect('/')

    search = request.args.get('search')

    conn = get_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM company
            WHERE name LIKE ?
        """, (f'%{search}%',))
    else:
        cursor.execute("SELECT * FROM company")

    companies = cursor.fetchall()
    conn.close()

    return render_template("admin/companies.html", companies=companies)

@app.route('/admin/approve/<int:company_id>', methods=['POST'])
def approve_company(company_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE company
        SET approval_status = 'Approved'
        WHERE id = ?
    """, (company_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/companies')

@app.route('/admin/reject/<int:company_id>', methods=['POST'])
def reject_company(company_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE company
        SET approval_status = 'Rejected'
        WHERE id = ?
    """, (company_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/companies')

#Blacklisting companies and students
@app.route('/admin/blacklist/company/<int:company_id>', methods=['POST'])
def blacklist_company(company_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE company
        SET is_active = 0
        WHERE id = ?
    """, (company_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/companies')

@app.route('/admin/blacklist/student/<int:student_id>', methods=['POST'])
def blacklist_student(student_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE student
        SET is_active = 0
        WHERE id = ?
    """, (student_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/students')

#Aproving or rejecting placement drive by admin
@app.route('/admin/drives')
def manage_drives():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT placement_drive.*, company.name as company_name
        FROM placement_drive
        JOIN company ON placement_drive.company_id = company.id
    """)

    drives = cursor.fetchall()
    conn.close()

    return render_template("admin/drives.html", drives=drives)

@app.route('/admin/approve-drive/<int:drive_id>', methods=['POST'])
def approve_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE placement_drive
        SET status = 'Approved'
        WHERE id = ?
    """, (drive_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/drives')

@app.route('/admin/reject-drive/<int:drive_id>', methods=['POST'])
def reject_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE placement_drive
        SET status = 'Closed'
        WHERE id = ?
    """, (drive_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/drives')

#Managing students
@app.route('/admin/students')
def manage_students():
    if session.get('role') != 'admin':
        return redirect('/')

    search = request.args.get('search')

    conn = get_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM student
            WHERE name LIKE ?
               OR phone LIKE ?
               OR id LIKE ?
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM student")

    students = cursor.fetchall()
    conn.close()

    return render_template("admin/students.html", students=students)

#Managing job applications
@app.route('/admin/applications')
def manage_applications():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            s.name AS student_name,
            c.name AS company_name,
            pd.job_title,
            a.status,
            a.application_date
        FROM application a
        JOIN student s ON a.student_id = s.id
        JOIN placement_drive pd ON a.drive_id = pd.id
        JOIN company c ON pd.company_id = c.id
        ORDER BY a.application_date DESC
    """)
    applications = cursor.fetchall()
    conn.close()

    return render_template("admin/applications.html", applications=applications)
#Dashboards
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/student/login')
    search = request.args.get('search', '').strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pd.id, pd.job_title, pd.job_description, pd.eligibility, pd.deadline, pd.status, c.name as company_name
        FROM placement_drive pd
        JOIN company c ON pd.company_id = c.id
        WHERE pd.status IN ('Approved', 'Active')
    """)
    drives = cursor.fetchall()
    cursor.execute("SELECT drive_id FROM application WHERE student_id = ?", (session['user_id'],))
    applied_ids = {row['drive_id'] for row in cursor.fetchall()}
    conn.close()
    if search:
        drives = [d for d in drives if (search.lower() in (d['company_name'] or '').lower() or search.lower() in (d['job_title'] or '').lower() or search.lower() in (d['eligibility'] or '').lower())]
    return render_template("student/dashboard.html", drives=drives, search=search, applied_ids=applied_ids)


@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        return redirect('/')
    company_id = session.get('company_id')
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM placement_drive WHERE company_id=?", (company_id,))
    jobs = cursor.fetchall()

    cursor.execute("""
       SELECT COUNT(*) FROM application a 
       JOIN placement_drive pd ON a.drive_id = pd.id
       WHERE pd.company_id=?
    """, (company_id,))
    total_applications = cursor.fetchone()[0]

    conn.close()
    return render_template("company/dashboard.html", jobs=jobs, total_applications=total_applications)


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    # Students
    cursor.execute("SELECT COUNT(*) FROM student WHERE is_active = 1")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM student WHERE is_active = 0")
    blacklisted_students = cursor.fetchone()[0]

    # Companies
    cursor.execute("SELECT COUNT(*) FROM company WHERE is_active = 1")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM company WHERE is_active = 0")
    blacklisted_companies = cursor.fetchone()[0]

    # Drives
    cursor.execute("SELECT COUNT(*) FROM placement_drive")
    total_drives = cursor.fetchone()[0]

    # Applications
    cursor.execute("SELECT COUNT(*) FROM application")
    total_applications = cursor.fetchone()[0]

    # Placed students (from job_position)
    cursor.execute("SELECT COUNT(*) FROM job_position")
    placed_students = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        blacklisted_students=blacklisted_students,
        total_companies=total_companies,
        blacklisted_companies=blacklisted_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        placed_students=placed_students
    )

#Conpany Functions
#Posting of new job positions
@app.route('/company/post-job', methods=['GET','POST'])
def post_job():
    if session.get('role') != 'company':
        return redirect('/')

    if request.method == 'POST':
        job_title = request.form['job_title']
        job_description = request.form['job_description']
        eligibility = request.form['eligibility']
        deadline = request.form['deadline']

        conn = get_connection()
        cursor = conn.cursor()

        # Prevent duplicate active/approved drives for same role
        cursor.execute("""
            SELECT id FROM placement_drive
            WHERE company_id = ?
              AND job_title = ?
              AND status IN ('Approved', 'Active')
        """, (session['user_id'], job_title))
        if cursor.fetchone():
            conn.close()
            return "An active placement drive for this role already exists. Please close the current drive before creating another."

        cursor.execute("""
            INSERT INTO placement_drive
            (company_id, job_title, job_description, eligibility, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'Pending Approval', datetime('now'))
        """, (session['user_id'], job_title, job_description, eligibility, deadline))

        conn.commit()
        conn.close()

        return redirect('/company/dashboard')

    return render_template("company/post_job.html")

#Change Job Status
@app.route('/company/update-job-status/<int:job_id>/<status>')
def update_job_status(job_id, status):
    if session.get('role') != 'company':
        return redirect('/')
    if status != 'Closed':
        return redirect('/company/dashboard')
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE placement_drive
        SET status=?
        WHERE id=? AND company_id=?
    """, (status, job_id, session['user_id']))
    
    conn.commit()
    conn.close()

    return redirect('/company/dashboard')

@app.route('/company/applicants')
def company_applicants_index():
    if session.get('role') != 'company':
        return redirect('/')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM placement_drive
        WHERE company_id = ?
        ORDER BY created_at DESC
    """, (session['user_id'],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "No placement drives found. Post a drive first from your dashboard."
    return redirect(f"/company/applicants/{row['id']}")


#View applications for company jobs
@app.route('/company/applicants/<int:drive_id>')
@app.route('/company/applications/<int:drive_id>')
def company_applications(drive_id):

    if session.get('role') != 'company':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            a.id,
            s.name,
            s.email,
            s.resume_path,
            a.application_date,
            a.status,
            s.id AS student_id
        FROM application a
        JOIN student s ON a.student_id = s.id
        WHERE a.drive_id = ?
    """, (drive_id,))

    applications = cursor.fetchall()
    conn.close()

    return render_template("company/applicants.html", applications=applications, drive_id=drive_id)

#Update Application Status
@app.route('/company/update-application/<int:app_id>/<status>')
def update_application_status(app_id, status):
    if session.get('role') != 'company':
        return redirect('/')

    if status == 'Selected':
        return redirect(url_for('company_offer', app_id=app_id))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE application
        SET status=?
        WHERE id=?
    """, (status, app_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)

#Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# --- Student: apply, applied jobs, upload resume ---
@app.route('/student/apply/<int:drive_id>', methods=['POST'])
def student_apply(drive_id):
    if session.get('role') != 'student':
        return redirect('/student/login')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM placement_drive WHERE id = ? AND status IN ('Approved', 'Active')", (drive_id,))
    if not cursor.fetchone():
        conn.close()
        return "Drive not found or not approved.", 404
    try:
        cursor.execute("""
            INSERT INTO application (student_id, drive_id, application_date, status)
            VALUES (?, ?, ?, 'Applied')
        """, (session['user_id'], drive_id, datetime.now().isoformat()))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return redirect(url_for('student_dashboard') + "?msg=already_applied")
    conn.close()
    return redirect('/student/dashboard')

@app.route('/student/applied-jobs')
def student_applied_jobs():
    if session.get('role') != 'student':
        return redirect('/student/login')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.application_date, a.status, pd.job_title, pd.id as drive_id, c.name as company_name
        FROM application a
        JOIN placement_drive pd ON a.drive_id = pd.id
        JOIN company c ON pd.company_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.application_date DESC
    """, (session['user_id'],))
    applications = cursor.fetchall()
    conn.close()
    return render_template("student/applied_jobs.html", applications=applications)

@app.route('/student/upload-resume', methods=['GET', 'POST'])
def student_upload_resume():
    if session.get('role') != 'student':
        return redirect('/student/login')
    if request.method == 'POST':
        if 'resume' not in request.files:
            return redirect(request.url)
        f = request.files['resume']
        if not f.filename:
            return redirect(request.url)
        if not allowed_file(f.filename):
            return "Only PDF files are allowed."
        path = save_resume(f, prefix=f"student_{session['user_id']}")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE student SET resume_path = ? WHERE id = ?", (path, session['user_id']))
        conn.commit()
        conn.close()
        return redirect('/student/dashboard')
    return render_template("student/upload_resume.html")

@app.route('/student/notifications')
def student_notifications():
    if session.get('role') != 'student':
        return redirect('/student/login')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.status, pd.job_title, c.name
        FROM application a
        JOIN placement_drive pd ON a.drive_id = pd.id
        JOIN company c ON pd.company_id = c.id
        WHERE a.student_id = ?
          AND a.status IN ('Shortlisted', 'Selected', 'Rejected')
        ORDER BY a.application_date DESC
    """, (session['user_id'],))
    notifications = cursor.fetchall()
    conn.close()

    return render_template("student/notifications.html", notifications=notifications)


# --- Shared helpers and role-specific student profile routes ---
def _load_student_profile(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return None, None, None

    cursor.execute("""
        SELECT 
            a.application_date,
            a.status,
            pd.job_title,
            c.name AS company_name
        FROM application a
        JOIN placement_drive pd ON a.drive_id = pd.id
        JOIN company c ON pd.company_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.application_date DESC
    """, (student_id,))
    applications = cursor.fetchall()

    cursor.execute("""
        SELECT 
            jp.title,
            jp.description,
            jp.employment_type,
            jp.offered_salary,
            jp.offered_at,
            c.name AS company_name
        FROM job_position jp
        JOIN company c ON jp.company_id = c.id
        WHERE jp.student_id = ?
        ORDER BY jp.offered_at DESC
    """, (student_id,))
    placements = cursor.fetchall()

    conn.close()
    return student, applications, placements


@app.route('/student/profile')
def student_profile_self():
    if session.get('role') != 'student':
        return redirect('/student/login')
    student_id = session.get('user_id')
    student, applications, placements = _load_student_profile(student_id)
    if not student:
        return "Student not found", 404
    return render_template("student/profile.html",
                           student=student,
                           applications=applications,
                           placements=placements)


@app.route('/admin/student-profile/<int:student_id>')
def admin_student_profile(student_id):
    if session.get('role') != 'admin':
        return redirect('/')
    student, applications, placements = _load_student_profile(student_id)
    if not student:
        return "Student not found", 404
    return render_template("admin/student_profile.html",
                           student=student,
                           applications=applications,
                           placements=placements)


@app.route('/company/student-profile/<int:student_id>')
def company_student_profile(student_id):
    if session.get('role') != 'company':
        return redirect('/')
    student, applications, placements = _load_student_profile(student_id)
    if not student:
        return "Student not found", 404
    source = request.args.get('from') or ''
    drive_id = request.args.get('drive_id')
    return render_template("company/student_profile.html",
                           student=student,
                           applications=applications,
                           placements=placements,
                           source=source,
                           drive_id=drive_id)


@app.route('/company/students')
def company_students():
    if session.get('role') != 'company':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()
    conn.close()

    return render_template("company/students.html", students=students)


@app.route('/company/offer/<int:app_id>', methods=['GET', 'POST'])
def company_offer(app_id):
    if session.get('role') != 'company':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            a.student_id,
            a.drive_id,
            s.name AS student_name,
            pd.job_title,
            pd.job_description,
            pd.company_id
        FROM application a
        JOIN student s ON a.student_id = s.id
        JOIN placement_drive pd ON a.drive_id = pd.id
        WHERE a.id = ?
    """, (app_id,))
    app_row = cursor.fetchone()

    if not app_row:
        conn.close()
        return "Application not found", 404

    if request.method == 'POST':
        title = request.form.get('title') or app_row['job_title']
        description = request.form.get('description') or app_row['job_description']
        employment_type = request.form.get('employment_type') or 'Full Time'
        offered_salary = request.form.get('offered_salary')

        # Avoid duplicate job_position for same student/drive/company
        cursor.execute("""
            SELECT id FROM job_position
            WHERE student_id = ? AND placement_drive_id = ? AND company_id = ?
        """, (app_row['student_id'], app_row['drive_id'], app_row['company_id']))
        exists = cursor.fetchone()

        cursor.execute(
            "UPDATE application SET status = 'Selected' WHERE id = ?",
            (app_id,)
        )

        if not exists:
            cursor.execute("""
                INSERT INTO job_position
                (student_id, company_id, placement_drive_id, title, description, employment_type, offered_salary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                app_row['student_id'],
                app_row['company_id'],
                app_row['drive_id'],
                title,
                description,
                employment_type,
                offered_salary
            ))

        conn.commit()
        conn.close()
        return redirect(f"/company/applications/{app_row['drive_id']}")

    conn.close()
    return render_template("company/offer_form.html", app=app_row)


if __name__ == "__main__":
    app.run(debug=True)