import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse
import base64
import mimetypes
import os

# Page config and dark theme CSS
st.set_page_config(page_title="Movie Recommender", layout="wide")

_PAGE_STYLE = """
<style>
html, body, .stApp {
    background: #06070a;
    color: #e6eef6;
    min-height: 100vh;
}
/* two blurred, animated radial blobs for a soft neon background */
.stApp::before{
    content: '';
    position: fixed;
    left: -20%;
    top: -30%;
    width: 60%;
    height: 120%;
    background: radial-gradient(circle at 30% 40%, rgba(124,58,237,0.28), transparent 25%), radial-gradient(circle at 70% 60%, rgba(34,211,238,0.16), transparent 30%);
    filter: blur(80px) saturate(120%);
    transform: translate3d(0,0,0);
    animation: float1 20s linear infinite;
    z-index: 0;
}
.stApp::after{
    content: '';
    position: fixed;
    right: -20%;
    bottom: -30%;
    width: 60%;
    height: 120%;
    background: radial-gradient(circle at 60% 40%, rgba(59,130,246,0.12), transparent 25%), radial-gradient(circle at 40% 60%, rgba(236,72,153,0.10), transparent 30%);
    filter: blur(100px) saturate(110%);
    animation: float2 25s linear infinite;
    z-index: 0;
}
@keyframes float1 {0%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(18px) rotate(18deg)}100%{transform:translateY(0) rotate(0deg)}}
@keyframes float2 {0%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-22px) rotate(-14deg)}100%{transform:translateY(0) rotate(0deg)}}

/* ensure content sits above the background blobs */
.stApp > * { position: relative; z-index: 1; }

.stApp .stButton>button {
    background-color: rgba(17,24,39,0.9);
    color: #e6eef6;
    border: 1px solid rgba(255,255,255,0.04);
}
.stImage img {
    border-radius: 10px;
    box-shadow: 0 12px 36px rgba(2,6,23,0.7);
    object-fit: cover;
}
.stCaption, .stMarkdown p, .stMarkdown div {
    color: #cbd5e1;
}
a { color: #7dd3fc; }
.recommend-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    padding: 8px;
    border-radius: 10px;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.recommend-card:hover { transform: translateY(-6px); box-shadow: 0 18px 50px rgba(2,6,23,0.6); }
</style>
</style>
"""

st.markdown(_PAGE_STYLE, unsafe_allow_html=True)

_STARFIELD = """
<canvas id="starfield"></canvas>
<script>
if(!window.__starfield_added){
    window.__starfield_added = true;
    const canvas = document.getElementById('starfield');
    function size(){canvas.width = window.innerWidth; canvas.height = window.innerHeight}
    size(); window.addEventListener('resize', size);
    canvas.style.position = 'fixed';
    canvas.style.left = '0';
    canvas.style.top = '0';
    canvas.style.zIndex = '0';
    canvas.style.pointerEvents = 'none';
    const ctx = canvas.getContext('2d');
    const stars = [];
    const STAR_COUNT = Math.min(180, Math.max(60, Math.floor(window.innerWidth/8)));
    for(let i=0;i<STAR_COUNT;i++){
        stars.push({x: Math.random()*canvas.width, y: Math.random()*canvas.height, z: Math.random()*1.2+0.2, r: Math.random()*1.2+0.2});
    }
    let t = 0;
    function render(){
        t += 0.008;
        ctx.clearRect(0,0,canvas.width,canvas.height);
        for(const s of stars){
            const sx = (s.x + Math.sin(t*0.6 + s.z*8)*18 + canvas.width) % canvas.width;
            const sy = (s.y + Math.cos(t*0.4 + s.z*6)*18 + canvas.height) % canvas.height;
            const alpha = 0.45 * s.z;
            const rad = s.r * (1 + 0.35*Math.sin(t*3 + s.z*6));
            ctx.beginPath();
            ctx.fillStyle = `rgba(255,255,255,${alpha.toFixed(3)})`;
            ctx.arc(sx, sy, rad, 0, Math.PI*2);
            ctx.fill();
            // small glow
            if(rad>0.8){
                const g = ctx.createRadialGradient(sx, sy, rad*0.5, sx, sy, rad*6);
                g.addColorStop(0, `rgba(125,211,252,${(alpha*0.06).toFixed(3)})`);
                g.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = g;
                ctx.fillRect(sx-rad*6, sy-rad*6, rad*12, rad*12);
            }
        }
        requestAnimationFrame(render);
    }
    render();
    // parallax on mouse move
    window.addEventListener('mousemove', e =>{
        const nx = (e.clientX - window.innerWidth/2)/window.innerWidth;
        const ny = (e.clientY - window.innerHeight/2)/window.innerHeight;
        for(const s of stars){ s.x += nx*0.6*s.z; s.y += ny*0.6*s.z; }
    });
}
</script>
"""

st.markdown(_STARFIELD, unsafe_allow_html=True)


# 🔧 Function to fetch movie poster using TMDB API
def fetch_poster(movie_id):
    # Prefer a locally cached poster image if present
    local_path = os.path.join('posters', f"{movie_id}.jpg")
    if os.path.exists(local_path):
        return local_path
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=9d020c68996d1cd75b873b135cc09b02&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            # try to download and cache the poster locally for future runs
            img_url = "https://image.tmdb.org/t/p/w500/" + poster_path
            try:
                img_resp = requests.get(img_url, timeout=5)
                if img_resp.status_code == 200:
                    os.makedirs('posters', exist_ok=True)
                    with open(local_path, 'wb') as f:
                        f.write(img_resp.content)
                    return local_path
            except Exception:
                # if download fails, fall back to remote URL
                return img_url
    except Exception:
        # Network error or API problem — fall through to fallback
        pass

    # Fallback: return a simple SVG data URI so the UI still shows an image
    svg_fallback = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450">'
        '<rect width="100%" height="100%" fill="#222"/>'
        '<text x="50%" y="50%" fill="#fff" font-size="20" text-anchor="middle" '
        'dominant-baseline="middle">No Image</text>'
        '</svg>'
    )
    return "data:image/svg+xml;utf8," + svg_fallback


def fetch_backdrop(movie_id):
    """Fetch and cache a movie backdrop image (w780 or original) and return a local path or remote URL."""
    local_path = os.path.join('posters', f"{movie_id}_backdrop.jpg")
    if os.path.exists(local_path):
        return local_path
    info_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=9d020c68996d1cd75b873b135cc09b02&language=en-US"
    try:
        r = requests.get(info_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        backdrop_path = data.get('backdrop_path') or data.get('poster_path')
        if backdrop_path:
            img_url = "https://image.tmdb.org/t/p/w780" + backdrop_path
            try:
                ir = requests.get(img_url, timeout=6)
                if ir.status_code == 200:
                    os.makedirs('posters', exist_ok=True)
                    with open(local_path, 'wb') as f:
                        f.write(ir.content)
                    return local_path
            except Exception:
                return img_url
    except Exception:
        pass
    return None




# 🔍 Load data
movies_dict = pickle.load(open('movies.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))


# 🔁 Recommend function
def recommend(movie_name):
    movie_index = movies[movies['title'] == movie_name].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id  # ✅ FIXED: get the TMDB movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_posters


st.markdown("<h1 style='text-align:center; color:#f8fafc; margin-bottom:8px'>🎬 Movie Recommender System</h1>", unsafe_allow_html=True)

selected_movie_name = st.selectbox(
    'Select a movie to get recommendations:',
    movies['title'].values
)

if st.button('Recommend'):
    names, posters = recommend(selected_movie_name)

    # set a single cinematic backdrop for the selected movie (not per-card)
    try:
        sel_id = movies[movies['title'] == selected_movie_name].iloc[0].movie_id
    except Exception:
        sel_id = None
    if sel_id:
        b = fetch_backdrop(sel_id)
        if b:
            burl = b
            bg_js = f"""
            <style>
            .movie-backdrop{{
                position: fixed; left:0; top:0; width:100%; height:100%; z-index:0; pointer-events:none; background-image: url('{burl}'); background-size:cover; filter: blur(14px) brightness(0.28) saturate(120%); opacity:0.85; transform: scale(1.03);
            }}
            </style>
            <div class='movie-backdrop'></div>
            """
            st.markdown(bg_js, unsafe_allow_html=True)

    def _img_src_for(src):
        """Return an HTML-safe src value. If `src` is a local file path, return a data URI."""
        try:
            if isinstance(src, str) and src.startswith('posters') and os.path.exists(src):
                ctype, _ = mimetypes.guess_type(src)
                if not ctype:
                    ctype = 'image/jpeg'
                with open(src, 'rb') as f:
                    data = base64.b64encode(f.read()).decode('ascii')
                return f"data:{ctype};base64,{data}"
        except Exception:
            pass
        return src

    # Create 5 equal columns and render themed recommendation cards
    cols = st.columns(5)

    def theme_from_tags(tagstr):
        if not isinstance(tagstr, str):
            return ("#0f172a", "#0b1220")
        s = tagstr.lower()
        if 'action' in s or 'thriller' in s:
            return ("#ff5f6d", "#ffc371")
        if 'romanc' in s or 'love' in s:
            return ("#fbc2eb", "#a6c1ee")
        if 'sciencefict' in s or 'sci' in s or 'futur' in s:
            return ("#7dd3fc", "#c084fc")
        if 'horror' in s or 'mystery' in s:
            return ("#0f172a", "#020617")
        if 'comedy' in s:
            return ("#fdeb7d", "#ffb199")
        if 'adventur' in s or 'fantasi' in s:
            return ("#8fd3f4", "#84fab0")
        return ("#0f172a", "#0b1220")

    for idx, col in enumerate(cols):
        if idx >= len(names):
            break
        try:
            movie_row = movies[movies['title'] == names[idx]].iloc[0]
            tags = movie_row.get('tags', '')
        except Exception:
            tags = ''
        c1, c2 = theme_from_tags(tags)
        query = urllib.parse.quote_plus(names[idx])
        jw_url = f"https://www.justwatch.com/us/search?q={query}"

        poster_src = _img_src_for(posters[idx])
        # attempt to get a backdrop to use as blurred page background
        backdrop = fetch_backdrop(movies[movies['title'] == names[idx]].iloc[0].movie_id)
        if backdrop:
            # inject a small script to set the page background to a blurred version of the backdrop
            burl = backdrop
            bg_js = f"""
            <style>
            .movie-backdrop{{
                position: fixed; left:0; top:0; width:100%; height:100%; z-index:0; pointer-events:none; background-image: url('{burl}'); background-size:cover; filter: blur(14px) brightness(0.28) saturate(120%); opacity:0.85; transform: scale(1.03);
            }}
            </style>
            <div class='movie-backdrop'></div>
            """
            st.markdown(bg_js, unsafe_allow_html=True)

        card_html = f"""
        <div class='recommend-card' style='background: linear-gradient(135deg, {c1}, {c2}); height:360px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
            <img src="{poster_src}" style='width:160px; height:240px; object-fit:cover; border-radius:8px; box-shadow: 0 12px 36px rgba(0,0,0,0.6);'/>
            <div style='margin-top:10px; text-align:center; font-weight:600; color:#f8fafc;'>{names[idx]}</div>
            <div style='margin-top:6px'> <a href="{jw_url}" target="_blank">Where to watch</a></div>
        </div>
        """
        col.markdown(card_html, unsafe_allow_html=True)
