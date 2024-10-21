from flask import Flask
import os

app = Flask(__name__)

# Generate a random secret key (for development use)
app.config['SECRET_KEY'] = os.urandom(24)

# Define the path for file uploads
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

from app import routes

