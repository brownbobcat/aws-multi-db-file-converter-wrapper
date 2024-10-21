import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def get_db_config(db_type):
    if db_type == 'mysql':
        return {
            'host': os.getenv('MYSQL_HOST'),
            'user': os.getenv('MYSQL_USER'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE')
        }
    elif db_type == 'dynamodb':
        return {}  # DynamoDB does not require additional config if using default
    elif db_type == 'neptune':
        return {'neptune_endpoint': os.getenv('NEPTUNE_ENDPOINT')}
    elif db_type == 'documentdb':
        return {
            'uri': os.getenv('DOCUMENTDB_URI'),
            'database': os.getenv('DOCUMENTDB_DATABASE')
        }
    else:
        raise ValueError("Unsupported DB type")
    
    