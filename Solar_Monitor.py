import re
import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import time
from playwright.sync_api import Playwright, sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GITHUB_USERNAME = "GenergyDashboard"
GITHUB_REPO = "MuirCollege"
DATA_FILE = "solar_data.json"
CSV_DOWNLOAD_PATH = "downloads"
DATA_INTERVAL_MINUTES = 5

# Get credentials from environment variables
SOLAR_EMAIL = os.getenv('SOLAR_EMAIL')
SOLAR_PASSWORD = os.getenv('SOLAR_PASSWORD')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', SOLAR_PASSWORD)

# Validate credentials
if not SOLAR_EMAIL or not SOLAR_PASSWORD:
    raise ValueError("Missing credentials! Please set SOLAR_EMAIL and SOLAR_PASSWORD in .env file")

# Environmental Parameters
PARAMS = {
    "kg_co2_per_kwh": 1,
    "kg_co2_per_tree_per_year": 22,
    "trees_per_hectare_lower": 250,
    "trees_per_hectare_upper": 1000,
    "kwh_per_household_per_year": 3546.63,
    "kg_co2_per_km_driven": 0.251033,
    "kg_co2_per_km_flown": 12.280237,
    "kg_coal_per_kwh": 0.50802304,
    "litres_water_per_kwh": 1.4
}

# Persistent totals file
TOTALS_FILE = "persistent_totals.json"

def load_persistent_totals():
    """Load lifetime and monthly totals from file"""
    if os.path.exists(TOTALS_FILE):
        with open(TOTALS_FILE, 'r') as f:
            return json.load(f)
    else:
        now = datetime.now()
        return {
            "lifetime_total_kwh": 1063460,
            "month_start_total_kwh": 10091.928,
            "current_month": now.month,
            "current_year": now.year,
            "last_daily_total": 0,
            "last_update_date": now.strftime('%Y-%m-%d')
        }

def save_persistent_totals(totals):
    """Save lifetime and monthly totals to file"""
    with open(TOTALS_FILE, 'w') as f:
        json.dump(totals, f, indent=2)

def run_playwright(playwright: Playwright) -> str:
    """Run Playwright to download CSV data"""
    print("  → Launching browser...")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    
    try:
        print("  → Navigating to login page...")
        page.goto("https://pass.enerest.world/auth/realms/pass/protocol/openid-connect/auth?response_type=code&client_id=1d699ca7-87c8-4d6d-98dc-32a4cc316907&state=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&redirect_uri=https%3A%2F%2Fgenergy.enerest.world%2Findex.html&scope=openid%20profile&code_challenge=66CPKTUs7xUuUNmX1CvSRmQXO8ZllglERBHknop_ikg&code_challenge_method=S256&nonce=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&responseMode=query", 
                  timeout=60000)
        
        print("  → Waiting for page load...")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        print("  → Filling in credentials...")
        # Try multiple selectors for the email field
        email_selectors = [
            'input[type="text"]',
            'input[placeholder*="Mail" i]',
            'input[name*="mail" i]',
            'input[id*="mail" i]'
        ]
        
        email_filled = False
        for selector in email_selectors:
            try:
                page.locator(selector).first.fill(SOLAR_EMAIL, timeout=5000)
                print(f"  ✓ Email filled using selector: {selector}")
                email_filled = True
                break
            except:
                continue
        
        if not email_filled:
            raise Exception("Could not find email input field")
        
        page.wait_for_timeout(1000)
        
        # Try multiple selectors for password field
        password_selectors = [
            'input[type="password"]',
            'input[placeholder*="Pass" i]',
            'input[name*="pass" i]',
            'input[id*="pass" i]'
        ]
        
        password_filled = False
        for selector in password_selectors:
            try:
                page.locator(selector).first.fill(SOLAR_PASSWORD, timeout=5000)
                print(f"  ✓ Password filled using selector: {selector}")
                password_filled = True
                break
            except:
                continue
        
        if not password_filled:
            raise Exception("Could not find password input field")
        
        page.wait_for_timeout(1000)
        
        print("  → Clicking login button...")
        # Try multiple ways to click the login button
        login_clicked = False
        login_selectors = [
            'button:has-text("Anmelden")',
            'button[type="submit"]',
            'button:has-text("Log")',
            'input[type="submit"]'
        ]
        
        for selector in login_selectors:
            try:
                page.locator(selector).first.click(timeout=5000)
                print(f"  ✓ Login button clicked using selector: {selector}")
                login_clicked = True
                break
            except:
                continue
        
        if not login_clicked:
            raise Exception("Could not find login button")
        
        print("  → Waiting for login to complete...")
        page.wait_for_timeout(5000)
        
        print("  → Navigating to monitoring page...")
        page.goto("https://genergy.enerest.world/monitoring", timeout=60000)
        
        print("  → Waiting for page to fully load...")
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        
        print("  → Waiting for search component to be visible...")
        page.wait_for_selector("sds-global-search", state="visible", timeout=30000)
        page.wait_for_timeout(2000)
        
        print("  → Clicking search component...")
        page.locator("sds-global-search").click()
        page.wait_for_timeout(1000)
        
        print("  → Waiting for search field to be visible...")
        page.wait_for_selector("[data-test=\"global-search-field\"]", state="visible", timeout=10000)
        
        print("  → Filling search field with 'Muir'...")
        page.locator("[data-test=\"global-search-field\"]").fill("Muir")
        page.wait_for_timeout(2000)
        
        print("  → Waiting for insights button to appear...")
        page.wait_for_selector("button:has-text('insights')", state="visible", timeout=10000)
        
        print("  → Clicking insights button...")
        page.get_by_role("button").filter(has_text="insights").click()
        page.wait_for_timeout(5000)
        
        print("  → Waiting for insights page to fully load...")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        print(f"  → Setting data interval to {DATA_INTERVAL_MINUTES} minutes...")
        try:
            page.wait_for_selector("[data-test=\"interval-selector\"]", state="visible", timeout=10000)
            
            interval_selector = page.locator("[data-test=\"interval-selector\"]")
            if interval_selector.count() == 0:
                interval_selector = page.locator('[class*="interval"], [aria-label*="interval"], button:has-text("Min")').first
            
            interval_selector.click(timeout=5000)
            page.wait_for_timeout(1000)
            
            interval_option = page.get_by_role("option", name=f"{DATA_INTERVAL_MINUTES} Min")
            if interval_option.count() == 0:
                interval_option = page.locator(f'[role="option"]:has-text("{DATA_INTERVAL_MINUTES} Min"), li:has-text("{DATA_INTERVAL_MINUTES} Min")').first
            
            interval_option.click(timeout=5000)
            page.wait_for_timeout(5000)
            print(f"  ✓ Interval set to {DATA_INTERVAL_MINUTES} minutes")
        except Exception as e:
            print(f"  ⚠ Could not set interval (will use default): {e}")
        
        print("  → Waiting for data to reload...")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        print("  → Downloading CSV...")
        page.wait_for_selector("[data-test=\"menu-trigger\"]", state="visible", timeout=10000)
        page.locator("[data-test=\"menu-trigger\"]").click(timeout=5000)
        page.wait_for_timeout(2000)
        
        print("  → Waiting for CSV download...")
        page.wait_for_selector("[role=\"menuitem\"]:has-text('CSV')", state="visible", timeout=10000)
        
        with page.expect_download(timeout=30000) as download_info:
            page.get_by_role("menuitem", name="CSV").click(timeout=5000)
        
        download = download_info.value
        
        os.makedirs(CSV_DOWNLOAD_PATH, exist_ok=True)
        filepath = os.path.join(CSV_DOWNLOAD_PATH, f"solar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        download.save_as(filepath)
        
        print(f"  ✓ CSV downloaded: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"  ✗ Playwright error: {e}")
        try:
            screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            print(f"  → Screenshot saved: {screenshot_path}")
        except:
            pass
        raise
        
    finally:
        context.close()
        browser.close()

def parse_csv_data(filepath: str) -> dict:
    """Parse CSV and calculate all metrics with proper kWh calculation"""
    print("  → Parsing CSV data...")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("  ✗ No rows in CSV")
        return None
    
    print(f"  → Found {len(rows)} rows")
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    persistent = load_persistent_totals()
    
    today_str = now.strftime('%Y-%m-%d')
    is_new_day = persistent['last_update_date'] != today_str
    
    is_new_month = (persistent['current_month'] != now.month or 
                    persistent['current_year'] != now.year)
    
    current_power_w = 0
    latest_with_data = None
    
    print(f"  → CSV columns: {list(rows[0].keys())}")
    
    for row in reversed(rows):
        try:
            col_b_key = list(row.keys())[1] if len(row.keys()) > 1 else None
            
            if col_b_key:
                value_str = str(row[col_b_key]).replace('kWh', '').replace('kwh', '').replace('W', '').replace('w', '').replace(',', '').strip()
                
                if value_str and value_str.lower() not in ['none', 'null', '', '0']:
                    try:
                        power_value = float(value_str)
                        if power_value > 0 and power_value <= 100000:
                            current_power_w = power_value
                            latest_with_data = row
                            print(f"  → Found latest data in column '{col_b_key}': {current_power_w} W")
                            break
                    except:
                        pass
        except Exception as e:
            print(f"  → Could not parse row: {e}")
            continue
    
    if latest_with_data:
        print(f"  ✓ Latest row with data: {latest_with_data}")
    else:
        print(f"  ⚠ No valid data found in column B")
        latest_with_data = rows[-1]
    
    daily_total_kwh = 0
    
    for row in rows:
        try:
            timestamp = None
            timestamp_str = ""
            
            for key in row.keys():
                if key and ('time' in key.lower() or 'date' in key.lower()):
                    timestamp_str = row[key]
                    break
            
            if not timestamp_str:
                timestamp_str = list(row.values())[0]
            
            for fmt in ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M']:
                try:
                    timestamp = datetime.strptime(timestamp_str, fmt)
                    break
                except:
                    continue
            
            if not timestamp:
                continue
            
            power_w = 0
            for key in row.keys():
                if key and ('production' in key.lower() or 'power' in key.lower() or 'kwh' in key.lower()):
                    try:
                        value_str = str(row[key]).replace('kWh', '').replace('kwh', '').replace('W', '').replace('w', '').replace(',', '').strip()
                        if value_str:
                            power_w = float(value_str)
                            break
                    except:
                        pass
            
            energy_kwh = power_w / 1000.0
            
            if timestamp >= today_start:
                daily_total_kwh += energy_kwh
                
        except Exception as e:
            continue
    
    print(f"  → Daily total (today): {daily_total_kwh:.2f} kWh")
    
    if is_new_day:
        persistent['lifetime_total_kwh'] += persistent['last_daily_total']
        print(f"  → New day detected! Added {persistent['last_daily_total']:.2f} kWh to lifetime")
    
    if is_new_month:
        persistent['month_start_total_kwh'] = 0
        persistent['current_month'] = now.month
        persistent['current_year'] = now.year
        print(f"  → New month detected! Reset monthly total")
    
    persistent['last_daily_total'] = daily_total_kwh
    persistent['last_update_date'] = today_str
    
    lifetime_kwh = persistent['lifetime_total_kwh'] + daily_total_kwh
    monthly_kwh = persistent['month_start_total_kwh'] + daily_total_kwh
    
    save_persistent_totals(persistent)
    
    print(f"  → Monthly total: {monthly_kwh:.2f} kWh")
    print(f"  → Lifetime total: {lifetime_kwh:.2f} kWh")
    
    def calc_environmental_impact(kwh):
        co2_avoided = kwh * PARAMS["kg_co2_per_kwh"]
        trees_planted_lower = co2_avoided / (PARAMS["kg_co2_per_tree_per_year"] / PARAMS["trees_per_hectare_lower"])
        trees_planted_upper = co2_avoided / (PARAMS["kg_co2_per_tree_per_year"] / PARAMS["trees_per_hectare_upper"])
        households_powered = kwh / PARAMS["kwh_per_household_per_year"]
        km_driven = co2_avoided / PARAMS["kg_co2_per_km_driven"]
        km_flown = co2_avoided / PARAMS["kg_co2_per_km_flown"]
        coal_saved = kwh * PARAMS["kg_coal_per_kwh"]
        water_saved = kwh * PARAMS["litres_water_per_kwh"]
        
        return {
            "co2_avoided_kg": int(round(co2_avoided)),
            "trees_planted_lower": int(round(trees_planted_lower)),
            "trees_planted_upper": int(round(trees_planted_upper)),
            "households_powered": round(households_powered, 2),
            "km_driven_equivalent": int(round(km_driven)),
            "km_flown_equivalent": int(round(km_flown)),
            "coal_saved_kg": int(round(coal_saved)),
            "water_saved_litres": int(round(water_saved))
        }
    
    return {
        "timestamp": now.isoformat(),
        "current_power_w": int(round(current_power_w)),
        "current_power_kwh": round(current_power_w / 1000, 2),
        "daily_total_kwh": int(round(daily_total_kwh)),
        "monthly_total_kwh": int(round(monthly_kwh)),
        "lifetime_total_kwh": int(round(lifetime_kwh)),
        "daily_environmental": calc_environmental_impact(daily_total_kwh),
        "monthly_environmental": calc_environmental_impact(monthly_kwh),
        "lifetime_environmental": calc_environmental_impact(lifetime_kwh)
    }

def push_to_github(data: dict):
    """Push updated data to GitHub using credentials"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        subprocess.run(
            ["git", "add", DATA_FILE], 
            check=True, 
            capture_output=True,
            startupinfo=startupinfo
        )
        
        subprocess.run(
            ["git", "commit", "-m", f"Update solar data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], 
            check=True, 
            capture_output=True,
            startupinfo=startupinfo
        )
        
        github_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{GITHUB_REPO}.git"
        subprocess.run(
            ["git", "push", github_url, "main"], 
            check=True, 
            capture_output=True,
            startupinfo=startupinfo
        )
        
        print(f"  ✓ Data pushed to GitHub ({GITHUB_USERNAME}/{GITHUB_REPO})")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"  ✗ Git error: {error_msg}")
        try:
            subprocess.run(["git", "push"], check=True, capture_output=True, startupinfo=startupinfo)
            print(f"  ✓ Pushed using stored credentials")
        except:
            print(f"  ✗ Push failed. You may need to configure Git credentials.")

def main_loop():
    """Main loop - runs every 5 minutes with auto-restart on error"""
    print("☀️ Solar Monitor Started - Muir College Dashboard")
    print(f"Repository: {GITHUB_USERNAME}/{GITHUB_REPO}")
    print(f"Checking every 5 minutes...\n")
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching data...")
            
            with sync_playwright() as playwright:
                csv_file = run_playwright(playwright)
            
            data = parse_csv_data(csv_file)
            
            if data:
                print(f"\n📊 Results:")
                print(f"  Current Power: {data['current_power_w']:,} W".replace(',', ' '))
                print(f"  Daily Total: {data['daily_total_kwh']:,} kWh".replace(',', ' '))
                print(f"  Monthly Total: {data['monthly_total_kwh']:,} kWh".replace(',', ' '))
                print(f"  Lifetime Total: {data['lifetime_total_kwh']:,} kWh".replace(',', ' '))
                
                push_to_github(data)
                print(f"\n✓ Update complete!\n")
            else:
                print("✗ No data parsed\n")
            
            csv_files = sorted(Path(CSV_DOWNLOAD_PATH).glob("*.csv"))
            for old_file in csv_files[:-10]:
                old_file.unlink()
            
            screenshot_files = sorted(Path(".").glob("error_screenshot_*.png"))
            for old_screenshot in screenshot_files[:-5]:
                old_screenshot.unlink()
            
            print(f"Waiting 5 minutes until next check...")
            print("=" * 60 + "\n")
            time.sleep(300)
            
        except Exception as e:
            print(f"✗ Error occurred: {e}")
            print(f"⟳ Restarting immediately...\n")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
