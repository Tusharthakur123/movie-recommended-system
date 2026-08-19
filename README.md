# Movie Recommender — deployment notes

Short steps to get a free public link (two options): Hugging Face Spaces or Streamlit Community Cloud.

Prerequisites:
- A GitHub account (for either deployment).
- This repository pushed to a GitHub repo.
- `requirements.txt` is present (already added).

Option A — Hugging Face Spaces (recommended for public Streamlit apps):
1. Push this project to a GitHub repository.
2. Go to https://huggingface.co/spaces and click **Create new Space**.
3. Choose **Streamlit** as the SDK, set visibility to **Public**, and create.
4. In the newly created Space repo, either connect your GitHub repo or upload these files.
5. The Space will build and provide a URL like `https://huggingface.co/spaces/<username>/<repo>`.

Option B — Streamlit Community Cloud:
1. Push this project to a GitHub repository.
2. Visit https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, select your repo and branch, and set the main file to `app.py`.
4. Deploy — Streamlit will build and give you a `share.streamlit.io` URL.

Notes & gotchas:
- Large files (like `movies.pkl` and `similarity.pkl`) may exceed hosting file-size limits. If they are large (>50-100 MB), consider hosting them on external storage (Git LFS, S3, or Hugging Face datasets) and download at runtime.
- If external API calls (TMDB) fail due to network, the app will show a placeholder image; consider pre-caching posters locally or bundling URLs.

Git LFS instructions (recommended for `similarity.pkl` which is large):
1. Install Git LFS: https://git-lfs.github.com/ and run `git lfs install`.
2. Track the large files and push:
```bash
git lfs track "*.pkl"
git add .gitattributes
git add movies.pkl similarity.pkl
git commit -m "Add pickles via Git LFS"
git push origin main
```
Note: You may need to enable Git LFS support on your Git hosting account.

Local push example (replace `<user>` and `<repo>`):
```bash
cd "movie-recommended-system"
git init
git add .
git commit -m "Prepare for deployment"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

After push, follow either Option A or B above to get a free link.

If you want, I can:
- prepare everything here (I added `requirements.txt`), and guide you through pushing to GitHub, or
- create a poster-cache script to download poster images once and commit them (if file sizes stay reasonable).
