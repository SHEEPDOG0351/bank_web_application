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
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        

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

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root', 
        password='password', 
        database='banking_app'  
    )
    return connection

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            error = "Both fields (Username and Password) are required"
            return render_template('login.html', error=error)
        

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            session['account_type'] = 'user'  
            return redirect('/dashboard')  
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)

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

@app.route("/api/transfer", methods=["POST"])
def transfer():
    data = request.get_json()

    recipients_account_num = data.get("recipients_account_num")
    senders_transaction_amount = int(data.get("senders_transaction_amount"))

    senders_account_num = data.get("senders_account_num")

    senders_card_num = data.get("senders_card_num")
    senders_card_ccv = data.get("senders_card_ccv")

    if senders_account_num:
        sender = Bank_accounts.query.filter_by(bank_account_number = senders_account_num).first()

    elif senders_card_num:
        senders_card = Users_cards.query.filter_by(card_number = senders_card_num).first()
        if not senders_card:
            return jsonify({"error": "Invalid card number"}), 404
        sender = Bank_accounts.query.filter_by(bank_account_number=senders_card.bank_account_number).first()
    else:
        return jsonify({"error": "No valid sender provided"}), 400
    
    if not sender:
        return jsonify({"error": "Sender account not found"}), 404
    
    recipient = Bank_accounts.query.filter_by(bank_account_number=recipients_account_num).first()
    if not recipient:
        return jsonify({"error": "Recipient's account num wasn't found"}), 404
    
    print(f"Sender.balance type: {type(sender.balance)}\nsenders transaction amount type: {type(senders_transaction_amount)}")
    if sender.balance < senders_transaction_amount:
        return jsonify({"error": "Insufficient funds"}), 400
    
    # Performs the transaction
    sender.balance -= senders_transaction_amount
    recipient.balance += senders_transaction_amount
    db.session.commit()

    return jsonify({
        "message": "Transfer successful",
        "sender_new_balance": sender.balance
    })


if __name__ == '__main__':
        app.run(debug=True)
