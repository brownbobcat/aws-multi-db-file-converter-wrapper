# Database Converter Project

This project is a Flask-based application that allows users to upload CSV files and insert data into various database systems, including **MySQL (RDS)**, **DynamoDB**, **Amazon Neptune**, and **DocumentDB**. The data is cleaned before being inserted, and database-specific operations are executed.

---

## Features

- **CSV Upload**: Upload CSV files via the web interface.
- **Data Cleaning**: Automatic data cleaning and validation.
- **Multiple Database Support**:
  - MySQL (RDS)
  - DynamoDB
  - Amazon Neptune
  - DocumentDB
- **Dynamic Table Creation**: For MySQL, tables are created dynamically based on the CSV schema.
- **UUID Generation**: For DynamoDB, the system generates unique UUIDs for primary keys when they are missing.

---

## Prerequisites

Make sure to install the following dependencies before you run the application:

- Python 3.x
- Flask
- pandas
- boto3
- pymysql
- pymongo
- gremlin-python

### Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

You will need to configure database credentials in the `config.py` file for the respective databases you're working with. Here's an example configuration structure:

```python
def get_db_config(db_type):
    if db_type == 'mysql':
        return {
            'host': 'your-rds-endpoint',
            'user': 'your-db-username',
            'password': 'your-db-password',
            'database': 'your-db-name'
        }
    elif db_type == 'dynamodb':
        return {}  # No additional config needed for DynamoDB
    elif db_type == 'neptune':
        return {'neptune_endpoint': 'your-neptune-endpoint'}
    elif db_type == 'documentdb':
        return {
            'uri': 'mongodb://your-docdb-uri',
            'database': 'your-docdb-database-name'
        }
    else:
        raise ValueError("Unsupported DB type")
```
## Usage

### Start the application

```bash
python3 app.py
```

## Access the application

Go to `http://localhost:5000` to use the web interface for uploading CSV files and selecting your target database.

## Database Details

### MySQL (RDS)

- **Table Creation**: If the table does not exist, it will be created based on the CSV schema.
- **Data Insertion**: Rows are inserted into the corresponding table.

```python
def create_table_if_not_exists(cursor, table_name, df):
    columns = []
    for col in df.columns:
        mysql_type = infer_mysql_type(df[col])
        columns.append(f"`{col}` {mysql_type}")
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        {', '.join(columns)}
    );
    """
    cursor.execute(create_table_query)

```
## DynamoDB

- **UUID Generation**: Generates a unique ID for rows that don't have a primary key.
- **Data Insertion**: Inserts each row as an item in a DynamoDB table.

```python
def insert_to_dynamodb(df, table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    for _, row in df.iterrows():
        # Ensure that the 'id' key exists; generate a UUID if missing
        item = {col: str(row[col]) for col in df.columns}
        if 'id' not in item:
            item['id'] = str(uuid.uuid4())  # Generate a unique ID

        try:
            table.put_item(Item=item)
        except Exception as e:
            print(f"Error occurred: {e}")

```
## Amazon Neptune

**Vertex Insertion**: Converts CSV rows into Gremlin queries and inserts them as vertices into Amazon Neptune.

```python
def convert_csv_to_neptune(df, neptune_endpoint):
    gremlin_client = client.Client(
        f'wss://{neptune_endpoint}:8182/gremlin',
        'g',
        message_serializer=serializer.GraphSONSerializersV2d0()
    )

    try:
        for _, row in df.iterrows():
            properties = [f".property('{col}', '{sanitize_value(row[col])}')" for col in df.columns]
            vertex_query = f"g.addV('vertex')" + "".join(properties)
            print(f"Executing vertex query: {vertex_query}")
            gremlin_client.submitAsync(vertex_query)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        gremlin_client.close()
```
## DocumentDB

**Data Insertion**: Inserts each row of the CSV as a document in a MongoDB-compatible DocumentDB collection.

```python
def insert_to_documentdb(df, documentdb_config, collection_name):
    client = MongoClient(documentdb_config['uri'])
    db = client[documentdb_config['database']]
    collection = db[collection_name]
    for _, row in df.iterrows():
        collection.insert_one(row.to_dict())
```

## Validation

After completing the installation and configuration, you can validate that each component of the project is working correctly by following these steps:

### 1. MySQL (RDS) Validation

To check if the data has been successfully inserted into your MySQL database:

1. Connect to your MySQL database using the MySQL client or any MySQL workbench:

    ```bash
    mysql -h your-rds-endpoint -u your-db-username -p
    ```

2. After logging in, select the database and check if the data has been inserted into the table:

    ```sql
    USE your-db-name;
    SELECT * FROM your-table-name LIMIT 10;
    ```

   You should see the rows from your CSV file in the output.

### 2. DynamoDB Validation

To validate that the data has been inserted into DynamoDB:

1. Go to the **AWS Management Console**.
2. Navigate to **DynamoDB** and select the table that was used in the project.
3. Click on the **Items** tab to view the data inserted into the table.
4. Ensure that each row from your CSV file appears as an item in the DynamoDB table.

Alternatively, you can use the AWS CLI to query DynamoDB:

```bash
aws dynamodb scan --table-name your-dynamodb-table-name
```

### 3. Amazon Neptune Validation

To verify that data has been inserted into Amazon Neptune:

1. Connect to the Neptune DB using Gremlin queries:

    ```bash
    aws neptune-query gremlin --endpoint your-neptune-endpoint --query "g.V().limit(5)"
    ```

    This query retrieves the first 5 vertices that were inserted into the database. You should see the data you added from the CSV.

2. Alternatively, you can run a specific query to find a vertex by one of its properties:

    ```bash
    aws neptune-query gremlin --endpoint your-neptune-endpoint --query "g.V().has('vertex', 'property-name', 'property-value')"
    ```

    This will return vertices that match the specific property from your CSV file.

---

### 4. DocumentDB Validation

To check if the data has been inserted into MongoDB-compatible DocumentDB:

1. Use the **MongoDB Shell** to connect to the DocumentDB instance:

    ```bash
    mongo "mongodb://your-docdb-uri"
    ```

2. After connecting, select the database and collection, and then query the data:

    ```bash
    use your-database-name;
    db.your-collection-name.find().limit(10).pretty();
    ```

    You should see the documents corresponding to the rows of your CSV file.

---

### 5. Application Validation

To check that the web application itself is working:

1. Start the Flask app:

    ```bash
    python3 app.py
    ```

2. Open your browser and navigate to the following address:

    ```text
    http://localhost:5000
    ```

3. Upload a sample CSV file and select the database you wish to insert the data into. Ensure that you receive a success message indicating the data was inserted.

4. Follow the respective database validation steps to ensure the data is inserted into the selected database.

---

By following these validation steps, you can confirm that the project components are functioning correctly and the data is being processed and stored in the desired databases.

## Contributing

- **Brown, Nicholas D.**
- **Vemula, Sai Srujan**
- **Nirmit H. Dagli**


Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change. 

Please make sure to update tests as appropriate.
