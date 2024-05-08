from sqlalchemy import Boolean, Float, Numeric, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from db import db
from datetime import datetime

# Define the User model (combines User and Customer)
class User(db.Model):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(128), nullable=False)
  address = db.Column(db.String(255), nullable=True)
  phone = db.Column(db.String(20))

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
      "password": "********", 
      "email": self.email,
      "address": self.address,
      "phone": self.phone,
    }

  orders = relationship('Order', backref='user')  # User can have many Orders

# Define the Drug model (remains unchanged)
class Drug(db.Model):
  id = db.Column(Integer, primary_key=True)
  name = db.Column(String(200), nullable=False, unique=True)
  price = db.Column(db.Numeric(10, 2), nullable=False)
  stock = db.Column(Integer, nullable=False, default=0)  # Assuming a field for available quantity
  items = relationship('DrugOrder', back_populates='drug')

  def to_json(self):
    return {
      "id": self.id,
      "name": self.name,
      "price": self.price,
      "stock": self.stock,
    }

# Define the Order model (using user_id for relationship)
class Order(db.Model):
  id = db.Column(Integer, primary_key=True)
  user_id = db.Column(db.Integer, ForeignKey('users.id'))  # Foreign key to User
  items = relationship('DrugOrder', back_populates='order')

  def to_json(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
      "total": sum([item.drug.price * item.quantity for item in self.items]),
    }

# Define the DrugOrder model (remains unchanged)
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
