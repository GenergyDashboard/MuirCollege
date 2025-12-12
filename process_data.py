#!/usr/bin/env python3
"""
Muir College Solar Data Processor
Processes CSV data and generates JSON files for the dashboard
"""

import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

# File paths
CONFIG_FILE = "config.json"
CSV_FILE = "data/solar_export_latest.csv"
PERSISTENT_TOTALS_FILE = "data/persistent_totals.json"
LATEST_TIMESTAMP_FILE = "data/latest_csv_timestamp.json"
SOLAR_DATA_FILE = "solar_data.json"  # Single output file for the dashboard

def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_persistent_totals(config):
    """Load or initialize persistent totals"""
    if os.path.exists(PERSISTENT_TOTALS_FILE):
        try:
            with open(PERSISTENT_TOTALS_FILE, 'r') as f:
                data = json.load(f)
                print(f"  ✓ Loaded persistent totals")
                
                # Ensure daily_history exists
                if 'daily_history' not in data:
                    data['daily_history'] = []
                
                return data
        except Exception as e:
            print(f"  ⚠ Error loading persistent totals: {e}")
    
    # Create fresh totals
    now = datetime.now()
    initial = config['initial_values']
    fresh_totals = {
        "lifetime_total_kwh": initial['lifetime_total_kwh'],
        "month_start_total_kwh": initial['month_start_total_kwh'],
        "current_month": now.month,
        "current_year": now.year,
        "last_daily_total": 0,
        "last_update_date": now.strftime('%Y-%m-%d'),
        "daily_history": []
    }
    
    print(f"  ✓ Created fresh persistent totals")
    return fresh_totals

def save_persistent_totals(totals):
    """Save persistent totals"""
    with open(PERSISTENT_TOTALS_FILE, 'w') as f:
        json.dump(totals, f, indent=2)

def load_latest_timestamp():
    """Load the latest timestamp we've already processed"""
    if os.path.exists(LATEST_TIMESTAMP_FILE):
        try:
            with open(LATEST_TIMESTAMP_FILE, 'r') as f:
                data = json.load(f)
                latest = data.get('latest_timestamp')
                if latest:
                    ts = datetime.fromisoformat(latest)
                    print(f"  ✓ Latest timestamp: {ts.isoformat()}")
                    return ts
        except Exception as e:
            print(f"  ⚠ Could not load latest timestamp: {e}")
    print(f"  ↳ No previous timestamp found")
    return None

def save_latest_timestamp(timestamp):
    """Save the latest timestamp we've processed"""
    with open(LATEST_TIMESTAMP_FILE, 'w') as f:
        json.dump({
            'latest_timestamp': timestamp.isoformat(),
            'saved_at': datetime.now().isoformat()
        }, f, indent=2)

def calc_environmental_impact(kwh, params):
    """Calculate environmental impact metrics"""
    co2_avoided = kwh * params["kg_co2_per_kwh"]
    trees_planted = int(round(co2_avoided / params["kg_co2_per_tree_per_year"]))
    households_powered = kwh / params["kwh_per_household_per_year"]
    km_driven = co2_avoided / params["kg_co2_per_km_driven"]
    km_flown = co2_avoided / params["kg_co2_per_km_flown"]
    coal_saved = kwh * params["kg_coal_per_kwh"]
    water_saved = kwh * params["litres_water_per_kwh"]

    return {
        "co2_avoided_kg": int(round(co2_avoided)),
        "trees_planted": trees_planted,
        "households_powered": round(households_powered, 2),
        "km_driven_equivalent": int(round(km_driven)),
        "km_flown_equivalent": int(round(km_flown)),
        "coal_saved_kg": int(round(coal_saved)),
        "water_saved_litres": int(round(water_saved))
    }

def parse_csv_data(config):
    """Parse CSV and calculate all metrics - INCREMENTAL VERSION"""
    print("📊 Processing CSV data...")
    
    params = config['environmental_factors']
    
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("  ✗ No rows in CSV")
        return None

    print(f"  ↳ Found {len(rows)} rows in CSV")

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    persistent = load_persistent_totals(config)
    latest_processed = load_latest_timestamp()

    today_str = now.strftime('%Y-%m-%d')
    is_new_day = persistent.get('last_update_date', '') != today_str

    is_new_month = (persistent.get('current_month') != now.month or
                    persistent.get('current_year') != now.year)

    current_power_w = 0
    latest_with_data = None

    print(f"  ↳ CSV columns: {list(rows[0].keys())}")

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
                            print(f"  ↳ Current power: {current_power_w} W")
                            break
                    except:
                        pass
        except Exception as e:
            continue

    # Parse all rows with timestamps and power values
    parsed_rows = []
    newest_timestamp = latest_processed

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

            # Extract power value
            power_w = 0
            col_b_key = None

            for key in row.keys():
                if key and 'production' in key.lower() and 'ac' in key.lower():
                    col_b_key = key
                    break

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
            if timestamp >= today_start and power_w > 0:
                if latest_processed is None or timestamp > latest_processed:
                    parsed_rows.append({
                        'timestamp': timestamp,
                        'power_w': power_w
                    })

                    if newest_timestamp is None or timestamp > newest_timestamp:
                        newest_timestamp = timestamp

        except Exception:
            continue

    print(f"  ↳ Found {len(parsed_rows)} NEW data points since last run")

    # Calculate total energy from new rows only
    daily_increment_kwh = 0.0
    data_interval_hours = config['system']['data_interval_minutes'] / 60.0

    for row in parsed_rows:
        # Energy = Power (kW) × Time (hours)
        energy_kwh = (row['power_w'] / 1000.0) * data_interval_hours
        daily_increment_kwh += energy_kwh

    print(f"  ↳ NEW daily increment: {daily_increment_kwh:.2f} kWh from {len(parsed_rows)} readings")

    # Handle day/month transitions
    if is_new_day:
        yesterday_total = persistent.get('last_daily_total', 0)
        persistent['lifetime_total_kwh'] += yesterday_total
        persistent['month_start_total_kwh'] += yesterday_total
        print(f"  ↳ New day! Added {yesterday_total:.2f} kWh to lifetime and monthly")
        
        # Add yesterday to daily history
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_env = calc_environmental_impact(yesterday_total, params)
        
        history_entry = {
            "date": yesterday,
            "total_kwh": round(yesterday_total, 2),
            "environmental": yesterday_env
        }
        
        daily_history = persistent.get('daily_history', [])
        daily_history.append(history_entry)
        daily_history = daily_history[-7:]  # Keep only last 7 days
        persistent['daily_history'] = daily_history
        
        print(f"  ↳ Added {yesterday} to daily history ({yesterday_total:.2f} kWh)")

        # Reset daily counter
        persistent['last_daily_total'] = 0.0

    if is_new_month:
        persistent['current_month'] = now.month
        persistent['current_year'] = now.year
        persistent['month_start_total_kwh'] = 0.0
        print(f"  ↳ New month! Reset monthly total")

    # Update persistent totals
    persistent['last_daily_total'] = persistent.get('last_daily_total', 0.0) + daily_increment_kwh
    persistent['last_update_date'] = today_str

    # Save the latest timestamp
    if newest_timestamp:
        save_latest_timestamp(newest_timestamp)

    save_persistent_totals(persistent)

    # Calculate cumulative totals
    lifetime_kwh = persistent['lifetime_total_kwh'] + persistent['last_daily_total']
    monthly_kwh = persistent['month_start_total_kwh'] + persistent['last_daily_total']

    print(f"  ↳ Today's total: {persistent['last_daily_total']:.2f} kWh")
    print(f"  ↳ Monthly total: {monthly_kwh:.2f} kWh")
    print(f"  ↳ Lifetime total: {lifetime_kwh:.2f} kWh")

    # Get yesterday's data
    yesterday_data = persistent.get('daily_history', [])[-1] if persistent.get('daily_history', []) else None

    return {
        "timestamp": now.isoformat(),
        "current_power_w": int(round(current_power_w)),
        "current_power_kwh": round(current_power_w / 1000, 2),
        "daily_total_kwh": round(persistent['last_daily_total'], 2),
        "monthly_total_kwh": round(monthly_kwh, 2),
        "lifetime_total_kwh": round(lifetime_kwh, 2),
        "daily_environmental": calc_environmental_impact(persistent['last_daily_total'], params),
        "monthly_environmental": calc_environmental_impact(monthly_kwh, params),
        "lifetime_environmental": calc_environmental_impact(lifetime_kwh, params),
        "past_7_days": persistent.get('daily_history', []),
        "yesterday_total_kwh": yesterday_data['total_kwh'] if yesterday_data else 0,
        "yesterday_environmental": yesterday_data['environmental'] if yesterday_data else calc_environmental_impact(0, params)
    }

def save_solar_data(data, config):
    """Save all data to a single solar_data.json file for the dashboard"""
    solar_data = {
        "timestamp": data["timestamp"],
        "plant_name": config['system']['plant_name'],
        "location": config['system']['location'],
        "yesterday_total_kwh": data["yesterday_total_kwh"],
        "daily_total_kwh": data["daily_total_kwh"],
        "monthly_total_kwh": data["monthly_total_kwh"],
        "lifetime_total_kwh": data["lifetime_total_kwh"],
        "yesterday_environmental": data["yesterday_environmental"],
        "daily_environmental": data["daily_environmental"],
        "monthly_environmental": data["monthly_environmental"],
        "lifetime_environmental": data["lifetime_environmental"],
        "past_7_days": data["past_7_days"]
    }
    
    with open(SOLAR_DATA_FILE, 'w') as f:
        json.dump(solar_data, f, indent=2)
    print(f"  ✓ Solar data saved to {SOLAR_DATA_FILE}")

if __name__ == "__main__":
    print("=" * 60)
    print("⚙️  MUIR COLLEGE DATA PROCESSOR")
    print("=" * 60)
    
    try:
        config = load_config()
        data = parse_csv_data(config)
        
        if data:
            save_solar_data(data, config)
            
            print("\n✅ Data processing completed successfully!")
            print("=" * 60)
        else:
            print("\n⚠️  No data to process")
            print("=" * 60)
            exit(1)
        
    except Exception as e:
        print(f"\n❌ Data processing failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        exit(1)
