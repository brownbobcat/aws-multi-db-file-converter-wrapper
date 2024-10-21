from pymysql import connect as mysql_connect
from pymongo import MongoClient
import boto3
import pandas as pd
from gremlin_python.driver import client, serializer
import re
import uuid


def infer_mysql_type(column):
    if pd.api.types.is_integer_dtype(column):
        return "INT"
    elif pd.api.types.is_float_dtype(column):
        return "FLOAT"
    else:
        return "VARCHAR(255)"

def create_table_if_not_exists(cursor, table_name, df):
    columns = []
    for col in df.columns:
        mysql_type = infer_mysql_type(df[col])
        columns.append(f"`{col}` {mysql_type}")
    columns_def = ", ".join(columns)
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        {columns_def}
    );
    """
    cursor.execute(create_table_query)

def insert_to_rds_mysql(df, mysql_config, table_name):
    connection = mysql_connect(
        host=mysql_config['host'],
        user=mysql_config['user'],
        password=mysql_config['password'],
        database=mysql_config['database']
    )
    cursor = connection.cursor()

    create_table_if_not_exists(cursor, table_name, df)
    columns = ", ".join([f"`{col}`" for col in df.columns])
    placeholders = ", ".join(['%s'] * len(df.columns))
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    for _, row in df.iterrows():
        cursor.execute(insert_query, tuple(row))

    connection.commit()
    connection.close()

def create_dynamodb_table(table_name):
    dynamodb = boto3.client('dynamodb')
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        return True
    except Exception as e:
        print(f"Error creating table: {str(e)}")
        return False

def insert_to_dynamodb(df, table_name):
    if not create_dynamodb_table(table_name):
        raise Exception(f"Failed to create new DynamoDB table: {table_name}")

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    df = df.fillna('')
    df = df.replace([float('inf'), -float('inf')], 0)

    if 'id' not in df.columns:
        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]

    success_count = 0
    error_count = 0

    with table.batch_writer() as batch:
        for _, row in df.iterrows():
            try:
                item = {'id': str(row.get('id', uuid.uuid4()))}
                
                for key, value in row.items():
                    if key == 'id':
                        continue
                    if pd.isnull(value):
                        continue
                    if isinstance(value, float):
                        item[key] = Decimal(str(value))
                    else:
                        item[key] = str(value)

                batch.put_item(Item=item)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing item: {str(e)}")

    time.sleep(5)  # Allow time for eventual consistency
    
    try:
        response = table.scan(Select='COUNT')
        actual_count = response['Count']
        if actual_count != success_count:
            print(f"WARNING: Mismatch between inserted items ({success_count}) and actual items in table ({actual_count})")
    except Exception as e:
        print(f"Error during verification scan: {str(e)}")
    
    return success_count, error_count

def insert_to_documentdb(df, documentdb_config, collection_name):
    client = MongoClient(documentdb_config['uri'])
    db = client[documentdb_config['database']]
    collection = db[collection_name]
    for _, row in df.iterrows():
        collection.insert_one(row.to_dict())

def sanitize_value(value):
    if isinstance(value, str):
        return re.sub(r"'", "\\'", value)
    return value

def convert_csv_to_neptune(df, neptune_endpoint):
    """
    Converts CSV data into Gremlin queries and inserts vertices and edges into Amazon Neptune.
    """
    gremlin_client = client.Client(
        f'wss://{neptune_endpoint}:8182/gremlin',
        'g',
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

    try:
        # Step 1: Insert vertices (automatically handling any CSV structure)
        for _, row in df.iterrows():
            # Dynamically chain the properties
            properties = [f".property('{col}', '{sanitize_value(row[col])}')" for col in df.columns]
            vertex_query = f"g.addV('vertex')" + "".join(properties)  # Corrected: Now the properties are joined properly.

            print(f"Executing vertex query: {vertex_query}")  # Debugging line
            gremlin_client.submitAsync(vertex_query)

        # Step 2: If edges are provided, create edges (assuming a CSV structure where edges are specified)
        if 'source_vertex' in df.columns and 'target_vertex' in df.columns:
            for _, row in df.iterrows():
                edge_query = f"g.V().has('vertex', 'id', '{sanitize_value(row['source_vertex'])}').addE('edge').to(g.V().has('vertex', 'id', '{sanitize_value(row['target_vertex'])}'))"
                print(f"Executing edge query: {edge_query}")  # Debugging line
                gremlin_client.submitAsync(edge_query)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the Gremlin connection
        gremlin_client.close()

def insert_data(df, db_type, config, table_name):
    if db_type == 'mysql':
        insert_to_rds_mysql(df, config, table_name)
    elif db_type == 'dynamodb':
        insert_to_dynamodb(df, table_name)
    elif db_type == 'neptune':
        convert_csv_to_neptune(df, config['neptune_endpoint'])
    elif db_type == 'documentdb':
        insert_to_documentdb(df, config, table_name)
    else:
        raise ValueError("Unsupported DB type")

