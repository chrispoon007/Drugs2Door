from app import app
from db import db
from models import Customer, Drug, Order, OrderHistory
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


if __name__ == "__main__":
    drop_tables()
    create_tables()
