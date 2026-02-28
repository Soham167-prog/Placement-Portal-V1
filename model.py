from database import get_connection
from datetime import datetime

#Student creation and finding(auth)
def create_student(name,email,password,phone):
    conn = get_connection()
    conn.execute("""
        INSERT INTO student (name,email,password,phone,created_at)
        VALUES ( ?, ?, ?, ?, ?)
    """, (name, email, password, phone, datetime.now().isformat()))
    conn.commit()
    conn.close()

def find_student(email, password):
    conn = get_connection()
    student = conn.execute("""
        SELECT * FROM student
        WHERE email=? AND password=? AND is_active=1
    """, (email,password)).fetchone()
    conn.close()
    return student


#Company creation and finding(auth)
def create_company(name, email, password, hr_contact, website):
    conn = get_connection()
    conn.execute("""
        INSERT INTO company (name, email, password, hr_contact, website, created_at)
        VALUES(?, ?, ?, ?, ?, ?)
    """, (name, email, password, hr_contact, website, datetime.now().isformat()))
    conn.commit()
    conn.close()

def find_company(email, password):
    conn = get_connection()
    company = conn.execute("""
        SELECT * FROM company
        WHERE email=? AND password=?
        AND approval_status='Approved'
        AND is_active=1    
    """, (email, password)).fetchone()
    conn.close()
    return company


#Admin auth
def find_admin(username, password):
    conn = get_connection()
    admin = conn.execute("""
       SELECT * FROM admin
       WHERE username=? AND password=?
    """, (username, password)).fetchone()
    conn.close()
    return admin