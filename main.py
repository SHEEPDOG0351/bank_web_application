from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text
import random
import bcrypt
import mysql.connector
conn_str = "mysql://root:cset155@localhost/banking_app"
engine = create_engine(conn_str, echo = True)
conn = engine.connect()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey123'
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

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_account = db.Column(db.String(20), nullable=True)
    recipient_account = db.Column(db.String(20), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

@app.route('/')
def index():
    return render_template('signup.html')

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
            flash(" user already exists", "error")
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
            bank_account_number="temp_acc_num", 
            approved=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully!", "success")
        return redirect('/waiting')   
    return render_template('signup.html')


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root', 
        password='your_password',
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

        user_account = Users.query.filter_by(username=username).first()
        if user_account and bcrypt.checkpw(password.encode('utf-8'), user_account.password.encode('utf-8')):
            session['username'] = username
            session['account_type'] = 'user'
            session['password'] = password  

            return redirect('/accounts') 

        error = "Invalid username or password"
        return render_template('login.html', error=error)

    return render_template('login.html')



   
def ensure_single_admin():
    with app.app_context():  
        existing_admin = Admin_accounts.query.first()
        if not existing_admin:
            print("No admin account found. Please create one manually.")
            

ensure_single_admin()
   
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin_account = Admin_accounts.query.filter_by(username=username).first()
        admin_password = Admin_accounts.query.filter_by(password=password).first()

        if admin_account and admin_password:
            session['username'] = username
            session['account_type'] = 'admin'
            session['password'] = password

            return jsonify({"success": True})
        
        return jsonify({"success": False})

    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('account_type') != 'admin':
        return redirect('/admin/login')

    
    unapproved_users = Users.query.filter_by(approved=False).all()
    return render_template('admin_dashboard.html', users=unapproved_users)


@app.route('/admin/approve_user/<social_security>', methods=['POST'])
def approve_user(social_security):
    if session.get('account_type') != 'admin':
        return redirect('/admin/login')

    user = Users.query.filter_by(social_security=social_security).first()

    if not user:
        flash("User not found", "error")
        return redirect('/admin/dashboard')

    new_account_number = str(random.randint(100000000, 999999999))  

    user.bank_account_number = new_account_number
    user.approved = True
    db.session.commit()

    new_bank_account = Bank_accounts(
        bank_account_number=new_account_number,
        social_security=user.social_security,
        balance=0  
    )
    db.session.add(new_bank_account)
    db.session.commit()

    flash("User approved successfully!", "success")
    return redirect('/admin/dashboard')



@app.route('/admin/deny_user/<social_security>', methods=['POST'])
def deny_user(social_security):
    if session.get('account_type') != 'admin':
        return redirect('/admin/login')

    user = Users.query.filter_by(social_security=social_security).first()

    if not user:
        flash("User not found", "error")
        return redirect('/admin/dashboard')

    db.session.delete(user)
    db.session.commit()

    flash("User denied and removed successfully!", "success")
    return redirect('/admin/dashboard')

@app.route('/waiting')
def waiting():
    return render_template('waiting.html')

@app.route('/accounts')
def accounts():
    return render_template('accounts.html')

@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

@app.route('/bank_statement')
def bank_statement():
    return render_template("bank_statement.html")

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
def handle_transaction():
    data = request.get_json()
    
    card_number = data.get("card_number")
    expiry_date = data.get("expiry_date")
    ccv = data.get("ccv")
    amount = int(data.get("amount"))
    bank_account_number = data.get("bank_account_number")

    account = Bank_accounts.query.filter_by(bank_account_number=bank_account_number).first()
    if not account:
        return jsonify({"error": "Bank account not found"}), 404

    account.balance += amount

    new_transaction = Transaction(
        sender_account=None,
        recipient_account=bank_account_number,
        transaction_type="deposit",
        amount=amount
    )
    db.session.add(new_transaction)
    db.session.commit()

    return jsonify({"message": "Deposit successful", "new_balance": account.balance})



@app.route("/api/transfer", methods=["POST"])
def transfer():
    data = request.get_json()

    recipients_account_num = data.get("recipients_account_num")
    senders_transaction_amount = int(data.get("senders_transaction_amount"))

    senders_account_num = data.get("senders_account_num")
    senders_card_num = data.get("senders_card_num")  # still unused, but we get it
    senders_card_ccv = data.get("senders_card_ccv")

    # Try to pull sender account info if provided
    sender = None
    if senders_account_num:
        sender = Bank_accounts.query.filter_by(bank_account_number=senders_account_num).first()
        if not sender:
            return jsonify({"error": "Sender account not found"}), 404

    recipient = Bank_accounts.query.filter_by(bank_account_number=recipients_account_num).first()
    if not recipient:
        return jsonify({"error": "Recipient's account num wasn't found"}), 404

    if sender:
        # Verify sender has enough money
        if sender.balance < senders_transaction_amount:
            return jsonify({"error": "Insufficient funds"}), 400

        # Deduct from real sender's balance
        sender.balance -= senders_transaction_amount

    # Always add to recipient
    recipient.balance += senders_transaction_amount

    # Log the transaction (show sender if real, else simulate)
    new_transaction = Transaction(
        sender_account=sender.bank_account_number if sender else "CARD",
        recipient_account=recipient.bank_account_number,
        transaction_type="transfer",
        amount=senders_transaction_amount
    )
    db.session.add(new_transaction)
    db.session.commit()

    return jsonify({
        "message": "Transfer successful",
        "sender_new_balance": sender.balance if sender else "N/A"
    })



@app.route("/api/statement/<bank_account_number>", methods=["GET"])
def get_bank_statement(bank_account_number):
    transactions = Transaction.query.filter(
        (Transaction.sender_account == bank_account_number) | 
        (Transaction.recipient_account == bank_account_number)
    ).order_by(Transaction.timestamp.desc()).all()

    return jsonify([
        {
            "id": t.id,
            "type": t.transaction_type,
            "amount": t.amount,
            "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "sender": t.sender_account,
            "recipient": t.recipient_account
        }
        for t in transactions
    ])

if __name__ == '__main__':
        app.run(debug=True)
