import pickle
import streamlit as st
import requests
from thefuzz import process  # ✅ Correct Import

# Function to fetch movie poster using TMDB API (dummy now)
def fetch_poster(movie_title):
    # You can improve this function by using TMDB API to get real posters
    return "https://via.placeholder.com/150?text=" + movie_title.replace(" ", "+")

def recommend(movie):
    movie = movie.strip().lower()  # Normalize input
    
    # Step 1: Find the Closest Matching Movie Title
    best_match = process.extractOne(movie, movies['title'])
    
    if best_match is None or best_match[1] < 80:  # Confidence threshold
        st.error("Movie not found in dataset!")
        return [], []  # Return empty lists if not found

    index = movies[movies['title'] == best_match[0]].index[0]
    
    # Step 2: Get Similar Movies Based on Cosine Similarity
    distances = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)
    recommended_movies_name = []
    recommended_movies_poster = []
    
    # Step 3: Collect Top 5 Recommended Movies
    for i in distances[1:6]:  # Exclude the first (input movie itself)
        movie_title = movies.iloc[i[0]].title
        recommended_movies_name.append(movie_title)
        recommended_movies_poster.append(fetch_poster(movie_title))  # Fetch poster

    return recommended_movies_name, recommended_movies_poster

# Streamlit UI
st.header("Movies Recommendation System using Machine Learning")

movies = pickle.load(open('artifacts/movie_list.pkl', 'rb'))
similarity = pickle.load(open('artifacts/similarity.pkl', 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox('Select or type a movie name to get recommendations', movie_list)

if st.button('Show Recommendation'):
    recommended_movies_name, recommended_movies_poster = recommend(selected_movie)
    
    # Display in 5 columns
    if recommended_movies_name:
        col1, col2, col3, col4, col5 = st.columns(5)
        cols = [col1, col2, col3, col4, col5]
        
        for i in range(5):
            with cols[i]:
                st.text(recommended_movies_name[i])
                st.image(recommended_movies_poster[i])
