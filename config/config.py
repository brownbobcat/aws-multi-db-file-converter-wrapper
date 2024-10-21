def get_db_config(db_type):
    if db_type == 'mysql':
        return {
            'host': 'database-2.c1m2gemc8uom.us-east-1.rds.amazonaws.com',
            'user': 'admin',
            'password': 'nirmitdb',
            'database': 'database-2'
        }
    elif db_type == 'dynamodb':
        return {}  # DynamoDB does not require additional config if using default
    elif db_type == 'neptune':
        return {'neptune_endpoint': 'db-neptune.cluster-c1m2gemc8uom.us-east-1.neptune.amazonaws.com'}
    elif db_type == 'documentdb':
        return {
            'uri': 'mongodb://root:rootroot77@Database-2-577638360912.us-east-1.docdb-elastic.amazonaws.com:27017/?ssl=true',
            'database': 'Database-2'
        }
    else:
        raise ValueError("Unsupported DB type")

