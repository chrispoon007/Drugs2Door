from app import app
from db import db
from models import Drug, Order, DrugOrder, User, Role
import csv 
import random
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import bcrypt

# Drop all tables in the database
def drop_tables():
    with app.app_context():
        db.drop_all()

# Create all tables in the database
def create_tables():
    with app.app_context():
        db.create_all()

def import_data():
  """
  Imports users and drugs from CSV files.
  """
  with app.app_context():
    # Check if the role with id of 2 exists
    user_role = db.session.get(Role, 2)

    # If the role doesn't exist, create it
    if user_role is None:
        user_role = Role(id=2, name='user')
        db.session.add(user_role)
        db.session.commit()

    # Import users
    with open('./data/users.csv', 'r') as f:
      reader = csv.DictReader(f)
      next(reader)
      for row in reader:
        name = row["name"]
        phone = row["phone"]
        password = "123123123"
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        first_name, last_name = name.split()
        email = f"{first_name[0]}{last_name}@example.com"
        phn = ''.join(random.choice('0123456789') for i in range(10))
        user = User(name=name, email=email, password=hashed_password, phone=phone, phn=phn, role_id=user_role.id)

        db.session.add(user)

    # Commit the changes to the database
    db.session.commit()
    
    # Import drugs
    with open('./data/drugs.csv', 'r') as f:
      reader = csv.DictReader(f)
      next(reader)
      for row in reader:
        if row["price"] == '':
          continue  
        name = row["name"]
        price = float(row["price"])
        available = int(30)
        drug = Drug(name=name, price=price)
        db.session.add(drug)

    db.session.commit()


# Create a specified number of random orders
def create_random_orders():
  with app.app_context():
    users = User.query.join(Role).filter(Role.name != 'Pharmacist').all()  # only get users who are not pharmacists
    for user in users:

      num_orders = random.randint(2, 5)
      for _ in range(num_orders):
        order = Order(user=user)
        db.session.add(order)

        drug_stmt = db.select(Drug).order_by(func.random()).limit(1)
        drug = db.session.execute(drug_stmt).scalar()
        rand_qty = random.randint(50, 200)

        # Generate random dates for date_ordered and date_delivered
        date_ordered = datetime.now() - timedelta(days=random.randint(1, 60))
        date_delivered = date_ordered + timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None

        # If the order has been delivered, then the prescription must be approved and the order must be paid
        prescription_approved = None
        if date_delivered:
            prescription_approved = True
            paid = True
        else:
            prescription_approved = random.choice([True, False, None])
            paid = False if prescription_approved is None else random.choice([True, False])

        association = DrugOrder(order=order, drug=drug, quantity=rand_qty, date_ordered=date_ordered, date_delivered=date_delivered, prescription_approved=prescription_approved, paid=paid)
        db.session.add(association)

      db.session.commit()

def create_pharmacist():
    with app.app_context():
        pharmacist_role = db.session.get(Role, 1)
        if pharmacist_role is None:
            pharmacist_role = Role(id=1, name='Pharmacist')
            db.session.add(pharmacist_role)
            db.session.commit()
        elif pharmacist_role.name != 'Pharmacist':
            pharmacist_role.name = 'Pharmacist'
            db.session.commit()

        password = "123123123"
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        pharmacist = User(name='Hans Gruber', email='HGruber@example.com', password=hashed_password, phone='604-456-7890', phn='6666666666', role=pharmacist_role)
        db.session.add(pharmacist)
        db.session.commit()

if __name__ == "__main__":
    drop_tables()
    create_tables()
    import_data()
    create_random_orders()
    create_pharmacist() 
