#!/usr/bin/env python3
"""
Muir College Solar Data Scraper for GitHub Actions
Adapted from collector.py to work with GitHub Actions workflow
"""

import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

# Get credentials from environment variables (GitHub Secrets)
SOLAR_EMAIL = os.getenv('SOLAR_EMAIL')
SOLAR_PASSWORD = os.getenv('SOLAR_PASSWORD')

if not SOLAR_EMAIL or not SOLAR_PASSWORD:
    raise ValueError("Missing SOLAR_EMAIL or SOLAR_PASSWORD environment variables")

# Configuration
DATA_INTERVAL_MINUTES = 5
CSV_DOWNLOAD_PATH = "data/downloads"
LATEST_CSV_FILE = "data/solar_export_latest.csv"

def run_playwright():
    """Run Playwright to download CSV data from Genergy portal"""
    print("🤖 Starting Playwright browser automation...")
    
    with sync_playwright() as p:
        print("   Launching Chromium browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            # Navigate to login page
            print("   Navigating to login page...")
            page.goto("https://pass.enerest.world/auth/realms/pass/protocol/openid-connect/auth?response_type=code&client_id=1d699ca7-87c8-4d6d-98dc-32a4cc316907&state=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&redirect_uri=https%3A%2F%2Fgenergy.enerest.world%2Findex.html&scope=openid%20profile&code_challenge=66CPKTUs7xUuUNmX1CvSRmQXO8ZllglERBHknop_ikg&code_challenge_method=S256&nonce=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&responseMode=query", 
                      timeout=60000)
            
            page.wait_for_load_state("networkidle", timeout=60000)
            page.wait_for_timeout(2000)
            
            # Fill in credentials
            print("   Filling in credentials...")
            try:
                page.get_by_role("textbox", name="Email").click(timeout=10000)
                page.get_by_role("textbox", name="Email").fill(SOLAR_EMAIL)
                print("  ✓ Email filled")
            except Exception as e:
                print(f"  ⚠ Email field error: {e}")
                # Fallback selectors
                email_selectors = ['input[type="text"]', 'input[placeholder*="Mail" i]']
                for selector in email_selectors:
                    try:
                        page.locator(selector).first.fill(SOLAR_EMAIL, timeout=5000)
                        print(f"  ✓ Email filled using selector: {selector}")
                        break
                    except:
                        continue
            
            page.wait_for_timeout(1000)
            
            # Fill password
            print("   Filling password...")
            try:
                page.get_by_role("textbox", name="Password").click(timeout=10000)
                page.get_by_role("textbox", name="Password").fill(SOLAR_PASSWORD)
                print("  ✓ Password filled")
            except Exception as e:
                print(f"  ⚠ Password field error: {e}")
                # Fallback selectors
                password_selectors = ['input[type="password"]', 'input[placeholder*="Pass" i]']
                for selector in password_selectors:
                    try:
                        page.locator(selector).first.fill(SOLAR_PASSWORD, timeout=5000)
                        print(f"  ✓ Password filled using selector: {selector}")
                        break
                    except:
                        continue
            
            page.wait_for_timeout(1000)
            
            # Click login button
            print("   Clicking login button...")
            try:
                page.get_by_role("button", name="Log In").click(timeout=10000)
                print("  ✓ Login button clicked")
            except Exception as e:
                print(f"  ⚠ Login button error: {e}")
                # Fallback selectors
                login_selectors = ['button:has-text("Log In")', 'button[type="submit"]']
                for selector in login_selectors:
                    try:
                        page.locator(selector).first.click(timeout=5000)
                        print(f"  ✓ Login clicked using selector: {selector}")
                        break
                    except:
                        continue
            
            print("   Waiting for login to complete...")
            page.wait_for_timeout(5000)
            
            # Navigate to monitoring page
            print("   Navigating to monitoring page...")
            page.goto("https://genergy.enerest.world/monitoring", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                print("  ⚠ Network still active (normal for SPAs), continuing...")
            
            page.wait_for_timeout(5000)
            
            # Search for Muir
            print("   Searching for 'Muir' site...")
            page.wait_for_selector("sds-global-search", state="visible", timeout=30000)
            page.wait_for_timeout(2000)
            
            page.locator("sds-global-search").click()
            page.wait_for_timeout(1000)
            
            page.wait_for_selector("[data-test=\"global-search-field\"]", state="visible", timeout=10000)
            page.locator("[data-test=\"global-search-field\"]").fill("Muir")
            page.wait_for_timeout(2000)
            
            # Click insights button
            print("   Opening insights page...")
            page.wait_for_selector("button:has-text('insights')", state="visible", timeout=10000)
            page.get_by_role("button").filter(has_text="insights").click()
            page.wait_for_timeout(5000)
            
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                print("  ⚠ Network still active (normal for SPAs), continuing...")
            
            page.wait_for_timeout(3000)
            
            # Set data interval
            print(f"   Setting data interval to {DATA_INTERVAL_MINUTES} minutes...")
            try:
                page.wait_for_selector("[data-test=\"interval-selector\"]", state="visible", timeout=10000)
                interval_selector = page.locator("[data-test=\"interval-selector\"]")
                interval_selector.click(timeout=5000)
                page.wait_for_timeout(1000)
                
                interval_option = page.get_by_role("option", name=f"{DATA_INTERVAL_MINUTES} Min")
                interval_option.click(timeout=5000)
                page.wait_for_timeout(5000)
                print(f"  ✓ Interval set to {DATA_INTERVAL_MINUTES} minutes")
            except Exception as e:
                print(f"  ⚠ Could not set interval (will use default): {e}")
            
            # Wait for data to reload
            page.wait_for_timeout(3000)
            
            # Download CSV
            print("   Downloading CSV...")
            page.wait_for_selector("[data-test=\"menu-trigger\"]", state="visible", timeout=10000)
            page.locator("[data-test=\"menu-trigger\"]").click(timeout=5000)
            page.wait_for_timeout(2000)
            
            page.wait_for_selector("[role=\"menuitem\"]:has-text('CSV')", state="visible", timeout=10000)
            
            with page.expect_download(timeout=30000) as download_info:
                page.get_by_role("menuitem", name="CSV").click(timeout=5000)
            
            download = download_info.value
            
            # Save the downloaded file
            os.makedirs(os.path.dirname(LATEST_CSV_FILE), exist_ok=True)
            download.save_as(LATEST_CSV_FILE)
            
            print(f"  ✓ CSV downloaded: {LATEST_CSV_FILE}")
            
            # Also save a dated copy
            os.makedirs(CSV_DOWNLOAD_PATH, exist_ok=True)
            dated_filepath = os.path.join(CSV_DOWNLOAD_PATH, f"solar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            download.save_as(dated_filepath)
            print(f"  ✓ Dated copy saved: {dated_filepath}")
            
            return LATEST_CSV_FILE
            
        except Exception as e:
            print(f"  ✗ Playwright error: {e}")
            try:
                screenshot_path = f"data/error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path)
                print(f"   Screenshot saved: {screenshot_path}")
            except:
                pass
            raise
            
        finally:
            context.close()
            browser.close()

def save_scrape_info(filepath):
    """Save information about the last successful scrape"""
    scrape_info = {
        "timestamp": datetime.now().isoformat(),
        "csv_file": filepath,
        "success": True
    }
    
    with open("data/last_scrape.json", 'w') as f:
        json.dump(scrape_info, f, indent=2)
    
    print(f"  ✓ Scrape info saved")

if __name__ == "__main__":
    print("=" * 60)
    print("🌞 MUIR COLLEGE SOLAR DATA SCRAPER")
    print("=" * 60)
    
    try:
        csv_file = run_playwright()
        save_scrape_info(csv_file)
        print("\n✅ Scraper completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Scraper failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        exit(1)
