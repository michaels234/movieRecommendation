from flask import Flask, request, render_template, jsonify
from database import DataBase

app = Flask(__name__)
db = DataBase()


@app.route('/')
def home():
	return render_template('index.html', context={'prediction_text': 'Not Yet'})


@app.route('/movies', methods=['GET'])
def movies():
	title_query = request.args.get('title').replace('"', '')  # get title_query without "
	# return list of title + year options that contain title_query from db
	options = db.list_titles_from_query(title_query)
	return jsonify(options)


@app.route('/predict', methods=['GET'])
def predict():
	ind = request.args.get('ind')
	movie_list = db.list_similar_movies_from_ind(ind)
	return jsonify(list_to_output(movie_list))


def list_to_output(movie_list):
	output = 'SOURCE MOVIE:' + '\nTITLE: ' + movie_list[0]['title'] + '\nDESCRIPTION: ' + movie_list[0]['overview'] + '\n\nRECOMMENDATIONS:'
	for i in range(1, 11):
		output += '\n\n#' + str(i) + '\nTITLE: ' + movie_list[i]['title'] + '\nDESCRIPTION: ' + movie_list[i]['overview']
	return {'prediction_text': output}


if __name__ == "__main__":
	app.run(debug=True,host='0.0.0.0',port=8080)
