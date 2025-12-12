# 🚀 Muir College - Complete Deployment Guide

## Method 1: Drag & Drop (EASIEST - 5 Minutes)

This is the fastest method. Upload everything at once!

### Step 1: Create Repository

1. Go to https://github.com/GenergyDashboard
2. Click **"New repository"** (green button)
3. Repository name: `MuirCollege`
4. Description: `Muir College Solar Generation Dashboard`
5. ✅ Set to **Public**
6. ✅ Check **"Add a README file"**
7. Click **"Create repository"**

### Step 2: Prepare Files

1. Download the `MuirCollege` folder from Claude
2. Unzip it if needed
3. Open the folder - you should see these files:

```
MuirCollege/
├── .github/
│   └── workflows/
│       └── solar-data-update.yml
├── data/
│   ├── .gitkeep
│   └── daily/
│       └── .gitkeep
├── config.json
├── index.html
├── process_data.py
├── scraper.py
├── requirements.txt
├── .gitignore
├── README.md
├── SETUP_GUIDE.md
└── QUICKSTART.md
```

### Step 3: Upload All Files at Once

1. In your GitHub repository, click **"Add file"** → **"Upload files"**
2. **Drag the ENTIRE contents** of the MuirCollege folder into the upload area
   - Make sure you drag the **contents** (not the folder itself)
   - You should see ALL files including the `.github` folder
3. Scroll down to the commit message box
4. Commit message: `Initial setup - Muir College solar dashboard`
5. Click **"Commit changes"** (green button)

**⏳ Wait 10-20 seconds for upload to complete**

### Step 4: Verify Upload

Check that you have this structure in your repo:

```
✅ .github/workflows/solar-data-update.yml
✅ data/.gitkeep
✅ data/daily/.gitkeep
✅ .gitignore
✅ config.json
✅ index.html
✅ process_data.py
✅ scraper.py
✅ requirements.txt
✅ README.md
✅ SETUP_GUIDE.md
✅ QUICKSTART.md
```

### Step 5: Add GitHub Secrets

1. In your repo, click **"Settings"** (top menu)
2. Left sidebar: **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"** (green button)

**Add Secret 1:**
- Name: `SOLAR_EMAIL`
- Value: `your_genergy_email@domain.com`
- Click **"Add secret"**

**Add Secret 2:**
- Name: `SOLAR_PASSWORD`
- Value: `your_genergy_password`
- Click **"Add secret"**

**✅ You should now see 2 secrets listed**

### Step 6: Update config.json

1. In your repo, click on **`config.json`**
2. Click the **pencil icon** (✏️) to edit
3. Update these 3 values:

```json
{
  "system": {
    "installed_capacity_kwp": YOUR_SYSTEM_SIZE,  ← Change this
    ...
  },
  "initial_values": {
    "lifetime_total_kwh": YOUR_LIFETIME_TOTAL,   ← Change this
    "month_start_total_kwh": MONTH_START_TOTAL,  ← Change this
    ...
  }
}
```

4. Scroll down and click **"Commit changes"**

### Step 7: Enable GitHub Pages

1. Click **"Settings"** (top menu)
2. Left sidebar: Click **"Pages"**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/ (root)**
4. Click **"Save"**

**✅ You'll see:** "Your site is live at https://GenergyDashboard.github.io/MuirCollege/"

### Step 8: Run First Workflow

1. Click **"Actions"** tab (top menu)
2. If you see a message about workflows, click **"I understand my workflows, go ahead and enable them"**
3. Left sidebar: Click **"Update Solar Data"**
4. Click **"Run workflow"** dropdown (right side)
5. Click **"Run workflow"** button (green)

**⏳ Wait 2-3 minutes**

6. Refresh the page
7. You should see a workflow run with a:
   - Yellow dot 🟡 (running)
   - Green checkmark ✅ (success)
   - Red X ❌ (failed - just run it again, first run often fails)

### Step 9: View Your Dashboard

1. Wait 2-3 minutes for GitHub Pages to deploy
2. Go to: `https://GenergyDashboard.github.io/MuirCollege/`

**✅ You should see:**
- Dark-themed dashboard
- Animated sun
- Generation totals
- Environmental impact cards
- Last updated timestamp

---

## Method 2: File-by-File Upload (For Precision)

If drag & drop doesn't work, upload files one by one in this order.

### Phase 1: Core Structure (Do First)

**1. Create .github/workflows folder structure:**

```
Click "Add file" → "Create new file"
Filename: .github/workflows/solar-data-update.yml
[Paste content from solar-data-update.yml]
Click "Commit changes"
```

**2. Create data folder structure:**

```
Click "Add file" → "Create new file"
Filename: data/.gitkeep
[Leave empty]
Click "Commit changes"
```

**3. Create data/daily folder:**

```
Click "Add file" → "Create new file"
Filename: data/daily/.gitkeep
[Leave empty]
Click "Commit changes"
```

### Phase 2: Configuration Files

**4. Upload .gitignore:**

```
Click "Add file" → "Create new file"
Filename: .gitignore
[Paste content from .gitignore]
Click "Commit changes"
```

**5. Upload config.json:**

```
Click "Add file" → "Create new file"
Filename: config.json
[Paste content from config.json]
[UPDATE the 3 values mentioned above]
Click "Commit changes"
```

**6. Upload requirements.txt:**

```
Click "Add file" → "Create new file"
Filename: requirements.txt
[Paste content from requirements.txt]
Click "Commit changes"
```

### Phase 3: Python Scripts

**7. Upload scraper.py:**

```
Click "Add file" → "Create new file"
Filename: scraper.py
[Paste content from scraper.py]
Click "Commit changes"
```

**8. Upload process_data.py:**

```
Click "Add file" → "Create new file"
Filename: process_data.py
[Paste content from process_data.py]
Click "Commit changes"
```

### Phase 4: Dashboard

**9. Upload index.html:**

```
Click "Add file" → "Create new file"
Filename: index.html
[Paste content from index.html]
Click "Commit changes"
```

### Phase 5: Documentation (Optional but Recommended)

**10. Upload README.md:**

```
Click "Add file" → "Create new file"
Filename: README.md
[Paste content from README.md]
Click "Commit changes"
```

**11. Upload SETUP_GUIDE.md:**

```
Click "Add file" → "Create new file"
Filename: SETUP_GUIDE.md
[Paste content from SETUP_GUIDE.md]
Click "Commit changes"
```

**12. Upload QUICKSTART.md:**

```
Click "Add file" → "Create new file"
Filename: QUICKSTART.md
[Paste content from QUICKSTART.md]
Click "Commit changes"
```

**Then continue with Steps 5-9 from Method 1 above**

---

## 📋 Pre-Flight Checklist

Before you start, have these ready:

- [ ] GitHub account logged in
- [ ] GenergyDashboard organization access
- [ ] Genergy portal email address
- [ ] Genergy portal password
- [ ] Your system's installed capacity (kWp)
- [ ] Current lifetime total (kWh)
- [ ] Month start total (kWh)

---

## 📁 File Upload Order (Quick Reference)

If using Method 2, upload in this exact order:

**Priority 1 - Must Upload First:**
1. `.github/workflows/solar-data-update.yml` - Workflow
2. `data/.gitkeep` - Data folder
3. `data/daily/.gitkeep` - Daily folder
4. `.gitignore` - Git ignore rules

**Priority 2 - Core Functionality:**
5. `config.json` - Configuration (UPDATE THIS!)
6. `requirements.txt` - Dependencies
7. `scraper.py` - Data collector
8. `process_data.py` - Data processor
9. `index.html` - Dashboard

**Priority 3 - Documentation (Optional):**
10. `README.md`
11. `SETUP_GUIDE.md`
12. `QUICKSTART.md`

---

## 🎯 What Each File Does

| File | Purpose | Can Skip? |
|------|---------|-----------|
| `.github/workflows/solar-data-update.yml` | Automation schedule | ❌ Required |
| `data/.gitkeep` | Creates data folder | ❌ Required |
| `data/daily/.gitkeep` | Creates daily folder | ❌ Required |
| `.gitignore` | Excludes sensitive files | ❌ Required |
| `config.json` | System settings | ❌ Required |
| `requirements.txt` | Python packages | ❌ Required |
| `scraper.py` | Downloads CSV | ❌ Required |
| `process_data.py` | Processes data | ❌ Required |
| `index.html` | Dashboard UI | ❌ Required |
| `README.md` | Documentation | ✅ Optional |
| `SETUP_GUIDE.md` | Setup help | ✅ Optional |
| `QUICKSTART.md` | Quick reference | ✅ Optional |

---

## ✅ Verification Steps

After uploading all files:

### Check 1: Files Present
Go to your repo homepage, verify you see:
```
✅ .github/
✅ data/
✅ .gitignore
✅ config.json
✅ index.html
✅ process_data.py
✅ requirements.txt
✅ scraper.py
```

### Check 2: Secrets Added
Settings → Secrets → Actions:
```
✅ SOLAR_EMAIL
✅ SOLAR_PASSWORD
```

### Check 3: Pages Enabled
Settings → Pages:
```
✅ Source: Deploy from a branch
✅ Branch: main
✅ Folder: / (root)
✅ Shows URL: https://GenergyDashboard.github.io/MuirCollege/
```

### Check 4: Workflow Runs
Actions tab:
```
✅ Workflows are enabled
✅ "Update Solar Data" workflow exists
✅ Can click "Run workflow"
```

### Check 5: Dashboard Loads
Open: `https://GenergyDashboard.github.io/MuirCollege/`
```
✅ Dark theme visible
✅ Animated sun
✅ "Loading solar data..." message
✅ After workflow runs: data appears
```

---

## 🐛 Common Issues & Fixes

### Issue: "Workflows aren't enabled"
**Fix:** 
- Actions tab → Click "I understand my workflows, go ahead and enable them"

### Issue: Drag & drop doesn't work
**Fix:** 
- Use Method 2 (file-by-file)
- Or try different browser (Chrome works best)

### Issue: Can't see .github folder
**Fix:**
- It's there! GitHub hides folders starting with "."
- Click on the folder name in file list to verify

### Issue: Pages shows 404
**Fix:**
- Wait 2-3 minutes for first deployment
- Check Settings → Pages shows green checkmark
- Workflow must run successfully first

### Issue: Dashboard shows "Loading..." forever
**Fix:**
- Workflow must run successfully first
- Check Actions tab for green checkmark
- Verify `solar_data.json` exists in repo
- Wait 2-3 minutes for Pages to update

### Issue: Workflow fails on first run
**Fix:**
- This is NORMAL (Playwright installs browser)
- Just click "Re-run all jobs"
- Second run will succeed

---

## 📞 Need Help?

### Stuck on Upload?
- Try Method 1 (drag & drop) first
- If that fails, use Method 2 (file-by-file)
- Make sure you're logged into GitHub

### Stuck on Secrets?
- Settings → Secrets and variables → Actions
- Click "New repository secret"
- Names must be EXACT: `SOLAR_EMAIL` and `SOLAR_PASSWORD`

### Stuck on Pages?
- Settings → Pages
- Source: Deploy from a branch
- Branch: main, Folder: / (root)
- Click Save
- Wait 2-3 minutes

### Stuck on Workflow?
- Actions tab
- Enable workflows if prompted
- Click "Update Solar Data"
- Click "Run workflow" → "Run workflow"
- Wait 2-3 minutes
- Green checkmark = success

---

## 🎉 Success!

Once everything is uploaded and configured:

✅ **Workflow runs automatically 3x daily** (10am, 3pm, 8pm SAST)
✅ **Dashboard updates automatically**
✅ **No maintenance required**
✅ **Data persists correctly**

**Your live dashboard:**
`https://GenergyDashboard.github.io/MuirCollege/`

---

**🚀 You're ready to go! Choose Method 1 for fastest setup, Method 2 for precision.**
