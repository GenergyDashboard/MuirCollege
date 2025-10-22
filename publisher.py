"""
Solar Data Publisher - SAFE FOR PUBLIC GITHUB
This script only reads the sanitized solar_data.json and pushes it to GitHub.
NO credentials, NO login logic, NO sensitive information.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
REPO_PATH = r"C:\Users\Brandon\Documents\solar-dashboard"
DATA_FILE = "solar_data.json"  # Relative to repo


def validate_data(data):
    """
    Validate and sanitize data before publishing
    Ensures no sensitive information leaks
    """
    required_fields = [
        "timestamp",
        "current_power_w",
        "daily_total_kwh",
        "monthly_total_kwh",
        "lifetime_total_kwh"
    ]
    
    # Check all required fields exist
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Ensure no credential fields exist
    dangerous_fields = ["password", "email", "token", "key", "secret", "credential"]
    for field in data.keys():
        field_lower = str(field).lower()
        if any(danger in field_lower for danger in dangerous_fields):
            raise ValueError(f"Dangerous field detected: {field}")
    
    # Validate data types and ranges
    if not isinstance(data["current_power_w"], (int, float)):
        raise ValueError("Invalid current_power_w type")
    
    if data["current_power_w"] < 0 or data["current_power_w"] > 1000000:
        raise ValueError("Suspicious power value")
    
    return True


def check_data_exists():
    """Check if solar_data.json exists in repo"""
    data_path = Path(REPO_PATH) / DATA_FILE
    return data_path.exists()


def publish_to_github():
    """
    Push solar_data.json to GitHub
    Only commits if data has actually changed
    """
    try:
        print("=" * 60)
        print("SOLAR DATA PUBLISHER")
        print("=" * 60)
        
        # Check if data file exists
        if not check_data_exists():
            print(f"✗ {DATA_FILE} not found in repo")
            print(f"  Make sure collector has run and created the file")
            return False
        
        # Validate the data
        data_path = Path(REPO_PATH) / DATA_FILE
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        validate_data(data)
        print(f"✓ Data validated successfully")
        print(f"  Timestamp: {data.get('timestamp', 'UNKNOWN')}")
        print(f"  Current Power: {data.get('current_power_w', 0):,} W")
        
        # Change to repo directory
        import os
        os.chdir(REPO_PATH)
        
        # Check if data has changed
        result = subprocess.run(
            ['git', 'diff', '--name-only', DATA_FILE],
            capture_output=True, text=True, timeout=10
        )
        
        if DATA_FILE not in result.stdout:
            print(f"ℹ No changes detected - skipping push")
            return True
        
        print(f"→ Changes detected, preparing to push...")
        
        # Add only the data file
        subprocess.run(['git', 'add', DATA_FILE], 
                      capture_output=True, text=True, timeout=10)
        
        # Commit with timestamp
        commit_message = f"Update solar data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result = subprocess.run(['git', 'commit', '-m', commit_message],
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                print(f"ℹ Nothing to commit")
                return True
            else:
                print(f"✗ Commit failed: {result.stderr}")
                return False
        
        print(f"✓ Changes committed")
        
        # Pull latest changes from remote
        print(f"→ Syncing with remote...")
        result = subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'],
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"⚠ Pull warning: {result.stderr}")
        
        # Push to GitHub with retries
        max_retries = 3
        for attempt in range(max_retries):
            print(f"→ Pushing to GitHub (attempt {attempt + 1}/{max_retries})...")
            
            result = subprocess.run(['git', 'push', 'origin', 'main'],
                                   capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✓ Successfully pushed to GitHub!")
                print("=" * 60)
                return True
            
            if "rejected" in result.stderr and attempt < max_retries - 1:
                print(f"⚠ Push rejected, pulling and retrying...")
                subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'],
                              capture_output=True, text=True, timeout=30)
            else:
                print(f"✗ Push failed: {result.stderr}")
        
        print(f"✗ Failed to push after {max_retries} attempts")
        return False
        
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in {DATA_FILE}: {e}")
        return False
    except ValueError as e:
        print(f"✗ Data validation failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = publish_to_github()
    sys.exit(0 if success else 1)