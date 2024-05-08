from app import app
from db import db
from models import Customer, Drug, Order, DrugOrder
import csv 
import random
from sqlalchemy.sql import func

# Drop all tables in the database
def drop_tables():
    with app.app_context():
        db.drop_all()

# Create all tables in the database
def create_tables():
    with app.app_context():
        db.create_all()

# Import customers from a CSV file
def import_customers():
    with app.app_context():
        with open('./data/customers.csv', 'r') as f:
            reader = csv.DictReader(f) 
            next(reader) 
            for row in reader:
                balance = int(100)
                customer = Customer(name=row["name"], phone=row["phone"], balance=balance) 
                db.session.add(customer)
        db.session.commit()

# Import drugs from a CSV file
def import_drugs():  # Renamed function
    with app.app_context():
        with open('./data/drugs.csv', 'r') as f:  # Assuming you have a similar CSV file for drugs
            reader = csv.DictReader(f) 
            next(reader) 
            for row in reader:
                if row["price"] == '':
                    continue  # Skip this row if the price is an empty string
                available = int(30)
                drug = Drug(name=row["name"], price=row["price"], stock=available)  # Renamed variable and model
                db.session.add(drug)
        db.session.commit()


# Create a specified number of random orders
def create_random_orders(num_orders):
    with app.app_context():
        for _ in range(num_orders):
            cust_stmt = db.select(Customer).order_by(func.random()).limit(1)
            customer = db.session.execute(cust_stmt).scalar()

            order = Order(customer=customer)
            db.session.add(order)

            drug_stmt = db.select(Drug).order_by(func.random()).limit(1)  # Renamed variable and model
            drug = db.session.execute(drug_stmt).scalar()  # Renamed variable
            rand_qty = random.randint(10, 20)

            association_1 = DrugOrder(order=order, drug=drug, quantity=rand_qty)  # Renamed model
            db.session.add(association_1)

            drug_stmt = db.select(Drug).order_by(func.random()).limit(1)  # Renamed variable and model
            drug = db.session.execute(drug_stmt).scalar()  # Renamed variable
            rand_qty = random.randint(10, 20)

            association_2 = DrugOrder(order=order, drug=drug, quantity=rand_qty)  # Renamed model
            db.session.add(association_2)

        db.session.commit()

if __name__ == "__main__":
    drop_tables()
    create_tables()
    import_customers()
    import_drugs()
    create_random_orders(10)
