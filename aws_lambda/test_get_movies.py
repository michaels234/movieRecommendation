from get_movies import lambda_handler


results = lambda_handler({}, {})
print(f"{len(results)=}\n{results=}")