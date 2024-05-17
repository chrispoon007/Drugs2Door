from flask import Flask
from app import app

# Check if the home path returns a 200 status code
def test_home():
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200 

# Check if a nonexistent path returns a 404 status code
def test_home_not_found():
    with app.test_client() as client:
        response = client.get('/nonexistent_route')
        assert response.status_code == 404