# Muir College Solar Dashboard

Automated solar generation monitoring dashboard powered by GitHub Actions. Data is scraped daily from the Genergy portal and displayed on a live dashboard.

## 🌟 Features

- ✅ **Automated Data Collection** - Runs daily via GitHub Actions after sunset
- ✅ **Real-time Dashboard** - Live generation statistics and environmental impact
- ✅ **Incremental Processing** - Only processes new data since last run
- ✅ **7-Day History** - Tracks daily generation for the past week
- ✅ **Environmental Impact** - CO₂ avoided, trees planted, households powered, etc.
- ✅ **GitHub Pages Hosting** - Free, fast, and reliable

## 📋 Setup Instructions

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `MuirCollege`
3. Description: "Muir College Solar Generation Dashboard"
4. Set to **Public**
5. ✅ Check "Add a README file"
6. Click **Create repository**

### Step 2: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **root**
4. Click **Save**
5. Wait 2-3 minutes for deployment

### Step 3: Add GitHub Secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 2 secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SOLAR_EMAIL` | your_email@domain.com | Genergy portal login email |
| `SOLAR_PASSWORD` | your_password | Genergy portal password |

### Step 4: Upload Files

Upload all files from this folder to your GitHub repository:

```
.github/workflows/solar-data-update.yml
config.json
scraper.py
process_data.py
index.html
.gitignore
data/.gitkeep
data/daily/.gitkeep
README.md
```

**Method 1: Via GitHub Web Interface**
1. Click **Add file** → **Upload files**
2. Drag and drop all files
3. Click **Commit changes**

**Method 2: Via Git Command Line**
```bash
git clone https://github.com/GenergyDashboard/MuirCollege.git
cd MuirCollege
# Copy all files into this directory
git add .
git commit -m "Initial setup"
git push
```

### Step 5: Update config.json

Edit `config.json` and update:
- `installed_capacity_kwp` - Your system size in kWp
- `initial_values.lifetime_total_kwh` - Current lifetime total from your system
- `initial_values.month_start_total_kwh` - Total kWh at start of current month

### Step 6: Run First Workflow

1. Go to **Actions** tab
2. Click on "Update Solar Data" workflow
3. Click **Run workflow** dropdown
4. Click **Run workflow** button (green)
5. Wait 2-3 minutes for it to complete
6. Check for green ✅ checkmark

### Step 7: View Your Dashboard

Go to: `https://GenergyDashboard.github.io/MuirCollege/`

You should see:
- ✅ Current power generation
- ✅ Today/Month/Lifetime totals
- ✅ Environmental impact statistics

## 📅 Automated Schedule

The workflow runs automatically **3 times daily**:
- **10:00 AM SAST** (08:00 UTC)
- **3:00 PM SAST** (13:00 UTC)
- **8:00 PM SAST** (18:00 UTC)

You can also run it manually anytime from the Actions tab.

## 🗂️ File Structure

```
MuirCollege/
├── .github/
│   └── workflows/
│       └── solar-data-update.yml    # GitHub Actions workflow
├── data/
│   ├── solar_data.json              # Main data file (generated)
│   ├── persistent_totals.json       # Lifetime/monthly totals
│   ├── latest_csv_timestamp.json    # Last processed timestamp
│   ├── solar_export_latest.csv      # Latest CSV from scraper
│   ├── last_scrape.json             # Scraper status
│   └── daily/                       # Daily CSV archives
├── config.json                      # System configuration
├── scraper.py                       # Playwright web scraper
├── process_data.py                  # Data processor
├── index.html                       # Public dashboard
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 🔍 How It Works

### 1. **Scraper (scraper.py)**
- Launches headless Chromium browser
- Logs into Genergy portal with credentials from secrets
- Searches for "Muir" site
- Opens insights page
- Sets data interval to 5 minutes
- Downloads CSV file
- Saves to `data/solar_export_latest.csv`

### 2. **Processor (process_data.py)**
- Reads CSV file
- Parses timestamps and power values
- **Incremental processing**: Only processes NEW rows since last run
- Handles day/month transitions
- Calculates environmental impact
- Saves multiple JSON files for dashboard

### 3. **Dashboard (index.html)**
- Loads `solar_data.json`
- Displays generation statistics
- Shows environmental impact
- Yesterday's data in separate section
- Historical day selector (past 7 days)
- Auto-refreshes every minute

### 4. **Persistent Storage**
- `persistent_totals.json` - Lifetime and monthly totals
- `latest_csv_timestamp.json` - Last processed timestamp
- Prevents duplicate data processing
- Accumulates daily totals correctly

## 🔧 Troubleshooting

### Workflow Fails on First Run
- This is normal! Playwright needs to install browser dependencies
- Just run it again - it will succeed

### "No data in CSV" Error
- Check that credentials are correct
- Verify the "Muir" search finds your site
- Check CSV is being downloaded

### Dashboard Shows "Unable to load solar data"
- Wait a few minutes after first workflow run
- Check that `data/dashboard_data.json` was created
- Verify GitHub Pages is enabled

### Data Not Updating
- Check Actions tab for workflow errors
- Verify workflow ran successfully (green checkmark)
- Check that JSON files in data/ folder are updated

## 📊 Data Flow

```
GitHub Actions (3x daily: 8:00, 13:00, 18:00 UTC)
    ↓
scraper.py (Playwright automation)
    ↓
Download CSV → data/solar_export_latest.csv
    ↓
process_data.py (Parse & calculate)
    ↓
Generate solar_data.json (single output file)
    ↓
Commit & Push to GitHub
    ↓
GitHub Pages Auto-deploys
    ↓
Dashboard updates (index.html)
```

## 🔐 Security

- ✅ Credentials stored in GitHub Secrets (encrypted)
- ✅ Never exposed in logs or code
- ✅ Client login credentials separate from scraper credentials
- ✅ CSV downloads and screenshots ignored by git

## 📝 Maintenance

### Update System Configuration
Edit `config.json` and commit changes

### Change Client Credentials
Update GitHub Secrets: `CLIENT_USERNAME` and `CLIENT_PASSWORD`

### View Workflow Logs
Actions tab → Click on workflow run → Click on job step

### Manual Run
Actions tab → Update Solar Data → Run workflow

## 🎨 Customization

### Change Dashboard Branding
Edit `index.html`:
- Update title
- Change color scheme (CSS variables)
- Modify environmental impact cards

### Adjust Schedule
Edit `.github/workflows/solar-data-update.yml`:
```yaml
schedule:
  # 10:00 AM SAST = 08:00 UTC
  - cron: '0 8 * * *'
  # 3:00 PM SAST = 13:00 UTC
  - cron: '0 13 * * *'
  # 8:00 PM SAST = 18:00 UTC
  - cron: '0 18 * * *'
```

### Modify Environmental Factors
Edit `config.json` → `environmental_factors` section

## 📈 What's Tracked

- **Current Power** - Latest power reading in watts
- **Daily Total** - Accumulated generation today (resets at midnight)
- **Monthly Total** - Accumulated generation this month
- **Lifetime Total** - All-time generation
- **7-Day History** - Past week's daily totals
- **Environmental Impact**:
  - CO₂ avoided (kg)
  - Trees planted equivalent
  - Households powered (years)
  - km not driven
  - km not flown
  - Coal saved (kg)
  - Water saved (litres)

## ✅ Success Checklist

- [ ] Repository created and public
- [ ] GitHub Pages enabled
- [ ] 2 secrets added (SOLAR_EMAIL, SOLAR_PASSWORD)
- [ ] All files uploaded
- [ ] config.json updated with your values
- [ ] First workflow run successful (green checkmark)
- [ ] solar_data.json file created
- [ ] Dashboard loads at GitHub Pages URL
- [ ] Generation totals showing
- [ ] Environmental impact cards populated
- [ ] Yesterday's section showing data
- [ ] Day selector populated with past 7 days

## 🚀 Next Steps

1. Wait for sunset - workflow will run automatically
2. Check Actions tab next morning to verify it ran
3. View your dashboard at the GitHub Pages URL
4. Share the dashboard link with stakeholders!

## 📞 Support

If you encounter issues:
1. Check Actions tab for error messages
2. Verify all secrets are set correctly
3. Ensure CSV downloads successfully
4. Check config.json values are correct

---

**Powered by Genergy** | Automated with GitHub Actions | Built with ❤️
