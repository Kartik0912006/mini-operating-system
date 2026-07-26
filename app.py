from flask import Flask, render_template, request, redirect
import secrets
import string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mini_os.db'
app.config['SECRET_KEY'] = 'change-this-later-to-something-random'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    date = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    result = None
    if request.method == 'POST':
        num1 = float(request.form['num1'])
        num2 = float(request.form['num2'])
        op = request.form['op']
        if op == '+': result = num1 + num2
        elif op == '-': result = num1 - num2
        elif op == '*': result = num1 * num2
        elif op == '/': result = num1 / num2 if num2 != 0 else 'Error'
    return render_template('calculator.html', result=result)

@app.route('/password-gen', methods=['GET', 'POST'])
def password_gen():
    password = None
    if request.method == 'POST':
        length = int(request.form['length'])
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(chars) for _ in range(length))
    return render_template('password_gen.html', password=password)

@app.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        new_note = Note(title=request.form['title'], content=request.form['content'], user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
    all_notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('notes.html', notes=all_notes)

@app.route('/notes/delete/<int:id>')
@login_required
def delete_note(id):
    note = Note.query.get(id)
    db.session.delete(note)
    db.session.commit()
    return redirect('/notes')

@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    if request.method == 'POST':
        new_contact = Contact(
            name=request.form['name'],
            phone=request.form['phone'],
            email=request.form['email'],
            user_id=current_user.id
        )
        db.session.add(new_contact)
        db.session.commit()
    all_contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', contacts=all_contacts)

@app.route('/contacts/delete/<int:id>')
@login_required
def delete_contact(id):
    contact = Contact.query.get(id)
    db.session.delete(contact)
    db.session.commit()
    return redirect('/contacts')

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        new_expense = Expense(
            amount=float(request.form['amount']),
            category=request.form['category'],
            date=request.form['date'],
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()
    all_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    total = sum(e.amount for e in all_expenses)
    return render_template('expenses.html', expenses=all_expenses, total=total)

@app.route('/expenses/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect('/expenses')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect('/')
        error = "Invalid username or password."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    message = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        if check_password_hash(current_user.password_hash, current_password):
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            message = "Password updated successfully!"
        else:
            message = "Current password is incorrect."
    return render_template('settings.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)