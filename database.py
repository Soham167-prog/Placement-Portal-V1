import sqlite3
from datetime import datetime 

DB_NAME = "placement_portal.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    #Admin table
    cursor.execute(""" 
       CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL      
        )           
    """)

    #Student table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS student (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           name TEXT NOT NULL,
           email TEXT UNIQUE NOT NULL,
           password TEXT NOT NULL,
           phone TEXT,
           resume_path TEXT,
           is_active INTEGER DEFAULT 1,
           created_at TEXT
        )
    """)

    #Company table
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS company (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          email TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL,
          hr_contact TEXT,
          website TEXT,
          approval_status TEXT DEFAULT 'Pending',
          is_active INTEGER DEFAULT 1,
          created_at TEXT          
        )
    """)

    #Placement drive table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS placement_drive(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            job_title TEXT NOT NULL,
            job_description TEXT,
            eligibility TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT,
            FOREIGN KEY(company_id) REFERENCES company(id)              
        )
    """)

    #Application table 
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS application (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            drive_id INTEGER,
            application_date TEXT,
            status TEXT DEFAULT 'Applied',
            UNIQUE(student_id, drive_id),
            FOREIGN KEY(student_id) REFERENCES student(id),
            FOREIGN KEY(drive_id) REFERENCES placement_drive(id)
        )
    """)
    
    #Insert default admin if not exists
    cursor.execute("SELECT * FROM admin WHERE username = ?", ("admin",))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        cursor.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
    
    conn.commit()
    conn.close()