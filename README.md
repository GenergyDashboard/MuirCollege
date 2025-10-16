# Muir College Solar Dashboard

Automated solar energy monitoring dashboard that tracks real-time and historical solar power generation data.

## Features

- 🌞 Real-time power generation monitoring
- 📊 Daily, monthly, and lifetime energy statistics
- 🌍 Environmental impact calculations (CO2 savings, tree equivalents, etc.)
- 🔄 Automatic data updates every 5 minutes
- 📈 Historical data tracking with CSV exports

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Git
- GitHub account

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/GenergyDashboard/MuirCollege.git
   cd MuirCollege
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure credentials:**
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your credentials:
     - `SOLAR_EMAIL`: Your solar monitoring portal email
     - `SOLAR_PASSWORD`: Your solar monitoring portal password
     - `GITHUB_TOKEN`: Your GitHub Personal Access Token

4. **Run the monitor:**
   ```bash
   python Solar_Monitor.py
   ```

## Security Notes

⚠️ **NEVER commit the `.env` file to GitHub!**

- All sensitive credentials are stored in `.env`
- `.env` is included in `.gitignore` to prevent accidental commits
- Use `.env.example` as a template (this is safe to commit)

## Data Output

The script generates `solar_data.json` with:
- Current power generation (W and kWh)
- Daily/monthly/lifetime totals
- Environmental impact metrics

## Environmental Impact Calculations

Based on solar energy generation, we calculate:
- CO2 emissions avoided
- Tree planting equivalents
- Households powered
- Coal saved
- Water saved
- Driving/flying distance equivalents

## License

MIT License - See LICENSE file for details
