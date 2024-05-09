from sqlalchemy import Boolean, Float, Numeric, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from db import db
from datetime import datetime

# Define the User model
class User(db.Model):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False) 
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(128), nullable=False)
  address = db.Column(db.String(255), nullable=True)
  phone = db.Column(db.String(20))

  @property
  def is_active(self):
    return bool(self.name)
  @property
  def is_authenticated(self):
    return bool(self.password)

  @property
  def is_anonymous(self):
    return not bool(self.name) 

  def get_id(self):
    return str(self.id)

  def to_json(self):
    return {
      "id": self.id,
      "name": self.name,  
      "password": "********", 
      "email": self.email,
      "address": self.address,
      "phone": self.phone,
    }

  orders = relationship('Order', backref='user')

# Define the Drug model
class Drug(db.Model):
  id = db.Column(Integer, primary_key=True)
  name = db.Column(String(200), nullable=False, unique=True)
  price = db.Column(db.Numeric(10, 2), nullable=False)
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
  user_id = db.Column(db.Integer, ForeignKey('users.id')) 
  items = relationship('DrugOrder', back_populates='order')

  def to_json(self):
    return {
      "id": self.id,
      "user_id": self.user_id,
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
