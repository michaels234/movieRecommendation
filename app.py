from flask import Flask, request, render_template, jsonify
import numpy as np
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
	context = {'prediction_text': 'Not Yet'}
	return render_template('index.html', context=context)


@app.route('/movies', methods=['GET'])
def movies():
	movies = get_movies()
	data = {'movies': movies['original_title'].to_numpy().tolist()}
	return jsonify(data)


@app.route('/predict', methods=['POST'])
def predict():
	movies = get_movies()
	request_data = request.get_json()
	movie = request_data['movie']
	similarity_distance = np.load('similarity_distance.npy')
	output = give_recomendations(movie, similarity_distance, movies)
	data = {'prediction_text': output}
	return jsonify(data)


def get_movies():
	print('GET MOVIES')
	pd.options.display.max_colwidth = 220
	movies = pd.read_csv("tmdb_5000_movies.csv")
	movies = movies.drop(columns=['homepage', 'status','production_countries'])
	movies.dropna(subset=['overview', 'original_title'], inplace=True)
	movies.reset_index(drop=True, inplace=True)
	movies.drop_duplicates(subset=['original_title'], inplace=True)
	movies.reset_index(drop=True, inplace=True)
	return movies


def give_recomendations(movie, similarity_distance, movies):
	index = movies[movies['original_title'] == movie].index[0]
	output = 'SOURCE MOVIE:' + '\nTITLE: ' + movies["original_title"].iloc[index] + '\nDESCRIPTION: ' + movies["overview"].iloc[index] + '\n\nRECOMMENDATIONS:'
	for i in range(1, 11):
		ind = np.argsort(similarity_distance[index])[i]
		output += '\n\n#' + str(i) + '\nTITLE: ' + movies["original_title"].iloc[ind] + '\nDESCRIPTION: ' + movies["overview"].iloc[ind]
	return output


if __name__ == "__main__":
	app.run(debug=True,host='0.0.0.0',port=8080)
