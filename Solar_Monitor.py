import re
import os
import json
import csv
import sys
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
import subprocess
import time
from playwright.sync_api import Playwright, sync_playwright
from dotenv import load_dotenv
from suntime import Sun

# Load environment variables
load_dotenv()

# Configuration
GITHUB_USERNAME = "GenergyDashboard"
GITHUB_REPO = "MuirCollege"
DATA_FILE = "solar_data.json"
CSV_DOWNLOAD_PATH = "downloads"
DATA_INTERVAL_MINUTES = 5

# Location coordinates (set these to your location)
# Example: Muir College, UCSD coordinates
LATITUDE = 32.8801  # Replace with your latitude
LONGITUDE = -117.2340  # Replace with your longitude
SUNSET_OFFSET_MINUTES = 30  # Run this many minutes after sunset

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
LAST_RUN_FILE = "last_run.json"
LATEST_TIMESTAMP_FILE = "latest_csv_timestamp.json"

def get_sunset_time(lat, lon, date=None):
    """Calculate sunset time for given coordinates and date"""
    if date is None:
        date = datetime.now()
    
    sun = Sun(lat, lon)
    sunset = sun.get_local_sunset_time(date)
    return sunset

def should_run_today(force=False):
    """Check if we should run today based on last run date and sunset time"""
    if force:
        return True, datetime.now()
    
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    
    # Load last run info
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            last_run = json.load(f)
            last_run_date = last_run.get('last_run_date', '')
            
            # Already ran today
            if last_run_date == today_str:
                return False, None
    
    # Calculate today's sunset + offset
    sunset = get_sunset_time(LATITUDE, LONGITUDE)
    run_time = sunset + timedelta(minutes=SUNSET_OFFSET_MINUTES)
    
    # Check if it's past the run time
    if now >= run_time:
        return True, run_time
    
    return False, run_time

def mark_run_complete():
    """Mark today's run as complete"""
    now = datetime.now()
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump({
            'last_run_date': now.strftime('%Y-%m-%d'),
            'last_run_timestamp': now.isoformat()
        }, f, indent=2)

def load_persistent_totals():
    """Load lifetime and monthly totals from file"""
    if os.path.exists(TOTALS_FILE):
        try:
            with open(TOTALS_FILE, 'r') as f:
                data = json.load(f)
                print(f"  ✓ Loaded persistent totals from {TOTALS_FILE}")
                return data
        except json.JSONDecodeError as e:
            print(f"  ⚠ Corrupted {TOTALS_FILE}: {e}")
            print(f"  ↳ Backing up corrupted file and regenerating...")
            
            # Backup the corrupted file
            try:
                backup_path = f"{TOTALS_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(TOTALS_FILE, backup_path)
                print(f"  ↳ Backup saved to: {backup_path}")
            except Exception as backup_error:
                print(f"  ⚠ Could not backup: {backup_error}")
        except Exception as e:
            print(f"  ⚠ Error reading {TOTALS_FILE}: {e}")
    
    # Create fresh totals file
    now = datetime.now()
    fresh_totals = {
        "lifetime_total_kwh": 1053724.803,
        "month_start_total_kwh": 12057.838,
        "current_month": now.month,
        "current_year": now.year,
        "last_daily_total": 0,
        "last_update_date": now.strftime('%Y-%m-%d')
    }
    
    try:
        with open(TOTALS_FILE, 'w') as f:
            json.dump(fresh_totals, f, indent=2)
        print(f"  ✓ Created fresh {TOTALS_FILE}")
    except Exception as e:
        print(f"  ⚠ Could not write {TOTALS_FILE}: {e}")
    
    return fresh_totals

def save_persistent_totals(totals):
    """Save lifetime and monthly totals to file"""
    with open(TOTALS_FILE, 'w') as f:
        json.dump(totals, f, indent=2, ensure_ascii=True)

def load_latest_timestamp():
    """Load the latest timestamp we've already processed"""
    if os.path.exists(LATEST_TIMESTAMP_FILE):
        try:
            with open(LATEST_TIMESTAMP_FILE, 'r') as f:
                data = json.load(f)
                latest = data.get('latest_timestamp')
                if latest:
                    return datetime.fromisoformat(latest)
        except Exception as e:
            print(f"  ⚠ Could not load latest timestamp: {e}")
    return None

def save_latest_timestamp(timestamp):
    """Save the latest timestamp we've processed"""
    try:
        with open(LATEST_TIMESTAMP_FILE, 'w') as f:
            json.dump({
                'latest_timestamp': timestamp.isoformat(),
                'saved_at': datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        print(f"  ⚠ Could not save latest timestamp: {e}")

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
        page.wait_for_timeout(2000)
        
        print("  → Filling in credentials...")
        try:
            page.get_by_role("textbox", name="Email").click(timeout=10000)
            page.get_by_role("textbox", name="Email").fill(SOLAR_EMAIL)
            print("  ✓ Email filled using role selector")
        except Exception as e:
            print(f"  ⚠ Role selector failed, trying fallback: {e}")
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
        
        print("  → Filling password...")
        try:
            page.get_by_role("textbox", name="Password").click(timeout=10000)
            page.get_by_role("textbox", name="Password").fill(SOLAR_PASSWORD)
            print("  ✓ Password filled using role selector")
        except Exception as e:
            print(f"  ⚠ Role selector failed, trying fallback: {e}")
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
        try:
            page.get_by_role("button", name="Log In").click(timeout=10000)
            print("  ✓ Login button clicked using role selector")
        except Exception as e:
            print(f"  ⚠ Role selector failed, trying fallback: {e}")
            login_selectors = [
                'button:has-text("Log In")',
                'button:has-text("Anmelden")',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            login_clicked = False
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
        
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            print("  ⚠ Network still active (normal for SPAs), continuing...")
        
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
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            print("  ⚠ Network still active (normal for SPAs), continuing...")
        
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
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            print("  ⚠ Network still active (normal for SPAs), continuing...")
        
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
    """Parse CSV and calculate all metrics - INCREMENTAL VERSION"""
    print("  ↳ Parsing CSV data...")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("  ✗ No rows in CSV")
        return None
    
    print(f"  ↳ Found {len(rows)} rows in CSV")
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    persistent = load_persistent_totals()
    latest_processed = load_latest_timestamp()
    
    today_str = now.strftime('%Y-%m-%d')
    is_new_day = persistent['last_update_date'] != today_str
    
    is_new_month = (persistent['current_month'] != now.month or 
                    persistent['current_year'] != now.year)
    
    current_power_w = 0
    latest_with_data = None
    
    print(f"  ↳ CSV columns: {list(rows[0].keys())}")
    
    if latest_processed:
        print(f"  ↳ Last processed timestamp: {latest_processed.isoformat()}")
    else:
        print(f"  ↳ No previous timestamp found - processing all data from today")
    
    # Find current power from latest row
    for row in reversed(rows):
        try:
            col_b_key = None
            
            # Find the Production AC column
            for key in row.keys():
                if key and 'production' in key.lower() and 'ac' in key.lower():
                    col_b_key = key
                    break
            
            # Fallback: use second column if key not found
            if not col_b_key and len(row.keys()) > 1:
                col_b_key = list(row.keys())[1]
            
            if col_b_key:
                value_str = str(row[col_b_key]).replace('kWh', '').replace('kwh', '').replace('W', '').replace('w', '').replace(',', '').strip()
                
                if value_str and value_str.lower() not in ['none', 'null', '', '0']:
                    try:
                        power_value = float(value_str)
                        if power_value > 0 and power_value <= 100000:
                            current_power_w = power_value
                            latest_with_data = row
                            print(f"  ↳ Found latest data in column '{col_b_key}': {current_power_w} W")
                            break
                    except:
                        pass
        except Exception as e:
            print(f"  ↳ Could not parse row: {e}")
            continue
    
    if latest_with_data:
        print(f"  ✓ Latest row with data found")
    else:
        print(f"  ⚠ No valid data found in column B")
        latest_with_data = rows[-1]
    
    # Parse all rows with timestamps and power values
    parsed_rows = []
    newest_timestamp = latest_processed  # Track the newest timestamp we see
    
    for row in rows:
        try:
            timestamp = None
            timestamp_str = ""
            
            # Find timestamp column
            for key in row.keys():
                if key and ('time' in key.lower() or 'date' in key.lower()):
                    timestamp_str = row[key]
                    break
            
            if not timestamp_str:
                timestamp_str = list(row.values())[0]
            
            # Parse timestamp
            for fmt in ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M']:
                try:
                    timestamp = datetime.strptime(timestamp_str, fmt)
                    break
                except:
                    continue
            
            if not timestamp:
                continue
            
            # Extract power value from column B (Production AC)
            power_w = 0
            col_b_key = None
            
            # Find the Production AC column
            for key in row.keys():
                if key and 'production' in key.lower() and 'ac' in key.lower():
                    col_b_key = key
                    break
            
            # Fallback: use second column if key not found
            if not col_b_key and len(row.keys()) > 1:
                col_b_key = list(row.keys())[1]
            
            if col_b_key:
                try:
                    value_str = str(row[col_b_key]).replace('kWh', '').replace('kwh', '').replace('W', '').replace('w', '').replace(',', '').strip()
                    if value_str and value_str.lower() not in ['none', 'null', '']:
                        power_w = float(value_str)
                except:
                    pass
            
            # Only keep rows from TODAY with valid power > 0
            # AND only if they're after the latest processed timestamp
            if timestamp >= today_start and power_w > 0:
                if latest_processed is None or timestamp > latest_processed:
                    parsed_rows.append({
                        'timestamp': timestamp,
                        'power_w': power_w
                    })
                    
                    # Track the newest timestamp
                    if newest_timestamp is None or timestamp > newest_timestamp:
                        newest_timestamp = timestamp
        
        except Exception as e:
            continue
    
    print(f"  ↳ Found {len(parsed_rows)} NEW data points since last run")
    
    # Calculate total energy from new rows only
    daily_increment_kwh = 0
    
    for row in parsed_rows:
        # Each value is power in watts for the next 5 minutes (1/12 hour)
        # Energy = Power (kW) × Time (hours)
        # 5 minutes = 5/60 hours = 1/12 hours = 0.08333 hours
        energy_kwh = (row['power_w'] / 1000.0) * (5.0 / 60.0)
        daily_increment_kwh += energy_kwh
    
    print(f"  ↳ Calculated NEW daily increment: {daily_increment_kwh:.2f} kWh from {len(parsed_rows)} new readings")
    
    # Handle day/month transitions
    if is_new_day:
        persistent['lifetime_total_kwh'] += persistent['last_daily_total']
        persistent['month_start_total_kwh'] += persistent['last_daily_total']
        print(f"  ↳ New day detected! Added {persistent['last_daily_total']:.2f} kWh to lifetime and monthly")
    
    if is_new_month:
        persistent['current_month'] = now.month
        persistent['current_year'] = now.year
        persistent['month_start_total_kwh'] = 0
        print(f"  ↳ New month detected! Reset monthly total")
    
    # Update persistent totals with the increment, not replacement
    persistent['last_daily_total'] += daily_increment_kwh
    persistent['last_update_date'] = today_str
    
    # Save the latest timestamp we processed
    if newest_timestamp:
        save_latest_timestamp(newest_timestamp)
    
    save_persistent_totals(persistent)
    
    print(f"  ↳ Month start total: {persistent['month_start_total_kwh']:.2f} kWh")
    print(f"  ↳ Today's total (cumulative): {persistent['last_daily_total']:.2f} kWh")
    
    # Calculate cumulative totals
    lifetime_kwh = persistent['lifetime_total_kwh'] + persistent['last_daily_total']
    monthly_kwh = persistent['month_start_total_kwh'] + persistent['last_daily_total']
    
    print(f"  ↳ Monthly total: {monthly_kwh:.2f} kWh")
    print(f"  ↳ Lifetime total: {lifetime_kwh:.2f} kWh")
    
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
        "daily_total_kwh": int(round(persistent['last_daily_total'])),
        "monthly_total_kwh": int(round(monthly_kwh)),
        "lifetime_total_kwh": int(round(lifetime_kwh)),
        "daily_environmental": calc_environmental_impact(persistent['last_daily_total']),
        "monthly_environmental": calc_environmental_impact(monthly_kwh),
        "lifetime_environmental": calc_environmental_impact(lifetime_kwh)
    }

def push_to_github(data: dict):
    """Write solar data to JSON file and push to GitHub"""
    try:
        json_path = os.path.abspath(DATA_FILE)
        print(f"  → Writing JSON to: {json_path}")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"  ✓ JSON file updated successfully")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            written_data = json.load(f)
        
        written_timestamp = written_data.get('timestamp', 'UNKNOWN')
        print(f"  ✓ Timestamp: {written_timestamp}")
        
        print(f"  → Pushing to GitHub...")
        
        # Pull first to sync with remote changes
        try:
            print(f"  → Pulling latest changes from remote...")
            result = subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  ✓ Successfully synced with remote")
            else:
                print(f"  ⚠ Pull warning: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"  ⚠ Pull timeout, continuing anyway...")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠ Pull had issues, but continuing: {e.stderr}")
        
        # Add the data file
        subprocess.run(['git', 'add', DATA_FILE], 
                      check=True, capture_output=True, text=True)
        
        # Commit changes
        commit_message = f"Update solar data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            subprocess.run(['git', 'commit', '-m', commit_message], 
                          check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in e.stdout or "nothing to commit" in e.stderr:
                print(f"  ℹ No changes to commit (data unchanged)")
                return
            else:
                raise
        
        # Push to remote
        try:
            result = subprocess.run(['git', 'push'], 
                                   check=True, capture_output=True, text=True, timeout=30)
            print(f"  ✓ Pushed to GitHub successfully")
        except subprocess.CalledProcessError:
            # Try with set-upstream if regular push fails
            result = subprocess.run(['git', 'push', '--set-upstream', 'origin', 'main'], 
                                   check=True, capture_output=True, text=True, timeout=30)
            print(f"  ✓ Pushed to GitHub successfully (set upstream)")
        
        print(f"  ✓ File ready for GitHub Pages to serve")
        
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Git error: {e.stderr}")
        raise
    except Exception as e:
        print(f"  ✗ Error writing/pushing JSON: {e}")
        raise

def main_loop():
    """Main loop - runs once daily after sunset"""
    # Check for flags
    force_run = '--force' in sys.argv or '-f' in sys.argv
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    
    if test_mode:
        print("🧪 TEST MODE - Running without modifying persistent data\n")
        print("=" * 60)
        
        try:
            with sync_playwright() as playwright:
                csv_file = run_playwright(playwright)
            
            data = parse_csv_data(csv_file)
            
            if data:
                print(f"\n📊 Results (TEST MODE - NOT SAVED):")
                print(f"  Current Power: {data['current_power_w']:,} W".replace(',', ' '))
                print(f"  Daily Total: {data['daily_total_kwh']:,} kWh".replace(',', ' '))
                print(f"  Monthly Total: {data['monthly_total_kwh']:,} kWh".replace(',', ' '))
                print(f"  Lifetime Total: {data['lifetime_total_kwh']:,} kWh".replace(',', ' '))
                print(f"\n⚠️  NOTE: These values are calculated but NOT saved to persistent storage")
                print(f"✅ Test mode complete!")
            else:
                print("✗ No data parsed\n")
            
        except Exception as e:
            print(f"✗ Error during test run: {e}")
        
        return
    
    if force_run:
        print("🔧 FORCE RUN MODE - Running immediately and SAVING data\n")
        print("=" * 60)
        
        try:
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
                print(f"\n✅ Force run complete!")
                
                # Mark as complete
                mark_run_complete()
            else:
                print("✗ No data parsed\n")
            
        except Exception as e:
            print(f"✗ Error during force run: {e}")
        
        return
    
    # Normal sunset mode
    print("☀️ Solar Monitor Started - Daily Sunset Mode")
    print(f"Repository: {GITHUB_USERNAME}/{GITHUB_REPO}")
    print(f"Location: {LATITUDE}°, {LONGITUDE}°")
    print(f"Runs daily {SUNSET_OFFSET_MINUTES} minutes after sunset")
    print(f"Tips:")
    print(f"  - Use 'python Solar_Monitor.py --force' to run immediately (SAVES data)")
    print(f"  - Use 'python Solar_Monitor.py --test' to test without saving data\n")
    
    while True:
        try:
            should_run, run_time = should_run_today()
            now = datetime.now()
            
            if should_run:
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Running daily data fetch...")
                
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
                    print(f"\n✅ Daily update complete!")
                    
                    # Mark as complete
                    mark_run_complete()
                else:
                    print("✗ No data parsed\n")
                
                # Cleanup old files
                csv_files = sorted(Path(CSV_DOWNLOAD_PATH).glob("*.csv"))
                for old_file in csv_files[:-10]:
                    old_file.unlink()
                
                screenshot_files = sorted(Path(".").glob("error_screenshot_*.png"))
                for old_screenshot in screenshot_files[:-5]:
                    old_screenshot.unlink()
                
                # Calculate tomorrow's run time
                tomorrow = now + timedelta(days=1)
                tomorrow_sunset = get_sunset_time(LATITUDE, LONGITUDE, tomorrow)
                tomorrow_run = tomorrow_sunset + timedelta(minutes=SUNSET_OFFSET_MINUTES)
                
                wait_seconds = (tomorrow_run - now).total_seconds()
                wait_hours = wait_seconds / 3600
                
                print(f"\n⏰ Next run: {tomorrow_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   (in {wait_hours:.1f} hours)")
                print("=" * 60 + "\n")
                
                time.sleep(wait_seconds)
                
            else:
                if run_time:
                    wait_seconds = (run_time - now).total_seconds()
                    if wait_seconds > 0:
                        wait_minutes = wait_seconds / 60
                        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Waiting for sunset...")
                        print(f"  Sunset time: {run_time.strftime('%H:%M:%S')}")
                        print(f"  Time until run: {wait_minutes:.1f} minutes")
                        print("=" * 60 + "\n")
                        
                        # Check every 5 minutes
                        time.sleep(min(300, max(60, wait_seconds)))
                    else:
                        time.sleep(60)
                else:
                    # Already ran today, wait until tomorrow
                    tomorrow = now + timedelta(days=1)
                    tomorrow_sunset = get_sunset_time(LATITUDE, LONGITUDE, tomorrow)
                    tomorrow_run = tomorrow_sunset + timedelta(minutes=SUNSET_OFFSET_MINUTES)
                    
                    wait_seconds = (tomorrow_run - now).total_seconds()
                    wait_hours = wait_seconds / 3600
                    
                    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Already ran today")
                    print(f"  Next run: {tomorrow_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  (in {wait_hours:.1f} hours)")
                    print("=" * 60 + "\n")
                    
                    # Sleep for a few hours, then check again
                    time.sleep(min(3600, wait_seconds))
            
        except Exception as e:
            print(f"✗ Error occurred: {e}")
            print(f"⏳ Retrying in 5 minutes...\n")
            time.sleep(300)

if __name__ == "__main__":
    main_loop()
