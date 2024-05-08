from app import app
from db import db
from models import Drug, Order, DrugOrder, User
import csv 
import random
from sqlalchemy.sql import func
from passlib.hash import scrypt

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
        user = User(username=name, email=f"{name}@example.com", password=hashed_password, phone=phone)
        db.session.add(user)

    # Import drugs (assuming similar structure for drugs.csv)
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

# Create a specified number of random orders
def create_random_orders(num_users):
  with app.app_context():
    for _ in range(num_users):
      user_stmt = db.select(User).order_by(func.random()).limit(1)
      user = db.session.execute(user_stmt).scalar()

      # Generate random number of orders between 2 and 5
      num_orders = random.randint(2, 5)
      for _ in range(num_orders):
        order = Order(user=user)
        db.session.add(order)

        drug_stmt = db.select(Drug).order_by(func.random()).limit(1)
        drug = db.session.execute(drug_stmt).scalar()
        rand_qty = random.randint(10, 20)

        association = DrugOrder(order=order, drug=drug, quantity=rand_qty)
        db.session.add(association)

      db.session.commit()

if __name__ == "__main__":
    drop_tables()
    create_tables()
    import_data()
    create_random_orders(10)
