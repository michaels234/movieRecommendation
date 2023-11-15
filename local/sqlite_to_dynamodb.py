import sqlite3
import boto3


def put_items(num_items=0):
	# Connect to DynamoDB table
	dynamodb = dynamo_connect()
	table_name = 'movies'
	existing_tables = dynamodb.meta.client.list_tables()['TableNames']
	if table_name in existing_tables:
		# If the table exists, load the existing table
		table = dynamodb.Table(table_name)
	else:
		# If the table doesn't exist, create a new table with desired settings
		table = dynamodb.create_table(
			TableName=table_name,
			KeySchema=[
				{
					'AttributeName': 'ind',
					'KeyType': 'HASH'  # Partition key
				}
			],
			AttributeDefinitions=[
				{
					'AttributeName': 'ind',
					'AttributeType': 'S'  # Assuming 'ind' is of type String
				}
				# Add additional AttributeDefinitions if you have more attributes
			],
			BillingMode='PAY_PER_REQUEST',  # On-demand capacity mode
		)

	# Connect to SQLite database
	local_connection = sqlite3.connect('local/movies.db')
	local_cursor = local_connection.cursor()

	# Query SQLite database for data to migrate
	local_cursor.execute('SELECT * FROM movies')
	rows = local_cursor.fetchall()

	# Convert data to format expected by DynamoDB
	# ind INTEGER PRIMARY KEY, title TEXT, clean_title TEXT, year TEXT, overview TEXT, genres TEXT, keywords TEXT, fittable_words TEXT, similarity_indices TEXT
	items = []
	for row in rows:
		item = {
			'ind': str(row[0]),
			'clean_title': str(row[2]),
			'year': str(row[3]),
			'title': str(row[1]),
			'overview': str(row[4]),
			'genres': str(row[5]),
			'keywords': str(row[6]),
			'fittable_words': str(row[7]),
			'similarity_indices': str(row[8]),
		}
		items.append(item)

	# Batch write items to DynamoDB table
	with table.batch_writer() as batch:
		if num_items:
			for item in items[:num_items]:
				batch.put_item(Item=item)
		else:
			for item in items:
				batch.put_item(Item=item)

	# Close connections
	local_cursor.close()
	local_connection.close()


def dynamo_connect():
	endpoint_url = 'http://localhost:8000'
	aws_access_key_id = 'dummy'
	aws_secret_access_key = 'dummy'

	dynamodb_resource = boto3.resource(
		'dynamodb',
		region_name='us-east-1',
		endpoint_url=endpoint_url,
		aws_access_key_id=aws_access_key_id,
		aws_secret_access_key=aws_secret_access_key,
	)

	return dynamodb_resource


if __name__ == "__main__":
	put_items()
