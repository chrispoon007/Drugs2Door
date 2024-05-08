from sqlalchemy import Boolean, Float, Numeric, ForeignKey, Integer, String, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from db import db
from datetime import datetime
from decimal import Decimal

# Define the User model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    @property
    def is_active(self):
        # Assuming a user is active if they have a username
        return bool(self.username)

    @property
    def is_authenticated(self):
        # Assuming a user is authenticated if they have a password
        return bool(self.password)

    @property
    def is_anonymous(self):
        # Assuming a user is not anonymous if they have a username
        return not bool(self.username)

    def get_id(self):
        return str(self.id)

    def to_json(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }



# Define the Customer model
class Customer(db.Model):
  id = db.Column(Integer, primary_key=True)
  name = db.Column(String(200), nullable=False, unique=True)
  phone = db.Column(String(20), nullable=False)
  balance = db.Column(DECIMAL(10,2), nullable=False, default=0)
  orders = relationship('Order')

  def to_json(self):
    return {
      "id": self.id,
      "name": self.name,
      "phone": self.phone,
      "balance": self.balance,
    }

# Define the Drug model
class Drug(db.Model):
  id = db.Column(Integer, primary_key=True)
  name = db.Column(String(200), nullable=False, unique=True)
  price = db.Column(DECIMAL(10,2), nullable=False)
  stock = db.Column(Integer, nullable=False, default=0)  # Assuming a field for available quantity
  items = relationship('DrugOrder', back_populates='drug')

  def to_json(self):
    return {
      "id": self.id,
      "name": self.name,
      "price": self.price,
      "stock": self.stock,
    }

# Define the Order model
class Order(db.Model):
  id = db.Column(Integer, primary_key=True)
  customer_id = db.Column(db.Integer, ForeignKey("customer.id"))
  customer = relationship("Customer", back_populates="orders")
  items = relationship('DrugOrder', back_populates='order')

  def to_json(self):
    return {
      "id": self.id,
      "customer_id": self.customer_id,
      "total": sum([item.drug.price * item.quantity for item in self.items]),
    }

# Define the DrugOrder model
class DrugOrder(db.Model):
  id = db.Column(Integer, primary_key=True)
  order_id = db.Column(Integer, ForeignKey('order.id'), nullable=False)
  drug_id = db.Column(Integer, ForeignKey('drug.id'), nullable=False)
  quantity = db.Column(Integer, nullable=False)
  drug = relationship('Drug', back_populates='items')
  order = relationship('Order', back_populates='items')

  def to_json(self):
    return {
      "id": self.id,
      "order_id": self.order_id,
      "drug_id": self.drug_id,
      "quantity": self.quantity,
    }
