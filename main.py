from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text
conn_str = "mysql://root:cset155@localhost/exam_management_2"
engine = create_engine(conn_str, echo = True)
conn = engine.connect()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:cset155@localhost/banking_app"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(36), nullable=False)
    first_name = db.Column(db.String(15), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    social_security = db.Column(db.String(11), primary_key=True)
    address = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    bank_account_number = db.Column(db.String(20), nullable=False)
    approved = db.Column(db.Boolean, default=False)

class Admin_accounts(db.Model):
    __tablename__ = 'admin_accounts'
    username = db.Column(db.String(36), primary_key=True)
    password = db.Column(db.String(50), nullable=False)

class Bank_accounts(db.Model):
    __tablename__ = 'bank_accounts'
    bank_account_number = db.Column(db.String(20), primary_key=True)
    social_security = db.Column(db.String(11), db.ForeignKey('users.social_security'), nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)

class Users_cards(db.Model):
    __tablename__ = 'users_cards'
    bank_account_number = db.Column(db.String(20), db.ForeignKey('bank_accounts.bank_account_number'), nullable=False)
    card_number = db.Column(db.String(20), primary_key=True)
    expiry_date = db.Column(db.String(7), nullable=False)
    ccv = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)

@app.route('/')
def index():
    return render_template('accounts.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/accounts')
def accounts():
    return render_template('accounts.html')

@app.route("/api/account/<bank_account_number>", methods=["GET"]) # This route is used to pull the data needed for displaying user information from the SQL database and preparing it for JS
def get_account_info(bank_account_number): # using the bank account num given in the request:
    user = Users.query.filter_by(bank_account_number=bank_account_number).first()
    # .first() returns the first matching row or None if not found.
    # (It's still good practice even if bank account numbers are unique — avoids raising an exception.)

    if user: # if it can find said user using their bank account number:
        return jsonify({ # the JS object which we will use in accounts.html
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "social_security": user.social_security,
            "bank_account_number": user.bank_account_number,
            "address": user.address,
            "password": user.password,
            "phone_number": user.phone_number
        })
    else: # if it can't find a user with said bank account number:
        return jsonify({"error": "Account not found"}), 404
    
@app.route("/api/transaction/<>", methods=["GET"])
if __name__ == '__main__':
        app.run(debug=True)