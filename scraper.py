#!/usr/bin/env python3
"""
Muir College Solar Data Scraper for GitHub Actions
Automatically updates AUTH_STATE secret when cookies expire
"""

import os
import json
import base64
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from nacl import encoding, public

# Get credentials from environment variables (GitHub Secrets)
SOLAR_EMAIL = os.getenv('SOLAR_EMAIL')
SOLAR_PASSWORD = os.getenv('SOLAR_PASSWORD')
AUTH_STATE_SECRET = os.getenv('AUTH_STATE')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Automatically provided by GitHub Actions
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')  # Format: owner/repo

if not SOLAR_EMAIL or not SOLAR_PASSWORD:
    raise ValueError("Missing SOLAR_EMAIL or SOLAR_PASSWORD environment variables")

# Configuration
DATA_INTERVAL_MINUTES = 5
CSV_DOWNLOAD_PATH = "data/downloads"
LATEST_CSV_FILE = "data/solar_export_latest.csv"

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a secret using GitHub's public key"""
    public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def update_github_secret(secret_name: str, secret_value: str):
    """Update a GitHub repository secret via API"""
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("  ⚠ Cannot update secret: Missing GITHUB_TOKEN or GITHUB_REPOSITORY")
        return False
    
    try:
        owner, repo = GITHUB_REPOSITORY.split('/')
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get repository public key
        print(f"  → Getting repository public key...")
        pubkey_response = requests.get(
            f"{base_url}/actions/secrets/public-key",
            headers=headers
        )
        
        if pubkey_response.status_code != 200:
            print(f"  ✗ Failed to get public key: {pubkey_response.status_code}")
            return False
        
        pubkey_data = pubkey_response.json()
        public_key = pubkey_data['key']
        key_id = pubkey_data['key_id']
        
        # Encrypt the secret value
        print(f"  → Encrypting new auth state...")
        encrypted_value = encrypt_secret(public_key, secret_value)
        
        # Update the secret
        print(f"  → Updating {secret_name} secret...")
        update_response = requests.put(
            f"{base_url}/actions/secrets/{secret_name}",
            headers=headers,
            json={
                "encrypted_value": encrypted_value,
                "key_id": key_id
            }
        )
        
        if update_response.status_code in [201, 204]:
            print(f"  ✓ Successfully updated {secret_name} secret!")
            print("  ✓ Future runs will use new cookies automatically!")
            return True
        else:
            print(f"  ✗ Failed to update secret: {update_response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error updating secret: {e}")
        return False

def load_auth_state():
    """Load saved auth state from GitHub Secret"""
    if AUTH_STATE_SECRET:
        try:
            decoded = base64.b64decode(AUTH_STATE_SECRET).decode()
            storage_state = json.loads(decoded)
            print("  ✓ Loaded auth state from GitHub Secret (skipping login)")
            return storage_state
        except Exception as e:
            print(f"  ⚠ Could not load auth state from secret: {e}")
            print("  ↳ Will perform manual login and save new auth state")
    else:
        print("  ℹ No AUTH_STATE secret found, will perform manual login")
    return None

def save_auth_state_to_secret(context):
    """Save auth state to GitHub Secret after successful login"""
    try:
        print("\n" + "="*60)
        print("💾 SAVING NEW AUTH STATE TO GITHUB SECRET")
        print("="*60)
        
        # Get storage state
        storage_state = context.storage_state()
        auth_state_str = json.dumps(storage_state)
        encoded = base64.b64encode(auth_state_str.encode()).decode()
        
        # Update GitHub secret
        success = update_github_secret('AUTH_STATE', encoded)
        
        if success:
            print("="*60)
            print("🎉 AUTH STATE AUTO-UPDATED!")
            print("   Next run will skip login automatically!")
            print("="*60 + "\n")
        else:
            print("="*60)
            print("⚠️  Could not auto-update secret")
            print("   Copy this value and update AUTH_STATE manually:")
            print(f"\n{encoded[:100]}...")
            print("="*60 + "\n")
        
        return success
        
    except Exception as e:
        print(f"  ⚠ Could not save auth state: {e}")
        return False

def run_playwright():
    """Run Playwright to download CSV data from Genergy portal"""
    print("🤖 Starting Playwright browser automation...")
    
    with sync_playwright() as p:
        print("   Launching Chromium browser...")
        browser = p.chromium.launch(headless=True)
        
        # Load saved auth state if available
        storage_state = load_auth_state()
        
        if storage_state:
            # Use saved auth state
            context = browser.new_context(
                accept_downloads=True,
                storage_state=storage_state
            )
            skip_login = True
        else:
            # Fresh context
            context = browser.new_context(accept_downloads=True)
            skip_login = False
        
        page = context.new_page()
        
        try:
            if not skip_login:
                # Perform manual login
                print("   Navigating to login page...")
                page.goto("https://pass.enerest.world/auth/realms/pass/protocol/openid-connect/auth?response_type=code&client_id=1d699ca7-87c8-4d6d-98dc-32a4cc316907&state=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&redirect_uri=https%3A%2F%2Fgenergy.enerest.world%2Findex.html&scope=openid%20profile&code_challenge=66CPKTUs7xUuUNmX1CvSRmQXO8ZllglERBHknop_ikg&code_challenge_method=S256&nonce=S01PQVY4dnJ3cUdfY3l-YkRWbDZtRmNwY05PQ3BfcEZYclRqUnlIemN1ZXZq&responseMode=query", 
                          timeout=60000)
                
                page.wait_for_load_state("networkidle", timeout=60000)
                page.wait_for_timeout(2000)
                
                print("   Filling in credentials...")
                try:
                    page.get_by_role("textbox", name="Email").fill(SOLAR_EMAIL)
                    print("  ✓ Email filled")
                except Exception as e:
                    print(f"  ⚠ Email field error, trying fallback: {e}")
                    page.locator('input[type="text"]').first.fill(SOLAR_EMAIL, timeout=5000)
                
                page.wait_for_timeout(1000)
                
                try:
                    page.get_by_role("textbox", name="Password").fill(SOLAR_PASSWORD)
                    print("  ✓ Password filled")
                except Exception as e:
                    print(f"  ⚠ Password field error, trying fallback: {e}")
                    page.locator('input[type="password"]').first.fill(SOLAR_PASSWORD, timeout=5000)
                
                page.wait_for_timeout(1000)
                
                print("   Clicking login button...")
                try:
                    page.get_by_role("button", name="Log In").click(timeout=10000)
                    print("  ✓ Login button clicked")
                except Exception as e:
                    print(f"  ⚠ Login button error, trying fallback: {e}")
                    page.locator('button[type="submit"]').first.click(timeout=5000)
                
                print("   Waiting for login to complete...")
                page.wait_for_timeout(5000)
                
                # Save new auth state to GitHub Secret automatically!
                save_auth_state_to_secret(context)
            
            # Navigate to monitoring page
            print("   Navigating to monitoring page...")
            page.goto("https://genergy.enerest.world/monitoring", timeout=120000)  # INCREASED to 2 minutes
            page.wait_for_load_state("domcontentloaded", timeout=120000)  # INCREASED to 2 minutes
            
            try:
                page.wait_for_load_state("networkidle", timeout=40000)  # INCREASED to 40 seconds
            except:
                print("  ⚠ Network still active (normal for SPAs), continuing...")
            
            page.wait_for_timeout(12000)  # INCREASED to 12 seconds for safety
            
            # Check if we're actually on the monitoring page (auth check)
            current_url = page.url
            print(f"  ℹ Current URL: {current_url}")
            
            if "auth" in current_url or "login" in current_url:
                print("  ✗ Redirected to login page - AUTH_STATE has expired!")
                print("  ℹ Auth state needs to be refreshed. Performing login...")
                # The script should have already tried login if skip_login was False
                # If we're here, it means the saved auth state was invalid
                raise Exception("Auth state expired - saved cookies are no longer valid")
            
            print("  ✓ Successfully on monitoring page")
            
            # Search for Muir - with multiple fallback strategies
            print("   Searching for 'Muir' site...")
            
            # Take diagnostic screenshot
            try:
                diag_screenshot = f"data/before_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=diag_screenshot)
                print(f"  ℹ Diagnostic screenshot: {diag_screenshot}")
            except:
                pass
            
            # Try multiple selectors for the search component
            search_selectors = [
                "sds-global-search",
                "[data-test='global-search']",
                "input[placeholder*='Search']",
                "input[type='search']",
                "[class*='global-search']",
                "[class*='search-component']",
                "header input",
                ".search-input"
            ]
            
            search_found = False
            for selector in search_selectors:
                try:
                    print(f"  → Trying selector: {selector}")
                    element = page.locator(selector).first
                    
                    # Check if element exists
                    if element.count() > 0:
                        print(f"  ✓ Found search element with: {selector}")
                        
                        # Wait for it to be visible with longer timeout
                        element.wait_for(state="visible", timeout=60000)
                        page.wait_for_timeout(3000)
                        
                        # Try to click it
                        element.click(timeout=10000)
                        page.wait_for_timeout(2000)
                        search_found = True
                        break
                except Exception as e:
                    print(f"  ✗ Failed with {selector}: {e}")
                    continue
            
            if not search_found:
                print("  ⚠ Could not find search element with any selector!")
                print("  ℹ Dumping page content for diagnosis...")
                try:
                    html_dump = page.content()
                    with open("data/page_dump.html", "w", encoding="utf-8") as f:
                        f.write(html_dump)
                    print("  ✓ Page HTML saved to: data/page_dump.html")
                except:
                    pass
                
                raise Exception("Search element not found - page may not have loaded correctly or auth expired")
            
            # Now try to find and fill the search field
            print("  → Looking for search input field...")
            search_field_selectors = [
                "[data-test=\"global-search-field\"]",
                "input[placeholder*='Search']",
                "input[type='search']",
                "input[type='text']"
            ]
            
            field_found = False
            for selector in search_field_selectors:
                try:
                    field = page.locator(selector).first
                    if field.count() > 0:
                        field.wait_for(state="visible", timeout=30000)
                        field.fill("Muir")
                        page.wait_for_timeout(2000)
                        print(f"  ✓ Filled search field with: {selector}")
                        field_found = True
                        break
                except:
                    continue
            
            if not field_found:
                raise Exception("Could not find search input field")
            
            # Click insights button - with fallback selectors
            print("   Opening insights page...")
            
            insights_selectors = [
                "button:has-text('insights')",
                "button:has-text('Insights')",
                "[data-test='insights-button']",
                "a:has-text('insights')",
                "a:has-text('Insights')",
                "[href*='insights']",
                "button[aria-label*='insights']"
            ]
            
            insights_found = False
            for selector in insights_selectors:
                try:
                    print(f"  → Trying insights selector: {selector}")
                    btn = page.locator(selector).first
                    if btn.count() > 0:
                        btn.wait_for(state="visible", timeout=60000)
                        btn.click(timeout=10000)
                        page.wait_for_timeout(5000)
                        print(f"  ✓ Clicked insights with: {selector}")
                        insights_found = True
                        break
                except Exception as e:
                    print(f"  ✗ Failed with {selector}: {e}")
                    continue
            
            if not insights_found:
                print("  ⚠ Could not find insights button!")
                raise Exception("Insights button not found")
            
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
        
        # Check if it's an auth-related issue
        if "auth" in str(e).lower() or "expired" in str(e).lower():
            print("\n" + "="*60)
            print("🔑 AUTH STATE EXPIRED")
            print("="*60)
            print("The saved AUTH_STATE secret has expired.")
            print("SOLUTION: Delete the AUTH_STATE secret in GitHub:")
            print("  1. Go to: Settings → Secrets → Actions")
            print("  2. Delete the AUTH_STATE secret")
            print("  3. Next run will perform fresh login and save new cookies")
            print("="*60 + "\n")
        
        print("=" * 60)
        import traceback
        traceback.print_exc()
        exit(1)
