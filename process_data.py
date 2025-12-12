#!/usr/bin/env python3
"""
Muir College Solar Data Processor - FIXED VERSION
Processes CSV data and generates JSON files for the dashboard
"""

import os
import json
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

# File paths
CONFIG_FILE = "config.json"
CSV_FILE = "data/solar_export_latest.csv"
PERSISTENT_TOTALS_FILE = "data/persistent_totals.json"
SOLAR_DATA_FILE = "solar_data.json"

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
    """Parse CSV and calculate all metrics - FULL DAY VERSION"""
    print("📊 Processing CSV data...")
    
    params = config['environmental_factors']
    
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("  ✗ No rows in CSV")
        return None

    print(f"  ↳ Found {len(rows)} rows in CSV")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = now.strftime('%Y-%m-%d')

    persistent = load_persistent_totals(config)

    is_new_day = persistent.get('last_update_date', '') != today_str
    is_new_month = (persistent.get('current_month') != now.month or
                    persistent.get('current_year') != now.year)

    # Parse ALL of today's data (not incremental)
    parsed_rows = []
    valid_count = 0
    empty_count = 0
    
    for row in rows:
        try:
            # Extract timestamp
            timestamp_str = row.get('Time', '')
            if not timestamp_str:
                continue

            # Parse timestamp - try multiple formats
            timestamp = None
            formats = [
                '%m/%d/%Y %H:%M',  # MM/DD/YYYY HH:MM
                '%d/%m/%Y %H:%M',  # DD/MM/YYYY HH:MM
                '%Y-%m-%d %H:%M',  # YYYY-MM-DD HH:MM
            ]
            
            for fmt in formats:
                try:
                    timestamp = datetime.strptime(timestamp_str, fmt)
                    break
                except:
                    continue

            if not timestamp:
                continue

            # Extract power value from "Production AC" column
            power_str = row.get('Production AC', '').strip()
            
            # Skip empty power values
            if not power_str or power_str == '':
                empty_count += 1
                continue
            
            try:
                power_w = float(power_str)
            except:
                continue

            # Only keep today's data with power > 0
            if power_w > 0:
                parsed_rows.append({
                    'timestamp': timestamp,
                    'power_w': power_w
                })
                valid_count += 1

        except Exception as e:
            continue

    print(f"  ✓ Parsed {valid_count} valid readings (skipped {empty_count} empty)")

    # Calculate total energy from ALL readings using 5-minute intervals
    data_interval_hours = config['system']['data_interval_minutes'] / 60.0
    daily_total_kwh = 0.0

    for row in parsed_rows:
        # Energy = Power (kW) × Time (hours)
        energy_kwh = (row['power_w'] / 1000.0) * data_interval_hours
        daily_total_kwh += energy_kwh

    print(f"  ✓ Calculated daily total: {daily_total_kwh:.2f} kWh from {len(parsed_rows)} readings")

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

    if is_new_month:
        persistent['current_month'] = now.month
        persistent['current_year'] = now.year
        persistent['month_start_total_kwh'] = 0.0
        print(f"  ↳ New month! Reset monthly total")

    # Update persistent totals - REPLACE daily total (don't add)
    persistent['last_daily_total'] = daily_total_kwh
    persistent['last_update_date'] = today_str

    save_persistent_totals(persistent)

    # Calculate cumulative totals
    lifetime_kwh = persistent['lifetime_total_kwh'] + persistent['last_daily_total']
    monthly_kwh = persistent['month_start_total_kwh'] + persistent['last_daily_total']

    print(f"  ✓ Today's total: {persistent['last_daily_total']:.2f} kWh")
    print(f"  ✓ Monthly total: {monthly_kwh:.2f} kWh")
    print(f"  ✓ Lifetime total: {lifetime_kwh:.2f} kWh")

    # Get yesterday's data
    yesterday_data = persistent.get('daily_history', [])[-1] if persistent.get('daily_history', []) else None

    return {
        "timestamp": now.isoformat(),
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
    print("⚙️  MUIR COLLEGE DATA PROCESSOR - FIXED VERSION")
    print("=" * 60)
    
    try:
        config = load_config()
        data = parse_csv_data(config)
        
        if data:
            save_solar_data(data, config)
            
            print("\n✅ Data processing completed successfully!")
            print(f"   Daily: {data['daily_total_kwh']} kWh")
            print(f"   Monthly: {data['monthly_total_kwh']} kWh")
            print(f"   Lifetime: {data['lifetime_total_kwh']} kWh")
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
