from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_from_directory
from pathlib import Path
from db import db
from models import Drug, Order, DrugOrder, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, distinct
from flask_bcrypt import Bcrypt
from forms import RegistrationForm, LoginForm, UserUpdateForm, UploadForm, SupportForm
from flask_login import login_manager, login_required, current_user, login_user, LoginManager, logout_user
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import os
import errno
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

app.config['LOGIN_VIEW'] = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# To Handle Unauthorized Access
@app.errorhandler(401)
def handle_401(e):
    return redirect(url_for('login'))

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
@login_required
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

        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(os.path.dirname(upload_path)):
            try:
                os.makedirs(os.path.dirname(upload_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        f.save(upload_path)

        # Create a new order for the current user
        order = Order(user_id=current_user.id)

        # Save the order to the database
        db.session.add(order)
        db.session.commit()

        # Now create a new DrugOrder linked to the order
        drug_order = DrugOrder(order_id=order.id, image_file=filename, prescription_approved=None, date_ordered=datetime.now(timezone.utc))  # prescription_approved is set to None

        # Save the DrugOrder to the database
        db.session.add(drug_order)
        db.session.commit()

        flash('Your file has been uploaded and is awaiting approval.', 'success')

    return render_template('upload.html', form=form, filename=filename)

@app.route('/upload/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'data', 'uploads'), filename)
    

@app.route('/pharmacistdash')
@login_required
def pharmacistdash():
    page_unapproved = request.args.get('page_unapproved', 1, type=int)
    page_approved = request.args.get('page_approved', 1, type=int)
    page_denied = request.args.get('page_denied', 1, type=int)
    per_page = 10
    if current_user.role_id != 1:
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('home'))

    # Fetch approved, unapproved, and denied orders from the database
    approved_orders = db.session.query(Order).join(DrugOrder, Order.id == DrugOrder.order_id).filter(DrugOrder.prescription_approved == True).group_by(Order.id).order_by(DrugOrder.date_ordered.desc()).paginate(page=page_approved, per_page=per_page, error_out=False)
    unapproved_prescriptions = db.session.query(Order).join(DrugOrder, Order.id == DrugOrder.order_id).filter(DrugOrder.prescription_approved == None).group_by(Order.id).order_by(DrugOrder.date_ordered.desc()).paginate(page=page_unapproved, per_page=per_page, error_out=False)
    
    denied_orders_query = db.session.query(Order, DrugOrder.denyreason).join(DrugOrder, Order.id == DrugOrder.order_id).filter(DrugOrder.prescription_approved == False).group_by(Order.id).order_by(DrugOrder.date_ordered.desc()).paginate(page=page_denied, per_page=per_page, error_out=False)
    denied_orders = [setattr(order, 'denyreason', denyreason) or order for order, denyreason in denied_orders_query.items]
    
    # Group by drugorder id and calculate the total quantity for each drugorder
    drug_orders = db.session.query(
        DrugOrder.id,
        func.sum(DrugOrder.quantity).label('total_quantity')
    ).group_by(DrugOrder.id).all()

    # Pass the sorted lists and drug orders to the template
    return render_template('pharmacistdash.html', unapproved_prescriptions=unapproved_prescriptions, approved_orders=approved_orders, denied_orders=denied_orders, drug_orders=drug_orders, page_unapproved=page_unapproved, page_approved=page_approved, page_denied=page_denied)

def send_email(to_address, subject, message):
    # setup the parameters of the message
    from_address = 'drhansgruber2911@gmail.com'
    password = 'fifm plgj bbxc infw'  # your email password

    # setup the MIME
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    #create server
    server = smtplib.SMTP('smtp.gmail.com: 587')

    server.starttls()

    # Login Credentials for sending the mail
    server.login(msg['From'], password)

    # send the message via the server.
    server.sendmail(msg['From'], msg['To'], msg.as_string())

    server.quit()

@app.route('/review_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def review_order(order_id):
    # Fetch the order from the database
    order = db.session.get(Order, order_id)
    drug_order = DrugOrder.query.filter_by(order_id=order.id).first()

    # If the order doesn't exist, redirect to a different page or show an error
    if order is None:
        flash('Order not found', 'error')
        return redirect(url_for('pharmacistdash'))

    # Check if the form is submitted
    if request.method == 'POST':
        # Update the order status based on the form data
        status = request.form.get('status')
        deny_reason = request.form.get('denyReason')  # Get the deny reason from the form data

        # Create a dictionary to store the drug orders by index
        drug_orders = {}

        # Iterate over the form data
        for key in request.form:
            # Check if the key starts with 'drug_orders-' which indicates it's a drug order field
            if key.startswith('drug_orders-'):
                # Extract the drug_order_id, field name and value
                _, drug_order_id, field = key.split('-')
                drug_order_id = int(drug_order_id)  # Convert drug_order_id to integer
                value = request.form[key]

                # If the field is 'quantity', only convert to int if value is not an empty string
                if field == 'quantity':
                    if value != '':
                        value = int(value)
                    else:
                        value = None

                # Get the drug order for this drug_order_id
                if drug_order_id not in drug_orders:
                    # Check if this is a new drug order or an existing one
                    existing_order = db.session.get(DrugOrder, drug_order_id)
                    if existing_order is not None:
                        # This is an existing drug order, so use it
                        drug_orders[drug_order_id] = existing_order
                    else:
                        # This is a new drug order, so create a new DrugOrder instance
                        drug_orders[drug_order_id] = DrugOrder(order_id=order_id, date_ordered=datetime.now(timezone.utc))

                drug_order = drug_orders[drug_order_id]

                # Update the corresponding field
                if field == 'name':
                    # Check if the value is an integer (drug id)
                    if value.isdigit():
                        drug = db.session.get(Drug, int(value))
                        if drug is not None:
                            drug_order.drug_id = drug.id
                    else:
                        # The value is a string (drug name)
                        drug = Drug.query.filter_by(name=value).first()
                        if drug is not None:
                            drug_order.drug_id = drug.id
                elif field == 'quantity' and value is not None:
                    drug_order.quantity = int(value)
                elif field == 'refills':
                    drug_order.refills = int(value)

                # Update the prescription_approved status and deny reason
                base_url = request.url_root  # This will give you the base URL of your app

                if status == 'approved' and not drug_order.prescription_approved:
                    drug_order.prescription_approved = True
                    drug_order.denyreason = None  # Clear the deny reason if the order is approved
                    if order.user is not None:
                        send_email(order.user.email, "Prescription Approved", 'Your prescription has been approved. Please proceed to <a href="' + base_url + 'orders">payment</a>.')
                    else:
                        print(f"Order {order.id} has no associated user.")
                elif status == 'denied' and drug_order.prescription_approved is not False:
                    drug_order.prescription_approved = False
                    drug_order.denyreason = deny_reason  # Set the deny reason if the order is denied
                    if order.user is not None:
                        send_email(order.user.email, "Prescription Denied", 'Your prescription has been denied. Reason: ' + deny_reason + '. Check your <a href="' + base_url + 'orders">orders</a> for more details.')
                    else:
                        print(f"Order {order.id} has no associated user.")

        # Add all new drug orders to the session
        for drug_order in drug_orders.values():
            db.session.add(drug_order)

        try:
            db.session.commit()
            print('Update successful')
        except Exception as e:
            print('Update failed:', e)
            db.session.rollback()

        return redirect(url_for('pharmacistdash'))

    # Render the review_order template
    drug_orders = order.items
    drugs = Drug.query.all()
    return render_template('review_order.html', order=order, drug_orders=drug_orders, drugs=drugs, drug_order=drug_order)

@app.route('/track', methods=['GET'])
@login_required
def track():
    order_id = request.args.get('order_id', default = 1, type = int)
    return render_template('track.html', order_id=order_id)

# Function to calculate total payment
def calculate_total_payment(order):
    return sum(item.drug.price * item.quantity for item in order.items)

# Orders route
@app.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).join(DrugOrder).order_by(DrugOrder.date_ordered.desc()).all()
    return render_template('orders.html', orders=orders, calculate_total_payment=calculate_total_payment)

@app.route('/getDenyReason', methods=['POST'])
def get_deny_reason():
    data = request.get_json()
    order_id = data.get('orderId')

    if order_id is None:
        return jsonify({'success': False, 'error': 'No orderId provided'}), 400

    drug_order = db.session.get(DrugOrder, order_id)

    if drug_order is None:
        return jsonify({'success': False, 'error': 'No order found with this id'}), 404

    return jsonify({'success': True, 'denyReason': drug_order.denyreason})

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    drug_order_id = data.get('orderId')

    if drug_order_id is None:
        return jsonify(success=False, error='No order ID provided'), 400

    # Get the DrugOrder with the provided id
    drug_order = db.session.get(DrugOrder, drug_order_id)

    if drug_order is None:
        return jsonify(success=False, error='No order found with this ID'), 404

    # Get the Order of the DrugOrder
    order = drug_order.order

    # Mark all drug_orders in the order as paid
    for do in order.items:
        do.paid = True

    db.session.commit()

    return jsonify(success=True)

@app.route('/payrefill', methods=['POST'])
def payrefill():
    data = request.get_json()
    order_id = data.get('orderId')

    if order_id is None:
        return jsonify(success=False, error='No order ID provided'), 400

    drug_order = db.session.get(DrugOrder, order_id)

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
    form = SupportForm()
    if form.validate_on_submit():
        # Logic to handle support queries
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('support'))
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in the {getattr(form, field).label.text} field - {error}", 'error')
    return render_template("support.html", form=form)

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

class Namespace:
    def __init__(self):
        self.unpaid_approved_count = 0

ns = Namespace()

# Dashboard Route
@app.route("/dashboard")
@login_required
def dashboard():
    total_unapproved_count = 0  # Define total_unapproved_count here
    denied_count = 0  # Define denied_count here
    unpaid_approved_count = 0  # Define unpaid_approved_count here
    if current_user.is_authenticated:
        if current_user.role_id == 1:  # if the user is a pharmacist
            # Fetch all unique order_ids where prescription_approved is None
            drugorders = DrugOrder.query.filter(DrugOrder.prescription_approved == None).all()
            unique_order_ids = DrugOrder.query.with_entities(distinct(DrugOrder.order_id)).filter(DrugOrder.prescription_approved == None).all()
            total_unapproved_count = len(unique_order_ids)  # Update total_unapproved_count here

        else:  # for other users
            orders = Order.query.filter_by(user_id=current_user.id).all()
            drugorders = [drugorder for order in orders for drugorder in order.items]
            unpaid_approved_count = db.session.query(DrugOrder.order_id).join(Order).filter(
                DrugOrder.prescription_approved == True,
                DrugOrder.paid == False,
                Order.user_id == current_user.id
            ).distinct().count()
            unique_unapproved_order_ids = list(set([drugorder.order_id for drugorder in drugorders if drugorder.prescription_approved == None]))

            # Count the number of unique unpaid approved and unapproved prescriptions
            total_unapproved_count = len(unique_unapproved_order_ids)  # Update total_unapproved_count here

            # Count the number of unique denied prescriptions
            unique_denied_order_ids = list(set([drugorder.order_id for drugorder in drugorders if drugorder.prescription_approved == False]))
            denied_count = len(unique_denied_order_ids)  # Update denied_count here

        return render_template('dashboard.html', title='Dashboard', name=current_user.name, email=current_user.email, drugorders=drugorders, unpaid_approved_count=unpaid_approved_count, total_unapproved_count=total_unapproved_count, denied_count=denied_count)
    else:
        return redirect(url_for('login'))
    
# User details route
def format_phone(phone):
    if phone is None:
        raise TypeError("Phone number cannot be None")
    phone = phone.replace("-", "")  # remove any existing dashes
    phone = "{}-{}-{}".format(phone[:3], phone[3:6], phone[6:])  # insert dashes
    return phone

@app.route('/userdetails', methods=['GET', 'POST'])
@login_required
def userdetails():
    form = UserUpdateForm()

    if form.validate_on_submit(): # pragma: no cover
        if bcrypt.check_password_hash(current_user.password, form.current_password.data):
            current_user.address = form.address.data
            current_user.phn = form.phn.data

            # Format phone number with dashes
            current_user.phone = format_phone(form.phone.data)

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
