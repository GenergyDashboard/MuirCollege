# Muir College Solar Dashboard

Automated solar generation monitoring dashboard powered by GitHub Actions. Data is scraped daily from the Genergy portal and displayed on a live dashboard.

## 🌟 Features

- ✅ **Automated Data Collection** - Runs daily via GitHub Actions after sunset
- ✅ **Real-time Dashboard** - Live generation statistics and environmental impact
- ✅ **Incremental Processing** - Only processes new data since last run
- ✅ **7-Day History** - Tracks daily generation for the past week
- ✅ **Environmental Impact** - CO₂ avoided, trees planted, households powered, etc.
- ✅ **GitHub Pages Hosting** - Free, fast, and reliable

The workflow runs automatically **3 times daily**:
- **10:00 AM SAST** (08:00 UTC)
- **3:00 PM SAST** (13:00 UTC)
- **8:00 PM SAST** (18:00 UTC)

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

## 📊 Data Flow

```
GitHub Actions (3x daily: 8:00, 13:00, 18:00 SAST)
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
- ✅ Not exposed in logs or code
- ✅ Client login credentials separate from scraper credentials
- ✅ CSV downloads and screenshots ignored by git

### Adjustable Schedule
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
---

**Powered by Genergy** | Automated with GitHub Actions | Built with ❤️
