from flask import Flask, render_template, request, redirect, session, url_for
from database import initialize_database, get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "super_secret_key"

initialize_database()

#Home page
@app.route('/')
def home():
    return render_template("home.html")

#Student register
@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        resume_path = request.form['resume_path']
        is_active = 1
        created_at = datetime.now()

        conn = get_connection()
        cursor = conn.cursor()

        # Email uniqueness
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
        name = request.form['name']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM student WHERE name = ? AND is_active = 1", (name,))
        student = cursor.fetchone()
        conn.close()

        if student and check_password_hash(student['password'], password):
            session.clear()
            session['user_id'] = student['id']
            session['role'] = 'student'
            session['username'] = student['name']
            return redirect('/student/dashboard')

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
        SET status = 'Rejected'
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

    conn = sqlite3.connect("placement_portal.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM application")

    applications = cursor.fetchall()
    conn.close()

    return render_template("admin/applications.html", applications=applications)
#Dashboards
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/')
    return render_template("student/dashboard.html")


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

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        blacklisted_students=blacklisted_students,
        total_companies=total_companies,
        blacklisted_companies=blacklisted_companies,
        total_drives=total_drives,
        total_applications=total_applications
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

        cursor.execute("""
            INSERT INTO placement_drive
            (company_id, job_title, job_description, eligibility, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'Pending', datetime('now'))
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

#View applications for company jobs
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
            a.status
        FROM application a
        JOIN student s ON a.student_id = s.id
        WHERE a.drive_id = ?
    """, (drive_id,))

    applications = cursor.fetchall()
    conn.close()

    return render_template("company/applications.html", applications=applications)

#Update Application Status
@app.route('/company/update-application/<int:app_id>/<status>')
def update_application_status(app_id, status):
    if session.get('role') != 'company':
        return redirect('/')
    
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


if __name__ == "__main__":
    app.run(debug=True)