from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from pathlib import Path
from db import db
from models import Drug, Order, DrugOrder, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func 
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from passlib.hash import scrypt 
from forms import RegistrationForm, LoginForm, UserUpdateForm
from flask_login import login_manager, login_required, current_user, login_user, LoginManager, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask application
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sql.db"
app.instance_path = Path("./data").resolve()
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)

# Secret key for form validation
app.config["SECRET_KEY"] = '12345678901'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration form
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('A user with this email already exists. Please log in or use a different email.', 'danger')
        else:
            hashed_password = scrypt.encrypt(form.password.data)  
            user = User(name=form.name.data, email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# Home route
@app.route("/")
def home():
    return render_template("base.html", name="Chris")

# Upload Prescription route
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # Logic to handle the uploaded prescription
        # This will depend on how you're handling file uploads
        pass
    return render_template("upload.html")

# Prescription History route
@app.route("/history")
def history():
    # Logic to fetch and display the prescription history
    # This will depend on how you're storing prescriptions
    return render_template("history.html")

# Orders route
@app.route('/orders')
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).join(DrugOrder).order_by(DrugOrder.date_ordered.desc()).all()
    return render_template('orders.html', orders=orders)

# Support route
@app.route("/support", methods=["GET", "POST"])
def support():
    if request.method == "POST":
        # Logic to handle support queries
        # This could involve sending an email or storing the query in a database
        pass
    return render_template("support.html")

# Login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.email) == func.lower(form.email.data)).first()
        if user:
            if user.password and scrypt.verify(form.password.data, user.password): 
                login_user(user)
                flash('You have successfully logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('Invalid email.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('home'))

# Dashboard Route
@app.route("/dashboard")
def dashboard():
    if current_user.is_authenticated:
        return render_template('dashboard.html', title='Dashboard', name=current_user.name, email=current_user.email)
    else:
        return redirect(url_for('login'))

# User details route
@app.route('/userdetails', methods=['GET', 'POST'])
@login_required
def userdetails():
    form = UserUpdateForm()

    if form.validate_on_submit():
        if scrypt.verify(form.current_password.data, current_user.password):
            current_user.address = form.address.data

            # Format phone number with dashes
            phone = form.phone.data
            phone = phone.replace("-", "")  # remove any existing dashes
            phone = "{}-{}-{}".format(phone[:3], phone[3:6], phone[6:])  # insert dashes
            current_user.phone = phone

            if form.new_password.data:
                current_user.password = scrypt.encrypt(form.new_password.data)

            db.session.commit()
            flash('Your account information has been updated!', 'success')
            return redirect(url_for('userdetails'))
        else:
            flash('Incorrect current password.', 'error')

    elif request.method == 'GET':
        form.name.data = current_user.name
        form.address.data = current_user.address
        form.phone.data = current_user.phone
        form.email.data = current_user.email

    return render_template('userdetails.html', title='User Details', form=form)


@app.route("/api/users") 
def users_json():
    statement = db.select(User).order_by(User.name)
    results = db.session.execute(statement)
    users = []
    for user in results.scalars():
        json_record = {
            "id": user.id,
            "name": user.name, 
            "phone": user.phone,
            # Add other relevant user data if needed
        }
        users.append(json_record)
    return jsonify(users)

# API route to create a new user
@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    if not data or "name" not in data or "phone" not in data:
        return "Invalid request", 400
    new_user = User(name=data["name"], phone=data["phone"]) 
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return "A user with this name already exists", 400
    return jsonify({"message": "User created successfully!"})

# Drugs Available route
@app.route("/drugs")
def drugs():
  statement = db.select(Drug).order_by(Drug.name)
  result = db.session.execute(statement)
  drug_list = result.scalars().all()
  return render_template("drugs.html", drugs=drug_list)

# API route to get all drugs in JSON format
@app.route("/api/drugs")
def drugs_json():
  statement = db.select(Drug).order_by(Drug.name)
  results = db.session.execute(statement)
  drugs = []
  for drug in results.scalars():
    json_record = {
      "id": drug.id,
      "name": drug.name,
      "price": drug.price,
    }
    drugs.append(json_record)
  return jsonify(drugs)

# API route to get a specific drug in JSON format
@app.route("/api/drugs/<int:drug_id>")
def drug_detail_json(drug_id):
  statement = db.select(Drug).where(Drug.id == drug_id)
  result = db.session.execute(statement).scalars().first()
  if result is None:
    return jsonify({"error": "Drug not found"}), 404
  return jsonify(result.to_json())

# Run the application
if __name__ == "__main__":
    app.run(debug=True, port=8888)
