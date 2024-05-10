from app import app
from db import db
from models import Drug, Order, DrugOrder, User
import csv 
import random
from sqlalchemy.sql import func
from passlib.hash import scrypt
from datetime import datetime, timedelta

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
    # Import users
    with open('./data/users.csv', 'r') as f:
      reader = csv.DictReader(f)
      next(reader)
      for row in reader:
        name = row["name"]
        phone = row["phone"]
        hashed_password = scrypt.encrypt("123123123")
        first_name, last_name = name.split()
        email = f"{first_name[0]}{last_name}@example.com"
        user = User(name=name, email=email, password=hashed_password, phone=phone)
        db.session.add(user)

    # Import drugs
    with open('./data/drugs.csv', 'r') as f:
      reader = csv.DictReader(f)
      next(reader)
      for row in reader:
        if row["price"] == '':
          continue  # Skip rows with empty price
        name = row["name"]
        price = float(row["price"])
        available = int(30)
        drug = Drug(name=name, price=price)
        db.session.add(drug)

    db.session.commit()

from datetime import datetime, timedelta
import random

# Create a specified number of random orders
def create_random_orders():
  with app.app_context():
    users = User.query.all() 
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

        # Randomly decide if prescription is approved
        prescription_approved = random.choice([True, False])

        association = DrugOrder(order=order, drug=drug, quantity=rand_qty, date_ordered=date_ordered, date_delivered=date_delivered, prescription_approved=prescription_approved)
        db.session.add(association)

      db.session.commit()

if __name__ == "__main__":
    drop_tables()
    create_tables()
    import_data()
    create_random_orders()
