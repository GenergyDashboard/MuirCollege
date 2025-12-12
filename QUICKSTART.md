# 🎉 Muir College Solar Dashboard - UPDATED & READY!

## ✅ What's Been Updated

I've updated everything to match your exact requirements:

1. ✅ **Dark-themed dashboard** - Animated sun, no login/refresh buttons
2. ✅ **3x daily schedule** - Same as 1st Ave Spar (10am, 3pm, 8pm SAST)
3. ✅ **Single JSON file** - `solar_data.json` (not multiple files)
4. ✅ **Yesterday's section** - Separate card for yesterday's total
5. ✅ **Day selector** - Dropdown to view past 7 days (excluding yesterday)
6. ✅ **Info panel** - Detailed environmental calculations explanation
7. ✅ **Only 2 secrets needed** - No client credentials required

---

## 📦 Files Ready (11 Total)

### Core Files
1. **`.github/workflows/solar-data-update.yml`** - Runs 3x daily (10am, 3pm, 8pm SAST)
2. **`scraper.py`** - Playwright automation for Genergy portal
3. **`process_data.py`** - Generates single `solar_data.json` file
4. **`config.json`** - System configuration
5. **`index.html`** - Your exact dark-themed dashboard

### Documentation
6. **`README.md`** - Complete documentation (updated)
7. **`SETUP_GUIDE.md`** - Detailed setup instructions
8. **`requirements.txt`** - Python dependencies

### Git Files
9. **`.gitignore`** - Excludes sensitive files
10. **`data/.gitkeep`** - Tracks data folder
11. **`data/daily/.gitkeep`** - Tracks daily folder

---

## 🎯 Key Features

✅ **Automated 3x Daily Runs** (10am, 3pm, 8pm SAST)
- Same schedule as 1st Avenue Spar
- Keeps data fresh throughout the day

✅ **Dark Theme Dashboard**
- Animated floating sun
- Gold/yellow accent colors
- Genergy branding with animated gradient
- No login or refresh buttons (just auto-refresh)

✅ **Yesterday's Data**
- Dedicated card for yesterday's total
- Separate environmental impact section

✅ **Historical Day Selector**
- Dropdown showing past 7 days (excluding yesterday)
- Shows day name, date, and total kWh
- Click to see environmental impact for that day

✅ **Info Panel**
- Toggle button to show/hide
- Detailed explanation of all calculations
- Formulas for each metric

✅ **Single Data File**
- Generates `solar_data.json`
- Contains all data dashboard needs
- Simpler structure than 1st Ave Spar

---

## 🚀 5-Minute Setup

### 1. Create Repository
```
https://github.com/GenergyDashboard/MuirCollege
Public ✅
```

### 2. Add 2 GitHub Secrets
```
Settings → Secrets → Actions → New secret
```

| Secret Name | Value |
|-------------|-------|
| `SOLAR_EMAIL` | your_genergy_email@domain.com |
| `SOLAR_PASSWORD` | your_genergy_password |

**That's it! No client username/password needed!**

### 3. Upload All Files
- Drag entire MuirCollege folder contents
- Maintain folder structure (`.github/workflows/`, `data/`)

### 4. Enable GitHub Pages
```
Settings → Pages → main/root → Save
```

### 5. Update config.json
Edit these 3 values:
```json
{
  "system": {
    "installed_capacity_kwp": YOUR_SYSTEM_SIZE
  },
  "initial_values": {
    "lifetime_total_kwh": YOUR_LIFETIME_TOTAL,
    "month_start_total_kwh": MONTH_START_TOTAL
  }
}
```

### 6. Run First Workflow
```
Actions → Update Solar Data → Run workflow
```

### 7. View Dashboard
```
https://GenergyDashboard.github.io/MuirCollege/
```

---

## 📊 What the Dashboard Shows

### Main Cards (Top Row)
- 📅 **Yesterday's Total** - Previous day's generation
- 📅 **Today's Total** - Current day accumulation
- 📆 **This Month** - Monthly total
- ☀️ **Lifetime Total** - All-time generation

### Environmental Sections (Grid Layout)
Each section shows 7 metrics:
- 💨 CO₂ Avoided (kg)
- 🌳 Trees Equivalent
- 🏠 Households Powered (years)
- 🚗 km Driven Equivalent
- ✈️ km Flown Equivalent
- ⚫ Coal Saved (kg)
- 💧 Water Saved (litres)

**Sections:**
1. **Selected Day** (when dropdown is used)
2. **Yesterday**
3. **Today**
4. **This Month**
5. **Lifetime**

### Interactive Features
- **Hover over metrics** → Tooltip appears after 3 seconds
- **Info button** → Shows detailed calculation explanations
- **Day selector** → View any of past 7 days (excluding yesterday)
- **Auto-refresh** → Updates every minute

---

## 🔄 Schedule (Same as 1st Avenue Spar)

Runs **3 times daily**:
- **10:00 AM SAST** (08:00 UTC) - Morning update
- **3:00 PM SAST** (13:00 UTC) - Afternoon update
- **8:00 PM SAST** (18:00 UTC) - Evening update

---

## 📁 Generated Data Structure

After first successful run:

```
MuirCollege/
├── solar_data.json                 # ← Single output file for dashboard
├── data/
│   ├── solar_export_latest.csv     # Latest downloaded CSV
│   ├── persistent_totals.json      # Lifetime/monthly tracking
│   ├── latest_csv_timestamp.json   # Last processed timestamp
│   ├── last_scrape.json            # Scraper status
│   └── daily/                      # Daily CSV archives
```

### solar_data.json Structure
```json
{
  "timestamp": "2025-12-12T15:30:00",
  "plant_name": "Muir College",
  "location": "Port Elizabeth, South Africa",
  "yesterday_total_kwh": 450.25,
  "daily_total_kwh": 320.50,
  "monthly_total_kwh": 12500.00,
  "lifetime_total_kwh": 1054000.00,
  "yesterday_environmental": { ... },
  "daily_environmental": { ... },
  "monthly_environmental": { ... },
  "lifetime_environmental": { ... },
  "past_7_days": [
    {
      "date": "2025-12-11",
      "total_kwh": 450.25,
      "environmental": { ... }
    },
    ...
  ]
}
```

---

## 🆚 Muir College vs 1st Avenue Spar

| Feature | Muir College | 1st Avenue Spar |
|---------|--------------|-----------------|
| **Theme** | Dark (black/gold) | Light (white/gold) |
| **Login** | None | Client login available |
| **Yesterday** | Separate card | Not shown |
| **Day Selector** | Yes (past 7 days) | No |
| **Info Panel** | Yes (detailed) | No |
| **Schedule** | 3x daily | 3x daily ✅ |
| **Portal** | Genergy/Enerest | SolisCloud |
| **Data File** | solar_data.json | dashboard_data.json + others |
| **Secrets** | 2 | 4 (includes client creds) |

---

## ✅ Success Checklist

After setup, verify:

- [ ] Repository: `GenergyDashboard/MuirCollege` (public)
- [ ] 2 secrets added (SOLAR_EMAIL, SOLAR_PASSWORD)
- [ ] All 11 files uploaded
- [ ] GitHub Pages enabled
- [ ] config.json updated with your values
- [ ] First workflow run: green ✅
- [ ] `solar_data.json` file created
- [ ] Dashboard loads at GitHub Pages URL
- [ ] Dark theme with animated sun
- [ ] Yesterday's card showing data
- [ ] Day selector populated
- [ ] Environmental sections loaded
- [ ] Info panel toggle works
- [ ] Auto-refresh working (check timestamp)

---

## 🎨 Dashboard Features

### Animated Sun
- Floating animation (8-second cycle)
- Glowing shadow effect
- Radial gradient (yellow/gold)

### Genergy Branding
- Animated gradient sweep effect
- Green gradient appears every 6 seconds
- Links to https://genergy.co.za

### Day Selector
- Shows past 7 days (excludes yesterday - it has its own section)
- Format: "Day (DD/MM/YYYY) - XXX kWh"
- Click to load that day's environmental data

### Info Panel
- Toggle button (top right)
- Detailed calculation formulas
- Explains each environmental metric
- Smooth slide-down animation

### Tooltips
- Hover over any metric for 3 seconds
- Shows explanation of that metric
- Smooth fade-in animation

---

## 🔧 No Maintenance Required!

Once deployed:
- ✅ Runs automatically 3x daily
- ✅ No server to maintain
- ✅ No manual updates
- ✅ Data persists correctly
- ✅ Dashboard auto-refreshes

---

## 📊 Data Flow

```
GitHub Actions (3x daily: 08:00, 13:00, 18:00 UTC)
    ↓
scraper.py
    ↓ Login to Genergy
    ↓ Search "Muir"
    ↓ Open Insights
    ↓ Download CSV
    ↓
data/solar_export_latest.csv
    ↓
process_data.py
    ↓ Parse CSV (incremental)
    ↓ Calculate totals
    ↓ Generate environmental impact
    ↓
solar_data.json (single file)
    ↓
Git commit & push
    ↓
GitHub Pages deploy
    ↓
Dashboard updates (index.html)
```

---

## 🎯 What's Different from Your collector.py?

### Removed
- ❌ Infinite loop - GitHub Actions handles scheduling
- ❌ Sunset calculation - Using fixed 3x daily schedule
- ❌ Local file paths - Cloud-based paths
- ❌ `.env` file - Using GitHub Secrets
- ❌ Git operations in Python - GitHub Actions handles commits
- ❌ Multiple retry loops - GitHub Actions retries

### Kept
- ✅ Playwright automation logic
- ✅ CSV parsing
- ✅ Incremental processing (latest_csv_timestamp.json)
- ✅ Environmental calculations
- ✅ Persistent totals tracking
- ✅ 7-day history
- ✅ Day/month transitions

### Added
- ✅ GitHub Actions workflow
- ✅ GitHub Secrets integration
- ✅ Dark-themed dashboard
- ✅ Yesterday's section
- ✅ Day selector
- ✅ Info panel
- ✅ Animated UI elements

---

## 🐛 Troubleshooting

### Workflow Fails First Time
**Normal!** Playwright installs browser.
**Fix:** Just run it again.

### "Missing SOLAR_EMAIL" Error
**Check:** Secrets named exactly:
- `SOLAR_EMAIL` (not Solar_Email)
- `SOLAR_PASSWORD` (not Solar_Password)

### Dashboard Shows "Loading..."
**Wait:** 2-3 minutes after first workflow
**Check:** 
- solar_data.json exists in repo
- GitHub Pages is enabled
- File committed successfully

### Yesterday Shows 0
**Normal** on first day!
**Fix:** Wait until tomorrow, then yesterday will populate.

### Day Selector Empty
**Normal** on first week!
**Fix:** After 2-3 days, dropdown will populate with historical data.

---

## 📞 Next Steps

1. **Upload files** to GitHub
2. **Add 2 secrets** (SOLAR_EMAIL, SOLAR_PASSWORD)
3. **Enable Pages**
4. **Update config.json**
5. **Run workflow**
6. **View dashboard** at GitHub Pages URL
7. **Wait for 3x daily updates** to start

---

## 🎉 You're Ready!

The dashboard is **production-ready** and will look exactly like the HTML you provided:

✅ Dark theme with animated sun
✅ Yesterday's dedicated section
✅ Day selector for historical data
✅ Info panel with calculations
✅ No login/refresh buttons
✅ Auto-refresh every minute
✅ 3x daily automated updates

**Your Dashboard URL (after setup):**
`https://GenergyDashboard.github.io/MuirCollege/`

---

**Built with ❤️ | Powered by GitHub Actions | Automated 3x Daily**
