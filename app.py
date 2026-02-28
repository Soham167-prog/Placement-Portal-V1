from flask import Flask, render_template, request, redirect, session
from database import initialize_database, get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
            return redirect('/admin/dashboard')

        return "Invalid Admin Credentials"

    return render_template("admin/login.html")

#Admin granting permissions to the company
@app.route('/admin/companies')
def view_companies():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM company")
    companies = cursor.fetchall()

    conn.close()

    return render_template("admin/companies.html", companies=companies)

@app.route('/admin/approve/<int:company_id>')
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
    return render_template("company/dashboard.html")


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/')
    return render_template("admin/dashboard.html")

#Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)