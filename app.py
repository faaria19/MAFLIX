from flask import Flask, request, jsonify, session
import pandas as pd
import math
import difflib
from flask_cors import CORS
from flask_session import Session
import uuid
from flask import render_template


app = Flask(__name__)
CORS(app)

# Configure session
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
import pandas as pd
import chardet

# Automatically detect encoding
with open('./MovieGenre.csv', 'rb') as f:
    result = chardet.detect(f.read())
    detected_encoding = result['encoding']
    print("Detected encoding:", detected_encoding)
movies_data = pd.read_csv('./MovieGenre.csv', encoding='latin1')
movies_data.fillna('', inplace=True)

# Combine features for TF-IDF
combined_features = (movies_data['Title'] + ' ' + movies_data['Genre']).tolist()

# TF-IDF
def compute_tf(doc):
    tf = {}
    words = doc.lower().split()
    for word in words:
        tf[word] = tf.get(word, 0) + 1
    total_words = len(words)
    for word in tf:
        tf[word] /= total_words
    return tf

def compute_idf(corpus):
    idf = {}
    total_docs = len(corpus)
    for doc in corpus:
        words = set(doc.lower().split())
        for word in words:
            idf[word] = idf.get(word, 0) + 1
    for word in idf:
        idf[word] = math.log(total_docs / idf[word])
    return idf

def compute_tfidf(corpus):
    idf = compute_idf(corpus)
    tfidf_matrix = []
    for doc in corpus:
        tf = compute_tf(doc)
        tfidf = {word: tf[word] * idf[word] for word in tf}
        tfidf_matrix.append(tfidf)
    return tfidf_matrix

def cosine_similarity(vec1, vec2):
    dot = sum(vec1.get(w, 0) * vec2.get(w, 0) for w in vec1)
    norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0

def rocchio_update(query_vec, relevant, non_relevant, alpha=1, beta=0.75, gamma=0.25):
    updated = {k: alpha * v for k, v in query_vec.items()}
    if relevant:
        rel_centroid = {}
        for vec in relevant:
            for k, v in vec.items():
                rel_centroid[k] = rel_centroid.get(k, 0) + v
        for k in rel_centroid:
            updated[k] = updated.get(k, 0) + beta * (rel_centroid[k] / len(relevant))
    if non_relevant:
        nonrel_centroid = {}
        for vec in non_relevant:
            for k, v in vec.items():
                nonrel_centroid[k] = nonrel_centroid.get(k, 0) + v
        for k in nonrel_centroid:
            updated[k] = updated.get(k, 0) - gamma * (nonrel_centroid[k] / len(non_relevant))
    return {k: v for k, v in updated.items() if v > 0}

tfidf_matrix = compute_tfidf(combined_features)
session_data = {}

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    movie_name = data.get('movieName', '').strip()
    genre_filter = data.get('genre', '').strip().lower()
    feedback = data.get('feedback', {})
    current_indexes = data.get('currentRecIndexes', [])

    session_id = get_session_id()
    if session_id not in session_data:
        session_data[session_id] = {'query_vector': None, 'positive_docs': set(), 'negative_docs': set()}

    if not movie_name:
        return jsonify({'error': 'Movie name required'}), 400

    if session_data[session_id]['query_vector'] is None:
        titles = movies_data['Title'].tolist()
        match = difflib.get_close_matches(movie_name, titles, n=1)
        if not match:
            return jsonify([])
        idx = movies_data[movies_data['Title'] == match[0]].index[0]
        session_data[session_id]['query_vector'] = tfidf_matrix[idx]

    for idx_str, fb in feedback.items():
        idx = int(idx_str)
        if fb == 'relevant':
            session_data[session_id]['positive_docs'].add(idx)
            session_data[session_id]['negative_docs'].discard(idx)
        elif fb == 'not_relevant':
            session_data[session_id]['negative_docs'].add(idx)
            session_data[session_id]['positive_docs'].discard(idx)

    pos_vecs = [tfidf_matrix[i] for i in session_data[session_id]['positive_docs']]
    neg_vecs = [tfidf_matrix[i] for i in session_data[session_id]['negative_docs']]
    session_data[session_id]['query_vector'] = rocchio_update(session_data[session_id]['query_vector'], pos_vecs, neg_vecs)

    def is_valid_genre(i):
        return genre_filter in movies_data.iloc[i]['Genre'].lower() if genre_filter else True

    scores = []
    for i, vec in enumerate(tfidf_matrix):
        if is_valid_genre(i):
            sim = cosine_similarity(session_data[session_id]['query_vector'], vec)
            scores.append((i, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_movies = []
    for i, sim in scores[:10]:
        top_movies.append({
            'index': i,
            'title': movies_data.iloc[i]['Title'],
            'vote_average': float(movies_data.iloc[i]['IMDB Score']),
            'genres': movies_data.iloc[i]['Genre'],
            'imdb_link': movies_data.iloc[i]['Imdb Link'],
            'poster': movies_data.iloc[i]['Poster'] if pd.notna(movies_data.iloc[i]['Poster']) else None
        })

    pos = len(session_data[session_id]['positive_docs'])
    neg = len(session_data[session_id]['negative_docs'])
    precision = round(pos / (pos + neg), 2) if (pos + neg) else None

    return jsonify({
        'recommendations': top_movies,
        'evaluation': {
            'relevant_feedback_count': pos,
            'not_relevant_feedback_count': neg,
            'precision': precision
        }
    })

if __name__ == '__main__':
    print("🚀 Starting MAFLIX Flask server at http://127.0.0.1:5000")
    app.run(debug=True)
