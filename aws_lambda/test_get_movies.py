import json
from get_movies import lambda_handler


results = lambda_handler({}, {})
output = json.loads(results['body'])
length = len(output)
print(f"{length=}\n{output[:5]=}")
