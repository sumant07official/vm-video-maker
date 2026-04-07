# 🔱 VM - Video Maker

## Deploy on Render (Free) — Step by Step

### Step 1 — GitHub pe upload karo
1. GitHub.com pe jaao
2. New Repository banao — name: `vm-video-maker`
3. Yeh sab files upload karo:
   - `VM_Maker.html`
   - `vm_server.py`
   - `requirements.txt`
   - `render.yaml`
   - `Procfile`
   - `README.md`

### Step 2 — Render pe deploy karo
1. **render.com** pe jaao
2. Sign up (GitHub se login karo)
3. **"New +"** → **"Web Service"** click karo
4. GitHub repo select karo (`vm-video-maker`)
5. Yeh settings karo:
   - **Name:** vm-video-maker
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn vm_server:app --bind 0.0.0.0:$PORT --workers 1 --timeout 600`
6. **"Create Web Service"** click karo
7. Wait karo (2-3 min) — deploy hoga!

### Step 3 — Use karo!
- Render tumhe ek URL dega: `https://vm-video-maker.onrender.com`
- Us URL pe jaao — VM directly browser mein chalega!
- Koi server locally nahi chalana padega!

## Local Use
```bash
pip install flask flask-cors Pillow
python vm_server.py
# Phir VM_Maker.html browser mein open karo
```

## FFmpeg on Render
Render pe FFmpeg pre-installed hota hai — koi extra setup nahi!
