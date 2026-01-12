#!/usr/bin/env python3
"""
Muir College Solar Data Scraper for GitHub Actions
Uses file-based auth state (same as 1st Avenue Spar) - ZERO MAINTENANCE!
"""

import os
import json
import base64
from datetime import datetime
from playwright.sync_api import sync_playwright

# Get credentials from environment variables (GitHub Secrets)
SOLAR_EMAIL = os.getenv('SOLAR_EMAIL')
SOLAR_PASSWORD = os.getenv('SOLAR_PASSWORD')

if not SOLAR_EMAIL or not SOLAR_PASSWORD:
    raise ValueError("Missing SOLAR_EMAIL or SOLAR_PASSWORD environment variables")

# Configuration
CSV_DOWNLOAD_PATH = "data/downloads"
LATEST_CSV_FILE = "data/solar_export_latest.csv"

def run_playwright():
    """Run Playwright to download CSV data from Genergy portal"""
    print("🤖 Starting Playwright browser automation...")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/daily', exist_ok=True)
    
    # Check for saved auth state (SAME AS 1ST AVENUE SPAR)
    use_auth_state = False
    auth_state_file = 'data/auth_state_encoded.txt'
    
    if os.path.exists(auth_state_file):
        try:
            print("🔓 Found saved authentication state")
            
            # Read and decode the auth state
            with open(auth_state_file, 'r') as f:
                encoded = f.read()
            
            auth_data = base64.b64decode(encoded).decode()
            
            # Save to temp file
            with open('auth_state_temp.json', 'w') as f:
                f.write(auth_data)
            
            use_auth_state = True
            print("✅ Using saved authentication state from repository")
        except Exception as e:
            print(f"⚠️  Could not use auth state: {e}")
            print("   Will login normally")
    else:
        print("ℹ️  No saved auth state found, will login normally")
    
    with sync_playwright() as p:
        print("   Launching Chromium browser...")
        
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        # Create context with or without saved state
        if use_auth_state and os.path.exists('auth_state_temp.json'):
            print("  ✓ Loaded auth state from file (skipping login)")
            context = browser.new_context(
                storage_state='auth_state_temp.json',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
        else:
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
        
        page = context.new_page()
        
        try:
            if use_auth_state:
                # Try to navigate directly to monitoring page
                print("   Navigating to monitoring page...")
                page.goto("https://genergy.enerest.world/monitoring", 
                         wait_until="domcontentloaded", 
                         timeout=60000)
                
                # Check if we're actually logged in
                import time
                time.sleep(3)
                current_url = page.url
                
                if "login" in current_url or "auth" in current_url:
                    print("  ⚠️  Saved session expired, logging in normally...")
                    use_auth_state = False
                else:
                    print("  ✓ Session still valid, skipping login")
            
            if not use_auth_state:
                # Normal login process (SAME AS COLLECTOR.PY)
                print("   Navigating to login page...")
                page.goto("https://pass.enerest.world/auth/realms/pass/protocol/openid-connect/auth?response_type=code&client_id=1d699ca7-87c8-4d6d-98dc-32a4cc316907&state=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&redirect_uri=https%3A%2F%2Fgenergy.enerest.world%2Findex.html&scope=openid%20profile&code_challenge=66CPKTUs7xUuUNmX1CvSRmQXO8ZllglERBHknop_ikg&code_challenge_method=S256&nonce=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&responseMode=query", 
                         wait_until="domcontentloaded", 
                         timeout=60000)
                
                import time
                time.sleep(2)
                
                # Fill in credentials with fallbacks (SAME AS COLLECTOR.PY)
                print("   Filling in credentials...")
                try:
                    page.get_by_role("textbox", name="Email").click(timeout=10000)
                    page.get_by_role("textbox", name="Email").fill(SOLAR_EMAIL)
                    print("  ✓ Email filled using role selector")
                except Exception as e:
                    print(f"  ⚠ Role selector failed, trying fallback: {e}")
                    page.locator('input[type="text"]').first.fill(SOLAR_EMAIL, timeout=5000)
                    print("  ✓ Email filled using fallback")
                
                time.sleep(1)
                
                try:
                    page.get_by_role("textbox", name="Password").click(timeout=10000)
                    page.get_by_role("textbox", name="Password").fill(SOLAR_PASSWORD)
                    print("  ✓ Password filled using role selector")
                except Exception as e:
                    print(f"  ⚠ Role selector failed, trying fallback: {e}")
                    page.locator('input[type="password"]').first.fill(SOLAR_PASSWORD, timeout=5000)
                    print("  ✓ Password filled using fallback")
                
                time.sleep(1)
                
                print("   Clicking login button...")
                try:
                    page.get_by_role("button", name="Log In").click(timeout=10000)
                    print("  ✓ Login button clicked using role selector")
                except Exception as e:
                    print(f"  ⚠ Role selector failed, trying fallback: {e}")
                    page.locator('button[type="submit"]').first.click(timeout=5000)
                    print("  ✓ Login button clicked using fallback")
                
                print("   Waiting for login to complete...")
                time.sleep(5)
                
                # Navigate to monitoring after login
                print("   Navigating to monitoring page...")
                page.goto("https://genergy.enerest.world/monitoring", 
                         wait_until="domcontentloaded", 
                         timeout=60000)
                
                time.sleep(3)
            
            # Now we're on the monitoring page
            print("   Waiting for page to fully render...")
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            
            import time
            time.sleep(5)
            
            # Navigate to Muir College (SAME AS COLLECTOR.PY)
            print("   Searching for Muir College...")
            
            try:
                print("   → Waiting for search component to be visible...")
                page.wait_for_selector("sds-global-search", state="visible", timeout=30000)
                time.sleep(2)
                
                print("   → Clicking search component...")
                page.locator("sds-global-search").click()
                time.sleep(1)
                
                print("   → Waiting for search field to be visible...")
                page.wait_for_selector("[data-test=\"global-search-field\"]", state="visible", timeout=10000)
                
                print("   → Filling search field with 'Muir'...")
                page.locator("[data-test=\"global-search-field\"]").fill("Muir")
                time.sleep(2)
                
                print("   → Waiting for insights button to appear...")
                page.wait_for_selector("button:has-text('insights')", state="visible", timeout=10000)
                
                print("   → Clicking insights button...")
                page.get_by_role("button").filter(has_text="insights").click()
                time.sleep(5)
                
                print("  ✓ Successfully navigated to Muir College insights")
                
            except Exception as e:
                print(f"  ✗ Navigation failed: {e}")
                raise Exception(f"Failed to navigate to Muir College: {e}")
            
            # Wait for insights page to settle
            print("   Waiting for insights page to fully load...")
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                print("  ⚠ Network still active (normal for SPAs), continuing...")
            
            time.sleep(3)
            print("  ✓ Muir College insights loaded")
            
            # Download CSV
            print("   Downloading CSV...")
            page.wait_for_selector("[data-test=\"menu-trigger\"]", state="visible", timeout=10000)
            page.locator("[data-test=\"menu-trigger\"]").click(timeout=5000)
            time.sleep(2)
            
            print("   Waiting for CSV download...")
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
            
            # Save the current auth state for next time (SAME AS 1ST AVENUE SPAR)
            if not use_auth_state:
                try:
                    import base64
                    
                    print("   💾 Saving authentication state for next run...")
                    
                    # Save as encoded text file
                    auth_json = context.storage_state()
                    encoded = base64.b64encode(json.dumps(auth_json).encode()).decode()
                    
                    with open('data/auth_state_encoded.txt', 'w') as f:
                        f.write(encoded)
                    
                    print("  ✓ Authentication state saved")
                    print("     This will skip login on next run!")
                except Exception as e:
                    print(f"  ⚠️  Could not save auth state: {e}")
            
            return LATEST_CSV_FILE
            
        except Exception as e:
            print(f"  ✗ Playwright error: {e}")
            
            # Take screenshot for debugging
            try:
                screenshot_path = f"data/error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"   Screenshot saved: {screenshot_path}")
            except:
                pass
            
            raise Exception(f"Failed to scrape: {e}")
            
        finally:
            # Cleanup temp file
            if os.path.exists('auth_state_temp.json'):
                os.remove('auth_state_temp.json')
            
            import time
            time.sleep(2)
            context.close()
            browser.close()
            print("   Browser closed")


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
