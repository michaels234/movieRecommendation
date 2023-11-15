import json
import os
import boto3


#@app.route('/predict', methods=['GET'])
def lambda_handler(event, context):
	ind = event['ind']
	movie_list = list_similar_movies_from_ind(ind)
	return {
	    "statusCode": 200,
	    "headers": {
	        "Content-Type": "application/json"
	    },
	    "body": json.dumps(list_to_output(movie_list))
	}


def list_to_output(movie_list):
	output = 'SOURCE MOVIE:' + '\nTITLE: ' + movie_list[0]['title'] + '\nDESCRIPTION: ' + movie_list[0]['overview'] + '\n\nRECOMMENDATIONS:'
	for i in range(1, 11):
		output += '\n\n#' + str(i) + '\nTITLE: ' + movie_list[i]['title'] + '\nDESCRIPTION: ' + movie_list[i]['overview']
	return {'prediction_text': output}


	
def list_similar_movies_from_ind(ind):
	dynamodb = dynamo_connect()
	table_name = 'movies'
	table = dynamodb.Table(table_name)

	response = table.get_item(
		Key={'ind': str(ind)},
		ProjectionExpression='similarity_indices'
	)
	similarity_indices = tuple(response['Item']['similarity_indices'].split(', '))

	items = []
	for i in similarity_indices:
		items.append(table.get_item(
			Key={'ind': i},
			ProjectionExpression='ind, title, overview',
		)['Item'])

	unordered = {str(item['ind']): {'title': item['title'], 'overview': item['overview']} for item in items}
	return [unordered[str(ind)] for ind in similarity_indices]


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
