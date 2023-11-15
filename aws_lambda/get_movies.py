import json
import os
import boto3


def lambda_handler(event, context):
	# return list of title + year for all movies in db
	select_response = list_titles()
	return {
	    "statusCode": 200,
	    "headers": {
	        "Content-Type": "application/json"
	    },
	    "body": json.dumps(select_response)
	}


def list_titles():
	dynamodb = dynamo_connect()
	table_name = 'movies'
	table = dynamodb.Table(table_name)

	items = []
	response = table.scan(
		ProjectionExpression='ind, title, #yr',
		ExpressionAttributeNames={'#yr': 'year'}
	)
	items.extend(response['Items'])
	while True:
		if 'LastEvaluatedKey' not in response:
			break
		response = table.scan(
			ProjectionExpression='ind, title, #yr',
			ExpressionAttributeNames={'#yr': 'year'},
			ExclusiveStartKey=response['LastEvaluatedKey']
		)
		items.extend(response['Items'])

	return [{'ind': item['ind'], 'titleYear': item['title'] + f" ({item['year']})"} for item in items]


def dynamo_connect():
	if 'ENV' not in os.environ or ('ENV' in os.environ and os.environ.get('ENV') == 'DEV'):
		# Local Development Environment
		endpoint_url = 'http://localhost:8000'
		aws_access_key_id = 'dummy'
		aws_secret_access_key = 'dummy'
	else:
		# AWS Production Environment
		endpoint_url = None
		aws_access_key_id = None
		aws_secret_access_key = None

	dynamodb_resource = boto3.resource(
		'dynamodb',
		region_name='us-east-1',
		endpoint_url=endpoint_url,
		aws_access_key_id=aws_access_key_id,
		aws_secret_access_key=aws_secret_access_key,
	)

	return dynamodb_resource
