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
		cursor.execute('CREATE INDEX movies_clean_title ON movies(clean_title)')  # for list_titles_from_query ON
		cursor.execute('CREATE VIRTUAL TABLE movies_fts USING fts5(clean_title)')  # for list_titles_from_query GLOB
		cursor.execute('INSERT INTO movies_fts(clean_title) SELECT clean_title FROM movies')
		conn.commit()
		conn.close()

	def list_titles_from_query(self, title_query):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			# movies_fts can be searched with partial matching with GLOB,
			# JOIN with movies to select title and year,
			# LIMIT to 100 rows returned so memory usage is kept low,
			# surround every word in title_query string with * to match father in godfather etc.
			cursor.execute("""
				SELECT movies.ind, movies.title, movies.year
				FROM movies_fts
				JOIN movies
				ON movies_fts.clean_title = movies.clean_title
				WHERE movies_fts.clean_title GLOB ?
				LIMIT 100
			""", (f"*{title_query.replace(' ', '* *')}*",))
			conn.commit()
			return [{'ind': ind, 'titleYear': title + f' ({year})'} for ind, title, year in cursor.fetchall()]
	
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
	
	def list_similar_movies_from_ind(self, ind):
		with sqlite3.connect('movies.db') as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT similarity_indices FROM movies WHERE ind = ?', (ind,))
			similarity_indices = tuple(cursor.fetchone()[0].split(', '))
			cursor.execute(f'SELECT ind, title, overview FROM movies WHERE ind IN {similarity_indices}')
			conn.commit()
			unordered = {str(ind): {'title': title, 'overview': overview} for ind, title, overview in cursor.fetchall()}
			return [unordered[str(ind)] for ind in similarity_indices]


if __name__ == "__main__":
	database = DataBase()
	database.csv_to_db()
