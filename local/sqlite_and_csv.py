import sqlite3
import pandas as pd
import json
import string

class DataBase():
	def csv_to_db(self):
		# get csv data
		movies = pd.read_csv("tmdb_5000_movies.csv")
		movies.dropna(subset=['overview', 'original_title'], inplace=True)  # drop items without overview or original title
		movies.drop_duplicates(subset=['original_title'], inplace=True)  # drop items with same original title as others
		movies.reset_index(drop=True, inplace=True)  # reset indices to fix gaps since some were deleted

		# insert into database
		conn = sqlite3.connect('movies.db')
		cursor = conn.cursor()
		cursor.execute('DROP TABLE IF EXISTS movies')
		cursor.execute('DROP TABLE IF EXISTS movies_fts')
		cursor.execute('CREATE TABLE movies (ind INTEGER PRIMARY KEY, title TEXT, clean_title TEXT, year TEXT, overview TEXT, genres TEXT, keywords TEXT, fittable_words TEXT, similarity_indices TEXT)')
		for ind, movie in movies.iterrows():
			title = movie['original_title']
			clean_title = ''.join([char for char in movie['original_title'].lower() if char not in string.punctuation])
			year = '' if pd.isna(movie['release_date']) else str(movie['release_date']).split('-')[0]
			overview = movie['overview']
			genres = str([genre['name'] for genre in json.loads(movie['genres'])]).replace("'", "").replace("[", "").replace("]", "")
			keywords = str([genre['name'] for genre in json.loads(movie['keywords'])]).replace("'", "").replace("[", "").replace("]", "")
			cursor.execute("""
				INSERT INTO movies (ind, title, clean_title, year, overview, genres, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)
			""", (ind, title, clean_title, year, overview, genres, keywords))
		conn.commit()
		conn.close()
	
	def get_movie_count(self):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT COUNT(ind) FROM movies')
			conn.commit()
			return cursor.fetchone()[0]

	def get_movie(self, ind):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM movies WHERE ind = ?', (ind,))
			conn.commit()
			return cursor.fetchone()

	def get_title_overview_from_ind_list(self, similarity_indices):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute(f'SELECT ind, title, overview FROM movies WHERE ind IN {similarity_indices}')
			conn.commit()
			unordered = {str(ind): {'title': title, 'overview': overview} for ind, title, overview in cursor.fetchall()}
			return [unordered[str(ind)] for ind in similarity_indices]

	def list_all_movie_data(self):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM movies')
			conn.commit()
			return cursor.fetchall()

	def list_all_fittable_words(self):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT fittable_words FROM movies')
			conn.commit()
			return [row[0] for row in cursor.fetchall()]
	
	def update_movie_fittable_words(self, ind, val):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('UPDATE movies SET fittable_words = ? WHERE ind = ?', (val, ind,))
			conn.commit()
	
	def update_movie_similarity_indices(self, ind, val):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('UPDATE movies SET similarity_indices = ? WHERE ind = ?', (val, ind,))
			conn.commit()


if __name__ == "__main__":
	database = DataBase()
	database.csv_to_db()
