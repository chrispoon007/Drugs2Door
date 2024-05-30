from sqlalchemy import Boolean, Float, Numeric, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from db import db

# Define the Role model
class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    users = relationship('User', backref='role')

# Define the User model
class User(db.Model):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False) 
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(128), nullable=False)
  address = db.Column(db.String(255), nullable=True)
  phone = db.Column(db.String(20))
  phn = db.Column(db.String(120), unique=True, nullable=False)
  role_id = db.Column(db.Integer, db.ForeignKey('roles.id')) 


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
  
  def has_role(self, role_name):
        return self.role.name == role_name

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

class DrugOrder(db.Model):
  id = db.Column(Integer, primary_key=True)
  order_id = db.Column(Integer, ForeignKey('order.id'), nullable=False)
  drug_id = db.Column(Integer, ForeignKey('drug.id'))
  quantity = db.Column(Integer)
  date_ordered = db.Column(DateTime, nullable=False)
  date_delivered = db.Column(DateTime)
  prescription_approved = db.Column(Boolean)  # NULL: not approved yet, True: approved, False: denied
  refills = db.Column(db.Integer, default=0)
  denyreason = db.Column(db.String(255), nullable=True)
  drug = relationship('Drug', back_populates='items')
  order = relationship('Order', back_populates='items')
  image_file = db.Column(db.String(120), nullable=True)
  paid = db.Column(Boolean, default=False, nullable=False)

  def to_json(self):
    return {
      "id": self.id,
      "order_id": self.order_id,
      "drug_id": self.drug_id,
      "quantity": self.quantity,
      "date_ordered": self.date_ordered,
      "date_delivered": self.date_delivered,
      "prescription_approved": self.prescription_approved,
      "refills": self.refills,
      "denyreason": self.denyreason,
      "image_file": self.image_file,
      "paid": self.paid,
    }