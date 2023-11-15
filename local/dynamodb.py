import boto3


def get_item(ind=1):
	# Connect to DynamoDB table
	dynamodb = dynamo_connect()
	table_name = 'movies'
	table = dynamodb.Table(table_name)

	item = table.get_item(
		Key={'ind': ind},
		ProjectionExpression='ind, title, overview',
	)

	print(item)


def delete_table(table_name):
	# Connect to DynamoDB table
	dynamodb = dynamo_connect()
	table_name = 'movies'
	table = dynamodb.Table(table_name)
	table.delete()


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
	#delete_table('movies')
	get_item('12')
