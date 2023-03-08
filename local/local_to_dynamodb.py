import sqlite3
import os
import boto3
from dotenv import load_dotenv


load_dotenv()


def put_items(num_items=0):
	# Connect to DynamoDB table
	dynamodb = dynamo_connect()
	table = dynamodb.Table('movies')

	# Connect to local SQLite database
	local_connection = sqlite3.connect('local/movies.db')
	local_cursor = local_connection.cursor()

	# Query local database for data to migrate
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


def delete_items(num_items=0):
	# Connect to DynamoDB table
	dynamodb = dynamo_connect()
	table = dynamodb.Table('movies')

	# Connect to local SQLite database
	local_connection = sqlite3.connect('local/movies.db')
	local_cursor = local_connection.cursor()

	# Query local database for data to migrate
	local_cursor.execute('SELECT * FROM movies')
	rows = local_cursor.fetchall()

	# Convert data to format expected by DynamoDB
	# ind INTEGER PRIMARY KEY, title TEXT, clean_title TEXT, year TEXT, overview TEXT, genres TEXT, keywords TEXT, fittable_words TEXT, similarity_indices TEXT
	items = []
	for row in rows:
		items.append({'ind': str(row[0])})

	# Batch write items to DynamoDB table
	if num_items:
		for item in items[:num_items]:
			table.delete_item(
				TableName='movies',
				Key=item
			)
	else:
		for item in items:
			table.delete_item(
				TableName='movies',
				Key=item
			)

	# Close connections
	local_cursor.close()
	local_connection.close()


def dynamo_connect():
	session = boto3.Session(
		region_name='us-east-1',
		aws_access_key_id=os.environ.get('DYNAMODB_ACCESS_KEY'),
		aws_secret_access_key=os.environ.get('DYNAMODB_SECRET_ACCESS_KEY'),
	)

	return session.resource('dynamodb')


if __name__ == "__main__":
	num_items = 5  # careful, set this to 0 and it will put or delete ALL items (around 5000 currently)
	#put_items(num_items)
	#delete_items(num_items)
