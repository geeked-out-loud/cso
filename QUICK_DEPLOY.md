# 🚀 Quick Deploy Guide - TL;DR

## 1️⃣ Push to GitHub (5 minutes)

```powershell
cd c:\projects\cso
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/cso-simulator.git
git push -u origin main
```

## 2️⃣ Deploy on Render (3 minutes)

1. Go to https://render.com → Sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Configure:
   - **Name:** `cso-simulator`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
   - **Plan:** Free
5. Click **"Create Web Service"**
6. Wait 3-5 minutes ⏳

## 3️⃣ Done! 🎉

Your app will be live at:
```
https://cso-simulator.onrender.com
```

### ⚠️ Important Notes:
- First load takes ~30 seconds (cold start)
- App sleeps after 15 min inactivity
- Free tier = 750 hours/month (enough for 24/7)

### 🔄 Auto-Deploy:
Every time you push to GitHub, Render automatically redeploys!

```powershell
git add .
git commit -m "Updates"
git push
```

---

**Full guide:** See [DEPLOYMENT.md](DEPLOYMENT.md)
