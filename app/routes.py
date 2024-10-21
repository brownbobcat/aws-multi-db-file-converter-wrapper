from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import pandas as pd
from app import app
from app.insert_handlers import insert_data
from app.clean_data import clean_data
from config.config import get_db_config
from app.convert_to_csv import txt_to_csv, json_to_csv, xml_to_csv

# Define upload folder for storing temporary files
UPLOAD_FOLDER = '/home/ec2-user/db_converter_project/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def upload_file():
    print("Rendering upload page")
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    print("File upload initiated")

    # Check if the file is in the request
    if 'file' not in request.files:
        flash('No file part')
        print("No file part found in request")
        return redirect(request.url)

    file = request.files['file']
    print(f"File received: {file.filename}")

    # Check if a file was selected
    if file.filename == '':
        flash('No selected file')
        print("No file selected by user")
        return redirect(request.url)

    # Secure the filename and save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    print(f"File saved at: {file_path}")

    # Extract the selected database type and table/collection name
    db_type = request.form.get('db_type')
    table_name = request.form.get('table_name')
    print(f"Selected DB Type: {db_type}")
    print(f"Table/Collection Name: {table_name}")

    try:
        # Determine file extension and convert to CSV if needed
        csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted.csv')

        if filename.endswith('.csv'):
            print(f"File is already a CSV")
            csv_file_path = file_path  # No conversion needed
        elif filename.endswith('.txt'):
            print("Converting TXT to CSV")
            txt_to_csv(file_path, csv_file_path)
        elif filename.endswith('.json'):
            print("Converting JSON to CSV")
            json_to_csv(file_path, csv_file_path)
        elif filename.endswith('.xml'):
            print("Converting XML to CSV")
            xml_to_csv(file_path, csv_file_path)
        else:
            flash('Unsupported file format')
            print("Unsupported file format")
            return redirect(request.url)

        # Read the CSV file into a DataFrame
        print(f"Reading {csv_file_path} as CSV")
        df = pd.read_csv(csv_file_path)

        # Clean the data before inserting into the DB
        print("Cleaning data")
        df = clean_data(df)
        print("Data cleaned successfully")

        # Insert the data into the selected database
        print(f"Inserting data into {db_type}")
        config = get_db_config(db_type)
        insert_data(df, db_type, config, table_name)

        print(f"Data successfully inserted into {db_type} in table/collection {table_name}")
        flash(f'Data successfully inserted into {db_type} in table/collection {table_name}')
        return redirect(url_for('upload_file'))

    except Exception as e:
        flash(f"An error occurred: {e}")
        print(f"Error occurred: {e}")
        return redirect(request.url)
