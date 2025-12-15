#!/usr/bin/env python3
"""
Muir College Solar Data Scraper for GitHub Actions
Automatically updates AUTH_STATE secret when cookies expire - ZERO MAINTENANCE!
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
            page.goto("https://genergy.enerest.world/monitoring", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            
            # Wait for network to settle
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except:
                print("  ⚠ Network still active (normal for SPAs), continuing...")
            
            # Give page extra time to fully render
            print("   Waiting for page to fully render...")
            page.wait_for_timeout(10000)
            
            # Handle potential "OK" button (notifications, cookie banners, etc.)
            try:
                ok_button = page.get_by_role("button", name="OK")
                if ok_button.is_visible(timeout=5000):
                    print("   → Clicking 'OK' button (notification/banner)...")
                    ok_button.click(timeout=3000)
                    page.wait_for_timeout(3000)
                    print("  ✓ OK button clicked")
            except:
                # OK button not present or not needed
                pass
            
            # Additional wait for UI to stabilize
            page.wait_for_timeout(5000)
            
            # NEW SIMPLIFIED METHOD: Click analysis panel → insights → Muir College
            print("   Navigating to Muir College via analysis panel...")
            
            # Click "insights" text within analysis panel
            print("   → Clicking analysis insights...")
            page.wait_for_selector("[data-test=\"analysis\"]", state="visible", timeout=20000)
            page.locator("[data-test=\"analysis\"]").get_by_text("insights").click(timeout=10000)
            page.wait_for_timeout(3000)
            
            # Click "Muir College" directly from the list
            print("   → Selecting Muir College...")
            page.wait_for_timeout(2000)  # Let list load
            page.get_by_text("Muir College").click(timeout=10000)
            page.wait_for_timeout(5000)  # Let insights page load
            
            # Wait for insights page to settle
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except:
                print("  ⚠ Network still active (normal for SPAs), continuing...")
            
            page.wait_for_timeout(3000)
            print("  ✓ Muir College insights loaded")
            
            # Download CSV
            print("   Downloading CSV...")
            page.wait_for_selector("[data-test=\"menu-trigger\"]", state="visible", timeout=15000)  # Increased from 10000
            page.locator("[data-test=\"menu-trigger\"]").click(timeout=8000)  # Increased from 5000
            page.wait_for_timeout(3000)  # Increased from 2000
            
            page.wait_for_selector("[role=\"menuitem\"]:has-text('CSV')", state="visible", timeout=15000)  # Increased from 10000
            
            with page.expect_download(timeout=45000) as download_info:  # Increased from 30000
                page.get_by_role("menuitem", name="CSV").click(timeout=8000)  # Increased from 5000
            
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
