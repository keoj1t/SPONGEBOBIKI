# Deployment Guide: Streamlit Cloud

## Quick Start (5 minutes)

### Option 1: Deploy on Streamlit Cloud (Recommended - Free)

**Prerequisites:**
- GitHub account with the repo pushed ✅ (already done: https://github.com/keoj1t/SPONGEBOBIKI)
- Streamlit account

**Steps:**

1. **Sign up on Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Click "Sign up"
   - Choose "Continue with GitHub"
   - Authorize Streamlit app

2. **Deploy the app**
   - Click "New app" 
   - Select repository: `keoj1t/SPONGEBOBIKI`
   - Select branch: `main`
   - Set main file path: `streamlit_app.py` or `app/dashboard.py`
   - Click "Deploy"

3. **Wait for deployment**
   - Takes 1-2 minutes
   - You'll see a public URL like: `https://spongebobiki-growth.streamlit.app`
   - Share this link in your submission

**That's it!** The dashboard will be live and accessible from anywhere.

---

### Option 2: Run Locally (For Development/Demo)

```bash
cd c:\Users\Aisanabatalova\spongebobiki

# Activate virtual environment
.venv\Scripts\activate

# Run the dashboard
streamlit run app/dashboard.py
```

- Opens at `http://localhost:8501`
- Perfect for screen recording the video walkthrough

---

### Option 3: Deploy with Docker (Advanced)

```bash
docker build -t spongebobiki-dashboard .
docker run -p 8501:8501 --env-file .env spongebobiki-dashboard
```

Then access at `http://localhost:8501`

---

## Environment Variables for Streamlit Cloud

If your dashboard needs API keys (Apify tokens), add them via Streamlit Cloud settings:

1. In Streamlit Cloud console → App settings → Secrets
2. Add:
```
APIFY_TOKEN = "your_token_here"
APIFY_TOKEN_TWITTER = "..."
```

The app will read these automatically from `st.secrets`.

---

## Dashboard Features

The Streamlit dashboard includes:

✅ **Real-time metrics cards** — Platform engagement stats  
✅ **Interactive charts** — Plotly visualizations  
✅ **Alert panel** — Latest anomaly detections  
✅ **Top posts carousel** — Highest engagement content  
✅ **Sentiment breakdown** — Per-platform sentiment distribution  
✅ **Narrative heatmap** — Narrative × Platform cross-tab  
✅ **Live pipeline trigger** — Run analysis on-demand  
✅ **Dark theme** — Lime accent (#c8ff00) on #0a0a0a background  

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'app'"**
- Make sure you're deploying from the root directory where the `app/` folder exists
- Check that `streamlit_app.py` is in the root

**"Data files not found"**
- CSV and chart files are committed to GitHub
- Streamlit Cloud will pull them automatically

**App crashes**
- Check the Streamlit Cloud logs (stdout tab in console)
- Ensure all dependencies in `requirements.txt` are included

---

## Submission Checklist

- [ ] Project on GitHub: https://github.com/keoj1t/SPONGEBOBIKI
- [ ] Streamlit Cloud URL: https://spongebobiki-growth.streamlit.app (or your URL)
- [ ] README.md with setup instructions ✅
- [ ] Counter-playbook document (COUNTER_PLAYBOOK.md) ✅
- [ ] Architecture diagram (architecture_diagram.html) ✅
- [ ] Video walkthrough (5-10 min) - record locally with Loom/OBS
- [ ] All deliverables ready

---

**Next Step:** Once deployed, visit your Streamlit Cloud URL to verify it's live, then submit!
