import pickle
import re
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

API_KEY = "c4258c798c6f52c6671162c53ea0bd91"
BASE_IMG = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER = "https://placehold.co/300x450/1c1c1c/888888?text=No+Poster"

BASE_DIR = Path(__file__).resolve().parent


@st.cache_resource
def get_session():
    session = requests.Session()

    retries = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "User-Agent": "movie-recommender-app/1.0"
    })

    return session


@st.cache_resource
def load_data():
    with open(BASE_DIR / "movie_dict.pkl", "rb") as file:
        movie_dict = pickle.load(file)

    with open(BASE_DIR / "similarity.pkl", "rb") as file:
        similarity_data = pickle.load(file)

    return pd.DataFrame(movie_dict), similarity_data


movies, similarity = load_data()
session = get_session()


@st.cache_data(ttl=86400)
def search_by_title(query):
    try:
        response = session.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": API_KEY,
                "query": query,
                "language": "en-US",
            },
            timeout=20,
        )

        response.raise_for_status()

        for result in response.json().get("results", []):
            poster_path = result.get("poster_path")
            if poster_path:
                return BASE_IMG + poster_path

    except requests.RequestException:
        return None

    return None


@st.cache_data(ttl=86400)
def fetch_poster(movie_id, movie_title):
    try:
        response = session.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={
                "api_key": API_KEY,
                "language": "en-US",
            },
            timeout=20,
        )

        response.raise_for_status()

        poster_path = response.json().get("poster_path")
        if poster_path:
            return BASE_IMG + poster_path

    except requests.RequestException:
        pass

    searches = []

    searches.append(movie_title)

    clean_title = re.sub(r"\(\d{4}\)", "", movie_title).strip()
    if clean_title and clean_title != movie_title:
        searches.append(clean_title)

    short_title = movie_title.split(":")[0].strip()
    if short_title and short_title != movie_title:
        searches.append(short_title)

    stop_words = {"the", "a", "an", "of", "in", "at", "and"}
    words = [word for word in movie_title.split() if word.lower() not in stop_words]
    partial_title = " ".join(words[:3])
    if partial_title:
        searches.append(partial_title)

    for title in searches:
        poster = search_by_title(title)
        if poster:
            return poster

    return PLACEHOLDER


def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]

    distances = sorted(
        list(enumerate(similarity[movie_index])),
        reverse=True,
        key=lambda item: item[1],
    )

    names = []
    posters = []

    for item in distances[1:6]:
        row = movies.iloc[item[0]]
        names.append(row.title)
        posters.append(fetch_poster(row.movie_id, row.title))

    return names, posters


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(229, 9, 20, 0.18), transparent 34%),
            radial-gradient(circle at top right, rgba(255, 255, 255, 0.08), transparent 28%),
            linear-gradient(135deg, #080808 0%, #111111 45%, #171717 100%);
        color: #ffffff;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 48px;
        padding-bottom: 48px;
    }

    .hero {
        text-align: center;
        padding: 26px 20px 34px;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border: 1px solid rgba(229, 9, 20, 0.35);
        border-radius: 999px;
        background: rgba(229, 9, 20, 0.08);
        color: #ffb3b8;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 18px;
    }

    .hero-title {
        font-size: clamp(2.2rem, 5vw, 4.2rem);
        font-weight: 800;
        line-height: 1.05;
        letter-spacing: 0;
        margin: 0;
        color: #ffffff;
    }

    .hero-title span {
        color: #e50914;
    }

    .subtitle {
        color: #b8b8b8;
        font-size: 1.02rem;
        margin-top: 16px;
        margin-bottom: 0;
    }

    .search-panel {
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.055);
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(16px);
        margin-top: 12px;
        margin-bottom: 30px;
    }

    label[data-testid="stWidgetLabel"] p {
        color: #f4f4f4 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    .stSelectbox > div > div {
        background-color: rgba(12, 12, 12, 0.95) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 12px !important;
        min-height: 48px;
    }

    .stSelectbox > div > div:hover {
        border-color: rgba(229, 9, 20, 0.75) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #ff1f2d, #b20710) !important;
        color: #ffffff !important;
        border: none !important;
        min-height: 48px;
        padding: 12px 28px !important;
        font-size: 0.98rem !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        width: 100%;
        box-shadow: 0 14px 30px rgba(229, 9, 20, 0.32);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 18px 38px rgba(229, 9, 20, 0.42);
    }

    .section-title {
        color: #ffffff;
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .section-subtitle {
        color: #9a9a9a;
        font-size: 0.92rem;
        margin-bottom: 22px;
    }

    div[data-testid="stImage"] img {
        border-radius: 16px !important;
        box-shadow: 0 18px 36px rgba(0, 0, 0, 0.5);
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }

    div[data-testid="stImage"] img:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 24px 48px rgba(229, 9, 20, 0.22);
    }

    .movie-title {
        color: #f5f5f5;
        font-size: 0.88rem;
        font-weight: 700;
        text-align: center;
        margin-top: 12px;
        line-height: 1.35;
        min-height: 42px;
    }

    .empty-state {
        text-align: center;
        padding: 70px 20px;
        border: 1px dashed rgba(255, 255, 255, 0.14);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.035);
        color: #9d9d9d;
    }

    .empty-icon {
        font-size: 3.4rem;
        margin-bottom: 12px;
    }

    .empty-title {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .empty-text {
        color: #9d9d9d;
        font-size: 0.95rem;
    }

    hr {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="hero">
    <div class="hero-badge">Movie intelligence powered by recommendations</div>
    <h1 class="hero-title">Movie <span>Recommendation</span> System</h1>
    <p class="subtitle">Choose a movie you like and discover five similar picks instantly.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="search-panel">', unsafe_allow_html=True)

c1, c2 = st.columns([4, 1])

with c1:
    selected_movie = st.selectbox("Select a Movie", movies["title"].values)

with c2:
    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    btn = st.button("Recommend")

st.markdown("</div>", unsafe_allow_html=True)


# RESULTS
if btn:
    with st.spinner("Finding the best matches..."):
        names, posters = recommend(selected_movie)

    st.markdown(
        f"""
        <div class="section-title">Because you liked {selected_movie}</div>
        <div class="section-subtitle">Here are five movies with a similar feel.</div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)

    for col, name, poster in zip(cols, names, posters):
        with col:
            st.image(poster, width="stretch")
            st.markdown(
                f'<div class="movie-title">{name}</div>',
                unsafe_allow_html=True,
            )

else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🎬</div>
        <div class="empty-title">Ready when you are</div>
        <div class="empty-text">
            Select a movie above and click <b style="color:#e50914">Recommend</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)