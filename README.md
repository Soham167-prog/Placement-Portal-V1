# Placement Portal Web Application

## Author
**Name:** Soham Narayankhedkar  
**Roll Number:** 24f2003116
**Email:** 24f2003116@ds.study.iitm.ac.in

## Project Description
This project is a **Placement Portal Web Application** developed using Flask.  
The system connects **students, companies, and administrators** to manage placement drives and recruitment processes. Students can apply to job drives, companies can post opportunities and review applicants, and administrators can monitor the overall system.

## Technologies Used
- Python
- Flask Framework
- Flask-Route
- Flask-Login
- SQLite
- HTML
- CSS
- Jinja2 Template Engine

## Project Structure

```
Placement-Portal-24f2003116/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── controllers
├── .venv
├── __pycache__
├── gitignore
│
├── templates/
│   ├── admin
│   ├── company
│   └── student
│   └── home.html
|   └── base.html
|
├── static/
│   ├── css/
│   └── resumes/
│
└── placement_portal.db
```

## Features
### Student
- Register and login
- View placement drives
- Apply for job drives
- Upload resume
- View personal profile

### Company
- Register and login
- Create placement drives
- View applicants
- View student profiles
- Select candidates

### Admin
- View system statistics
- View registered students and companies
- Monitor placement records
- Blacklist users if required

## Setting Up the Project
### 1. Clone or Download the Project
Download the project folder and navigate to it in the terminal.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

#### Mac / Linux

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

## 4. Install Required Dependencies

Install packages using pip:

```bash
pip install -r requirements.txt
```

If requirements.txt is not available, install manually:

```bash
pip install flask
pip install flask-login
pip install flask-sqlalchemy
pip install werkzeug
```

## Running the Application

Start the Flask application using:

```bash
python app.py
```

The application will start at:

```
http://127.0.0.1:5000
```

Open the above URL in your browser to access the portal.

## Database

The project uses **SQLite** for storing application data.

The database stores information related to:
- Users
- Placement Drives
- Applications
- Placement Records

The database file is located inside the **instance** folder.

## Notes

- Uploaded resumes are stored in **static/resumes/**
- User authentication and session management are handled using **Flask-Login**
- HTML templates are rendered using **Jinja2**

## License

This project is developed for academic purposes.