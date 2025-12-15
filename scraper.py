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

        print("  → Getting repository public key...")
        pubkey_response = requests.get(
            f"{base_url}/actions/secrets/public-key",
            headers=headers
        )

        if pubkey_response.status_code != 200:
            print(f"  ✗ Failed to get public key: {pubkey_response.status_code}")
            return False

        pubkey_data = pubkey_response.json()
        encrypted_value = encrypt_secret(pubkey_data['key'], secret_value)

        print(f"  → Updating {secret_name} secret...")
        update_response = requests.put(
            f"{base_url}/actions/secrets/{secret_name}",
            headers=headers,
            json={
                "encrypted_value": encrypted_value,
                "key_id": pubkey_data['key_id']
            }
        )

        if update_response.status_code in (201, 204):
            print(f"  ✓ Successfully updated {secret_name} secret!")
            return True

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
            print(f"  ⚠ Could not load auth state: {e}")
            print("  ↳ Will perform manual login")
    else:
        print("  ℹ No AUTH_STATE secret found, will perform manual login")
    return None


def save_auth_state_to_secret(context):
    """Save auth state to GitHub Secret"""
    storage_state = context.storage_state()
    encoded = base64.b64encode(json.dumps(storage_state).encode()).decode()
    update_github_secret("AUTH_STATE", encoded)


def run_playwright():
    print("🤖 Starting Playwright browser automation...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        storage_state = load_auth_state()
        context = browser.new_context(
            accept_downloads=True,
            storage_state=storage_state
        ) if storage_state else browser.new_context(accept_downloads=True)

        page = context.new_page()

        try:
            # LOGIN (only if needed)
            if not storage_state:
                print("   Navigating to login page...")
                page.goto(
                    "https://pass.enerest.world/auth/realms/pass/protocol/openid-connect/auth",
                    timeout=60000
                )

                page.get_by_role("textbox", name="Email").fill(SOLAR_EMAIL)
                page.get_by_role("textbox", name="Password").fill(SOLAR_PASSWORD)
                page.get_by_role("button", name="Log In").click()

                page.wait_for_load_state("networkidle", timeout=60000)
                save_auth_state_to_secret(context)

            # MONITORING PAGE
            print("   Navigating to monitoring page...")
            page.goto("https://genergy.enerest.world/monitoring", timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass

            page.wait_for_timeout(8000)

            # Click OK banner if present
            try:
                ok = page.get_by_role("button", name="OK")
                if ok.is_visible():
                    ok.click()
                    page.wait_for_timeout(3000)
            except:
                pass

            # ===============================
            # ✅ FIXED INSIGHTS NAVIGATION
            # ===============================
            print("   Navigating to Muir College via Insights...")

            print("   → Clicking Insights...")
            page.get_by_text("Insights", exact=False).click(timeout=15000)

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except:
                pass

            print("   → Waiting for Muir College...")
            page.get_by_text("Muir College", exact=False).wait_for(timeout=20000)

            print("   → Selecting Muir College...")
            page.get_by_text("Muir College", exact=False).click(timeout=10000)

            page.wait_for_timeout(5000)
            print("  ✓ Muir College insights loaded")

            # DOWNLOAD CSV
            print("   Downloading CSV...")
            page.wait_for_selector('[data-test="menu-trigger"]', timeout=15000)
            page.locator('[data-test="menu-trigger"]').click()

            page.wait_for_selector('[role="menuitem"]:has-text("CSV")', timeout=15000)

            with page.expect_download(timeout=45000) as download_info:
                page.get_by_role("menuitem", name="CSV").click()

            download = download_info.value

            os.makedirs(os.path.dirname(LATEST_CSV_FILE), exist_ok=True)
            download.save_as(LATEST_CSV_FILE)

            os.makedirs(CSV_DOWNLOAD_PATH, exist_ok=True)
            dated = os.path.join(
                CSV_DOWNLOAD_PATH,
                f"solar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            download.save_as(dated)

            print(f"  ✓ CSV saved: {LATEST_CSV_FILE}")
            print(f"  ✓ Dated copy saved: {dated}")

            return LATEST_CSV_FILE

        except Exception as e:
            screenshot = f"data/error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot)
            print(f"  ✗ Error occurred, screenshot saved: {screenshot}")
            raise

        finally:
            context.close()
            browser.close()


def save_scrape_info(filepath):
    with open("data/last_scrape.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "csv_file": filepath,
            "success": True
        }, f, indent=2)


if __name__ == "__main__":
    print("=" * 60)
    print("🌞 MUIR COLLEGE SOLAR DATA SCRAPER")
    print("=" * 60)

    try:
        csv_file = run_playwright()
        save_scrape_info(csv_file)
        print("\n✅ Scraper completed successfully!")
    except Exception as e:
        print(f"\n❌ Scraper failed: {e}")
        raise
