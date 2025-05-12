import asyncio
import pickle
import streamlit as st
import httpx  # For asynchronous HTTP requests
from thefuzz import process
import os

# --- Configuration ---
TMDB_API_KEY = "1d116fa203a27bc65fd960239a9de031"
if not TMDB_API_KEY:
    TMDB_API_KEY = "YOUR_TMDB_API_KEY"  # Replace with your actual API key
BASE_TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
NO_POSTER_URL = "https://via.placeholder.com/150?text=No+Image"
FUZZY_MATCH_THRESHOLD = 80

# --- Asynchronous Functions ---
async def fetch_poster_async(movie_id, client):
    """Asynchronously fetches the movie poster URL from TMDB API."""
    if not TMDB_API_KEY:
        st.error("TMDB API key not configured.")
        return NO_POSTER_URL
    search_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = await client.get(search_url)
        response.raise_for_status()
        data = response.json()
        if 'poster_path' in data and data['poster_path']:
            return f"{BASE_TMDB_IMAGE_URL}{data['poster_path']}"
    except httpx.RequestError as e:
        st.error(f"Error fetching poster for movie ID {movie_id}: {e}")
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error {e.response.status_code} fetching poster for movie ID {movie_id}")
    except ValueError:
        st.error(f"Error decoding JSON response for movie ID {movie_id}")
    return NO_POSTER_URL

async def fetch_movie_id_from_tmdb_async(movie_title, client):
    """Asynchronously fetches the movie ID from TMDB API based on the title."""
    if not TMDB_API_KEY:
        st.error("TMDB API key not configured.")
        return None
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}&language=en-US"
    try:
        response = await client.get(search_url)
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            return data['results'][0]['id']
    except httpx.RequestError as e:
        st.error(f"Error searching movie '{movie_title}' on TMDB: {e}")
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error {e.response.status_code} searching movie '{movie_title}'")
    except ValueError:
        st.error(f"Error decoding JSON response for movie '{movie_title}' search.")
    return None

async def recommend_async(movie_name, movies_df, similarity_matrix):
    """Asynchronously recommends similar movies based on the input movie name."""
    movie_name = movie_name.strip().lower()
    best_match = process.extractOne(movie_name, movies_df['title'])

    if best_match is None or best_match[1] < FUZZY_MATCH_THRESHOLD:
        st.error(f"Movie '{movie_name}' not found in the dataset with sufficient similarity.")
        return [], []

    matched_title = best_match[0]
    try:
        index = movies_df[movies_df['title'] == matched_title].index[0]
        distances = sorted(list(enumerate(similarity_matrix[index])), key=lambda x: x[1], reverse=True)

        recommended_movie_names = []
        recommended_movie_posters = []

        async with httpx.AsyncClient() as client:
            for i in distances[1:6]:
                movie_title = movies_df.iloc[i[0]]['title']
                movie_id = movies_df.iloc[i[0]].get('movie_id')

                if not movie_id:
                    movie_id = await fetch_movie_id_from_tmdb_async(movie_title, client)

                if movie_id:
                    recommended_movie_names.append(movie_title)
                    poster_url = await fetch_poster_async(movie_id, client)
                    recommended_movie_posters.append(poster_url)
                else:
                    recommended_movie_names.append(movie_title + " (Poster ID not found)")
                    recommended_movie_posters.append(NO_POSTER_URL)

        return recommended_movie_names, recommended_movie_posters

    except IndexError:
        st.error(f"Could not find the index for '{matched_title}' in the dataset.")
        return [], []
    except Exception as e:
        st.error(f"An unexpected error occurred during recommendation: {e}")
        return [], []

# --- Streamlit UI ---
st.set_page_config(page_title="Movie Recommender Async", layout="wide")
st.header("🎬 Asynchronous Movie Recommendation System using ML")

# Load pre-trained data
try:
    movies = pickle.load(open('artifacts/movie_list.pkl', 'rb'))
    similarity = pickle.load(open('artifacts/similarity.pkl', 'rb'))
except FileNotFoundError:
    st.error("Error: 'movie_list.pkl' or 'similarity.pkl' not found in the 'artifacts' directory. Please ensure these files exist.")
    st.stop()
except Exception as e:
    st.error(f"Error loading data files: {e}")
    st.stop()

# Debugging: Check the first few rows of your dataset
if st.checkbox("Show Movie Dataframe Head"):
    st.write(movies.head())

movie_list = movies['title'].values
selected_movie = st.selectbox('🎥 Select or type a movie name to get recommendations:', movie_list)

if st.button('Show Recommendation'):
    # Streamlit doesn't directly support asyncio.run() within the main script.
    # We need to use st.experimental_rerun to handle the asynchronous operation.
    async def get_recommendations():
        recommended_movie_names, recommended_movie_posters = await recommend_async(selected_movie, movies, similarity)
        if recommended_movie_names:
            st.subheader("Recommendations:")
            cols = st.columns(2)
            for i in range(min(2, len(recommended_movie_names))):
                with cols[i]:
                    st.text(recommended_movie_names[i])
                    st.image(recommended_movie_posters[i])
            if len(recommended_movie_names) > 2:
                cols = st.columns(3)
                for i in range(2, len(recommended_movie_names)):
                    with cols[i % 3]:
                        st.text(recommended_movie_names[i])
                        st.image(recommended_movie_posters[i])

    asyncio.run(get_recommendations())