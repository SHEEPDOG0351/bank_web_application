from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text
import random
import bcrypt
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



@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        social_security = request.form['social_security']
        address = request.form['address']
        phone_number = request.form['phone_number']
        password = request.form['password']
        
        if not username or not first_name or not last_name or not social_security or not address or not phone_number or not password:
            flash("All fields are required", "error")
            return redirect('/signup') 
        
        existing_user = Users.query.filter_by(social_security=social_security).first()
        if existing_user:
            flash("A user with this SSN already exists", "error")
            return redirect('/signup')  
        
        def hash(str):
            sum=0
            seacrch_string="abcdefghijklmnopqrstuvwxyz"
            for char in str:
                sum += seacrch_string.find(char)+1
            return sum
        
        salt = bcrypt.gensalt
        cerds = {}
        

        new_user = Users(
            username=username,
            first_name=first_name,
            last_name=last_name,
            social_security=social_security,
            address=address,
            phone_number=phone_number,
            password=hashed_password,
            bank_account_number="temporary_account_number" 
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully!", "success")
        return redirect('/')   
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/accounts')
def accounts():
    return render_template('accounts.html')

@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

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
    
@app.route("/api/transaction", methods=["POST"])
def process_transaction():
    data = request.get_json()
    card_number = data.get("card_number")
    expiry_date = data.get("expiry_date")
    ccv = data.get("ccv")
    amount = int(data.get("amount"))

    # Find card
    card = Users_cards.query.filter_by(
        card_number=card_number,
        expiry_date=expiry_date,
        ccv=ccv
    ).first()

    if not card:
        return jsonify({"error": "Card not found or invalid info"}), 404

    # Get bank account and add amount
    bank_account = Bank_accounts.query.filter_by(bank_account_number=card.bank_account_number).first()
    if not bank_account:
        return jsonify({"error": "Associated bank account not found"}), 404

    # Credit the amount
    bank_account.balance += amount
    db.session.commit()

    return jsonify({"message": "Transaction successful", "new_balance": bank_account.balance})

if __name__ == '__main__':
        app.run(debug=True)
