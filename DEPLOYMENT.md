# 🚀 Deploy CSO Simulator to Render.com

## Step-by-Step Deployment Guide

### Prerequisites
- ✅ GitHub account
- ✅ Render.com account (free)
- ✅ Your CSO project code

---

## 📋 Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)

Open PowerShell in your project directory and run:

```powershell
cd c:\projects\cso
git init
git add .
git commit -m "Initial commit - CSO Visual Simulator"
```

### 1.2 Create a GitHub Repository

1. Go to https://github.com/new
2. Repository name: `cso-simulator` (or any name you like)
3. Description: `Cat Swarm Optimization Visual Simulator`
4. Keep it **Public** (required for free Render deployment)
5. **Don't** initialize with README, .gitignore, or license
6. Click **"Create repository"**

### 1.3 Push Your Code to GitHub

```powershell
git remote add origin https://github.com/YOUR_USERNAME/cso-simulator.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## 🌐 Step 2: Create Render.com Account

1. Go to https://render.com
2. Click **"Get Started for Free"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if needed

---

## ⚙️ Step 3: Deploy Your App on Render

### 3.1 Create New Web Service

1. Log in to Render Dashboard: https://dashboard.render.com
2. Click **"New +"** button (top right)
3. Select **"Web Service"**

### 3.2 Connect Your GitHub Repository

1. Click **"Connect account"** under GitHub
2. Authorize Render to access your GitHub
3. Find and select your `cso-simulator` repository
4. Click **"Connect"**

### 3.3 Configure Your Service

Fill in the following details:

**Basic Settings:**
- **Name:** `cso-simulator` (or your preferred name)
- **Region:** Choose closest to you (e.g., Oregon, Frankfurt, Singapore)
- **Branch:** `main`
- **Root Directory:** (leave blank)
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** 
  ```
  pip install -r requirements.txt
  ```

- **Start Command:**
  ```
  gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
  ```

**Instance Type:**
- Select **"Free"** plan ($0/month)

**Advanced Settings (Optional):**
- **Environment Variables:** (None needed for basic setup)
- **Auto-Deploy:** ✅ Yes (enabled by default)

### 3.4 Create Web Service

1. Scroll down and click **"Create Web Service"**
2. Render will start building your app
3. Wait 2-5 minutes for the build to complete

---

## 📊 Step 4: Monitor Deployment

### 4.1 Watch the Build Logs

You'll see logs showing:
```
==> Installing dependencies...
==> Collecting flask>=3.0.0
==> Collecting numpy>=1.26.0
==> Collecting matplotlib>=3.8.0
==> Collecting gunicorn>=21.2.0
==> Successfully installed packages
==> Build successful!
==> Starting service...
```

### 4.2 Check Deployment Status

- ✅ **"Live"** (green) = Deployment successful!
- ⚠️ **"Build failed"** (red) = Check logs for errors
- 🔄 **"Deploying"** (yellow) = Build in progress

---

## 🎉 Step 5: Access Your App

Once deployed, Render will provide a URL like:

```
https://cso-simulator.onrender.com
```

Or your custom URL based on your chosen name.

### Test Your App:

1. Click the URL in the Render dashboard
2. Wait ~30 seconds for initial cold start (free tier)
3. Your CSO Simulator should load! 🐱✨

---

## 🔧 Troubleshooting

### Issue 1: Build Failed

**Solution:** Check the build logs for errors. Common issues:
- Missing dependencies in `requirements.txt`
- Python version mismatch
- Syntax errors in code

### Issue 2: App Crashes After Deployment

**Solution:** Check runtime logs in Render dashboard:
- Click "Logs" tab
- Look for Python errors
- Verify `gunicorn` is starting correctly

### Issue 3: Slow First Load (Cold Start)

**This is normal!** Free tier apps sleep after 15 minutes of inactivity.
- First request: ~30 seconds to wake up
- Subsequent requests: Fast
- **Solution:** Upgrade to paid tier for always-on, or accept the delay

### Issue 4: Static Files Not Loading

**Check:**
- Ensure `static/frames/` directory exists
- Flask is serving static files correctly
- Path in HTML is correct: `{{ url_for('static', filename='...') }}`

---

## 🔄 Step 6: Update Your App

### Automatic Deployments:

Render automatically redeploys when you push to GitHub!

```powershell
# Make changes to your code
git add .
git commit -m "Update: improved UI"
git push origin main

# Render automatically deploys the changes
```

### Manual Deploy:

In Render Dashboard:
1. Go to your service
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## ⚡ Performance Tips

### Free Tier Limitations:
- ⚠️ 512 MB RAM
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ Limited CPU
- ⚠️ Slower disk I/O

### Optimization Tips:
1. **Reduce simulation size** for cloud deployment
2. **Clear old frames** periodically to save disk space
3. **Limit max iterations** to avoid timeouts
4. **Consider upgrading** to paid tier ($7/month) for:
   - Always-on (no cold starts)
   - More RAM (512 MB → 2 GB+)
   - Faster performance

---

## 🎯 Final Checklist

- ✅ Code pushed to GitHub
- ✅ Render account created
- ✅ Web service configured
- ✅ Build successful
- ✅ App is live and accessible
- ✅ Simulation runs correctly
- ✅ Auto-deploy enabled

---

## 📞 Need Help?

**Render Documentation:**
- https://render.com/docs

**Render Community:**
- https://community.render.com

**Check Service Status:**
- https://status.render.com

---

## 🎊 Congratulations!

Your CSO Visual Simulator is now live on the internet! 🌍

Share your app URL with others:
```
https://your-app-name.onrender.com
```

Enjoy watching cats optimize the Rastrigin function in the cloud! 🐱✨

---

## 💰 Cost Breakdown

**Free Tier:**
- ✅ 750 hours/month (31 days × 24 hours = 744 hours)
- ✅ Enough for 1 app running 24/7
- ✅ **$0/month forever**

**Paid Tier (Optional):**
- Starter: $7/month
- Standard: $25/month
- Pro: $85/month

For this project, **Free tier is perfect!** 🎉
