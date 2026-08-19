#!/usr/bin/env python3
"""Download TMDB posters for all movies in movies.pkl and save to ./posters/.

Run this once when you have working network access to cache images locally.
"""
import os
import time
import pickle
import requests

API_KEY = "9d020c68996d1cd75b873b135cc09b02"
BASE_INFO = "https://api.themoviedb.org/3/movie/{id}?api_key={key}&language=en-US"
BASE_IMG = "https://image.tmdb.org/t/p/w500"


def main():
    os.makedirs('posters', exist_ok=True)
    movies = pickle.load(open('movies.pkl', 'rb'))
    # movies is a DataFrame — iterate rows
    try:
        ids = list(movies['movie_id'].values)
        titles = list(movies['title'].values)
    except Exception:
        # fallback if movies is a dict-like
        ids = []
        titles = []
        for r in movies:
            ids.append(r.get('movie_id'))
            titles.append(r.get('title'))

    total = len(ids)
    for idx, movie_id in enumerate(ids):
        if movie_id is None:
            continue
        local_path = os.path.join('posters', f"{movie_id}.jpg")
        if os.path.exists(local_path):
            print(f"[{idx+1}/{total}] cached {movie_id} — skip")
            continue
        info_url = BASE_INFO.format(id=movie_id, key=API_KEY)
        try:
            r = requests.get(info_url, timeout=6)
            r.raise_for_status()
            data = r.json()
            poster_path = data.get('poster_path')
            if poster_path:
                img_url = BASE_IMG + poster_path
                ir = requests.get(img_url, timeout=8)
                if ir.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(ir.content)
                    print(f"[{idx+1}/{total}] saved poster for {movie_id}")
                else:
                    print(f"[{idx+1}/{total}] image download failed {movie_id}: {ir.status_code}")
            else:
                print(f"[{idx+1}/{total}] no poster for {movie_id}")
        except Exception as e:
            print(f"[{idx+1}/{total}] error for {movie_id}: {e}")
        # be polite to TMDB API and avoid rate limits
        time.sleep(0.25)


if __name__ == '__main__':
    main()
