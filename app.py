from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_from_directory, abort
from pathlib import Path
from db import db
from models import Drug, Order, DrugOrder, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_bcrypt import Bcrypt
from forms import RegistrationForm, LoginForm, UserUpdateForm, UploadForm
from flask_login import login_manager, login_required, current_user, login_user, LoginManager, logout_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Initialize Flask application
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sql.db"
app.instance_path = Path("./data").resolve()
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)
bcrypt = Bcrypt(app)

# Secret key for form validation
app.config["SECRET_KEY"] = '12345678901'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Registration form
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate():
            user = User.query.filter(func.lower(User.email) == func.lower(form.email.data)).first()
            user_phn = User.query.filter_by(phn=form.phn.data).first()
            if user:
                flash('A user with this email already exists. Please log in or use a different email.', 'danger')
            elif user_phn:
                flash('A user with this PHN already exists. Please log in or use a different PHN.', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  
                user = User(name=form.name.data, email=form.email.data.lower(), phn=form.phn.data, password=hashed_password, role_id=2) 
                db.session.add(user)
                db.session.commit()
                flash('Your account has been created! You can now log in.', 'success')
                return redirect(url_for('login'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return render_template('register.html', title='Register', form=form)


# Home route
@app.route("/")
def home():
    return render_template("base.html", name="Chris")

def get_uploader_name():
    return current_user.name

# Upload Prescription route
# Set the upload folder in your configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    filename = None
    uploader_name = get_uploader_name()  # function to get the uploader's name from the database
    if form.validate_on_submit():
        f = form.file.data
        original_filename = secure_filename(f.filename)
        upload_time = datetime.now().strftime("%Y%m%d%H%M%S")  # get the current date and time
        extension = os.path.splitext(original_filename)[1]  # get the extension from the original filename
        filename = f"{upload_time}_{uploader_name}{extension}"  # prepend the uploader's name and upload time to the filename and append the extension
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Create a new order for the current user
        order = Order(user_id=current_user.id)

        # Save the order to the database
        db.session.add(order)
        db.session.commit()

        # Now create a new DrugOrder linked to the order
        drug_order = DrugOrder(order_id=order.id, image_file=filename, prescription_approved=None, date_ordered=datetime.utcnow())  # prescription_approved is set to None

        # Save the DrugOrder to the database
        db.session.add(drug_order)
        db.session.commit()

        flash('Your file has been uploaded and is awaiting approval.', 'success')
        return redirect(url_for('home'))

    return render_template('upload.html', form=form, filename=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'data', 'uploads'), filename)

@app.route('/pharmacistdash')
@login_required
def pharmacistdash():
    if current_user.role_id != 1:
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('home'))

    # Fetch approved and unapproved orders from the database
    approved_orders = db.session.query(Order).join(DrugOrder).filter(DrugOrder.prescription_approved == True).order_by(desc(DrugOrder.date_ordered)).all()
    unapproved_prescriptions = db.session.query(Order).join(DrugOrder).filter(DrugOrder.prescription_approved == False).order_by(desc(DrugOrder.date_ordered)).all()

    # Pass the sorted lists to the template
    return render_template('pharmacistdash.html', unapproved_prescriptions=unapproved_prescriptions, approved_orders=approved_orders)

@app.route('/review_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def review_order(order_id):
    # Fetch the order from the database
    order = DrugOrder.query.get(order_id)

    # If the order doesn't exist, redirect to a different page or show an error
    if order is None:
        flash('Order not found', 'error')
        return redirect(url_for('pharmacistdash'))

    # Check if the form is submitted
    if request.method == 'POST':
        # Update the order status based on the form data
        status = request.form.get('status')
        if status == 'approved':
            order.prescription_approved = True

            # Update the drug and quantity based on the form data
            drug_name = request.form.get('drug_name')
            quantity = request.form.get('quantity')
            refills = request.form.get('refills')  # Get the refill count from the form data

            # Find the drug by name
            drug = Drug.query.filter_by(name=drug_name).first()

            # If the drug exists, update the drug and quantity
            if drug is not None:
                order.drug = drug
                order.quantity = quantity
                order.refills = refills  # Update the refill count
        elif status == 'denied':
            order.prescription_approved = False

        db.session.commit()
        return redirect(url_for('pharmacistdash'))

    # Render the review_order template
    drugs = Drug.query.all()
    return render_template('review_order.html', order=order, drugs=drugs)

# Prescription History route
@app.route("/history")
def history():
    # Logic to fetch and display the prescription history
    # This will depend on how you're storing prescriptions
    return render_template("history.html")

@app.route('/track', methods=['GET'])
def track():
    return render_template('track.html')

# Orders route
@app.route('/orders')
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).join(DrugOrder).order_by(DrugOrder.date_ordered.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    order_id = data.get('orderId')

    if order_id is None:
        return jsonify(success=False, error='No order ID provided'), 400

    drug_order = DrugOrder.query.get(order_id)

    if drug_order is None:
        return jsonify(success=False, error='No order found with this ID'), 404

    drug_order.paid = True
    db.session.commit()

    return jsonify(success=True)

@app.route('/payrefill', methods=['POST'])
def payrefill():
    data = request.get_json()
    order_id = data.get('orderId')

    if order_id is None:
        return jsonify(success=False, error='No order ID provided'), 400

    drug_order = DrugOrder.query.get(order_id)

    if drug_order is None:
        return jsonify(success=False, error='No order found with this ID'), 404

    if drug_order.refills <= 0:
        return jsonify(success=False, error='No refills available for this order'), 400

    drug_order.refills -= 1
    db.session.commit()

    return jsonify(success=True)

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
            if user.password and bcrypt.check_password_hash(user.password, form.password.data):  
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
        if bcrypt.check_password_hash(current_user.password, form.current_password.data):
            current_user.address = form.address.data
            current_user.phn = form.phn.data  # update PHN

            # Format phone number with dashes
            phone = form.phone.data
            phone = phone.replace("-", "")  # remove any existing dashes
            phone = "{}-{}-{}".format(phone[:3], phone[3:6], phone[6:])  # insert dashes
            current_user.phone = phone

            if form.new_password.data:
                current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')

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
        form.phn.data = current_user.phn  # populate PHN field

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
    app.run(debug=True, port=443)
