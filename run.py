from flask import Flask, session, redirect, url_for
from database import initialize_database
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev_secret_key_change_later'
    initialize_database()
    @app.route('/')
    def home():
        if 'username' in session:
            return f"Welcome {session['username']}"
        return "You are not logged in"
    @app.route("/login-test")
    def login_test():
        session['username'] = "Soham"
        return redirect(url_for('home'))
    
    @app.route("/logout-test")
    def logout_test():
        session.clear()
        return redirect(url_for('home'))
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)