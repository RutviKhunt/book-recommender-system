from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np

# Load the data models
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_ratings'].values)
                           )


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')


@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = request.form.get('user_input')

    try:
        # 1. Find the index of the book
        index = np.where(pt.index == user_input)[0][0]

        # 2. Get similar items based on similarity scores
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
            data.append(item)

        return render_template('recommend.html', data=data)

    except Exception as e:
        # FALLBACK LOGIC: If book not found, suggest Top 4 Popular Books
        print(f"Error: {e}")
        fallback_data = []
        for i in range(4):
            item = [
                popular_df['Book-Title'].values[i],
                popular_df['Book-Author'].values[i],
                popular_df['Image-URL-M'].values[i]
            ]
            fallback_data.append(item)

        return render_template('recommend.html',
                               error="Book not found in our database. You might like these popular titles:",
                               data=fallback_data)


@app.route('/suggest', methods=['POST'])
def suggest():
    all_books = list(pt.index)
    return jsonify(all_books)


@app.route('/book/<name>')
def book_details(name):
    try:
        # Search for the book in your original books dataframe
        temp_df = books[books['Book-Title'] == name].drop_duplicates('Book-Title')

        # Extract details
        book_info = {
            'title': temp_df['Book-Title'].values[0],
            'author': temp_df['Book-Author'].values[0],
            'image': temp_df['Image-URL-L'].values[0],
            'publisher': temp_df['Publisher'].values[0],
            'year': temp_df['Year-Of-Publication'].values[0]
        }

        # Get recommendations for the details page
        index = np.where(pt.index == name)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

        suggestions = []
        for i in similar_items:
            item = []
            temp = books[books['Book-Title'] == pt.index[i[0]]].drop_duplicates('Book-Title')
            item.extend(list(temp['Book-Title'].values))
            item.extend(list(temp['Image-URL-M'].values))
            suggestions.append(item)

        return render_template('details.html', book=book_info, suggestions=suggestions)
    except:
        return render_template('index.html')  # Redirect home if something goes wrong

import random

@app.route('/surprise')
def surprise_me():
    # Pick a random index from the popular_df
    random_idx = random.randint(0, len(popular_df) - 1)
    book_name = popular_df['Book-Title'].values[random_idx]
    # Redirect to the details page of that random book
    from flask import redirect, url_for
    return redirect(url_for('book_details', name=book_name))

if __name__ == '__main__':
    app.run(debug=True)