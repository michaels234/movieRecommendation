from collections import Counter
from tqdm import tqdm
from scipy.sparse import csr_matrix, coo_matrix
import math
from sklearn.preprocessing import normalize


def get_idfs(documents, keywords):
	idfs = {}  # idfs: dict with idf calc for each keyword
	N = len(documents)  # N: total number of docs
	for word in keywords:
		count = 0  # count: number of docs with this keyword
		for doc in documents:
			# count number of docs this keyword appears in
			if word in doc.split():
				count += 1
		# calculate idf for each keyword
		# idf = relation between tot num docs and num docs with the keyword
		idfs[word] = math.log( 1 + N / count )
	return idfs 
	

def fit(documents):
	# get vocab and idfs
	# vocab: {word: index}
	# idfs: dict with idf calc for each keyword
	keywords = []  # keywords: list of unique keywords in docs
	# add keywords from every doc to list without repetition
	for doc in documents: 
		for word in doc.split(): 
			#if len(word) < 2:  # this is an optional setting to ignore short words
			#	continue
			if word not in keywords:
				keywords.append(word)
	keywords = sorted(keywords)
	vocab = {j: i for i, j in enumerate(keywords)}  # vocab: {word: index}
	idfs = get_idfs(documents, keywords)  # idfs: dict with idf calc for each keyword
	return vocab, idfs


def transform(documents, vocab, idfs):
	rows = []  # each row is a document from documents
	columns = []  # each column is a vocab word from vocab
	values = []
	for row_index, doc in enumerate(tqdm(documents)):
		counter = Counter(doc.split())  # counter: a collection which counts occurence of each element in a list
		word_freq = dict(counter)  # turn counter into a dictionary. {word: count}
		for word, count in word_freq.items():  # word: keyword, count: count of the keyword in the doc
			col_index = vocab.get(word, -1)  # find keyword index from vocab. return -1 if DNE
			if col_index != -1:  # if vocab's index exists
				#if len(word) < 2:  # this is an optional setting to ignore short words
				#	continue
				columns.append(col_index)  # make list of column indices from vocabs indices
				rows.append(row_index)  # make list of row indices from docs indices
				# idf = relation between tot num docs, and num docs with the keyword
				# high = word is in few docs
				# tf = relation between count of the keyword in a doc, and total keywords in a doc
				# high = word has high freq in this doc compared to other words in this doc
				# tf_idf = tf * idf
				# high = word has high freq in this doc and it is in few other docs
				tf = count / len(word_freq)
				tf_idf = tf * idfs[word]
				values.append(tf_idf)
	sparse_matrix = csr_matrix((values, (rows, columns)), shape=(len(rows), len(columns)))
	# scale to unit norm
	tf_idf_matrix = normalize(sparse_matrix, norm='l2', axis=1, copy=True, return_norm=False)		   
	return tf_idf_matrix 


def fit_transform(corpus):
	vocab, idfs = fit(corpus)
	tf_idf_matrix = transform(corpus, vocab, idfs)
	return tf_idf_matrix

#corpus = [
#	'this is the first document',
#	'this document is the second document',
#	'and this is the third one',
#	'is this the first document',
#]

#vocab, idfs = fit(corpus)
#print('vocab', vocab)
#print('idfs', idfs)
#tf_idf_matrix = transform(corpus, vocab, idfs)
#print('tf_idf_matrix')
#for i in range(len(corpus)):
#	for j in range(len(tf_idf_matrix[i].indices)):
#		index = tf_idf_matrix[i].indices[j]
#		value = tf_idf_matrix[i].data[j]
#		print(list(vocab.keys())[index], value)
#for word in vocab:
#	print(word, tf_idf_matrix[0].toarray()[0][vocab[word]])