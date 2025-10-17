import csv
from datetime import datetime
from pathlib import Path

# Find the most recent CSV
csv_folder = Path("downloads")
csv_files = sorted(csv_folder.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)

if not csv_files:
    print("No CSV files found in downloads folder!")
    exit()

csv_file = csv_files[0]
print(f"Analyzing: {csv_file}\n")
print("=" * 80)

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows)}")
print(f"Columns: {list(rows[0].keys())}\n")

# Show first 5 rows
print("FIRST 5 ROWS:")
print("-" * 80)
for i, row in enumerate(rows[:5]):
    print(f"Row {i+1}: {dict(row)}\n")

# Show last 5 rows
print("\nLAST 5 ROWS:")
print("-" * 80)
for i, row in enumerate(rows[-5:]):
    print(f"Row {len(rows)-5+i+1}: {dict(row)}\n")

# Analyze TODAY's data
now = datetime.now()
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

today_rows = []
for row in rows:
    timestamp_str = list(row.values())[0]
    
    for fmt in ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M']:
        try:
            timestamp = datetime.strptime(timestamp_str, fmt)
            if timestamp >= today_start:
                today_rows.append((timestamp, row))
            break
        except:
            continue

print(f"\nTODAY'S DATA ({today_start.strftime('%Y-%m-%d')}):")
print("-" * 80)
print(f"Found {len(today_rows)} rows from today\n")

if today_rows:
    print("First 10 rows from TODAY:")
    for i, (ts, row) in enumerate(today_rows[:10]):
        col_b_value = list(row.values())[1] if len(row.values()) > 1 else "N/A"
        print(f"{ts.strftime('%H:%M')} - {col_b_value}")
    
    print("\n...")
    
    print("\nLast 10 rows from TODAY:")
    for i, (ts, row) in enumerate(today_rows[-10:]):
        col_b_value = list(row.values())[1] if len(row.values()) > 1 else "N/A"
        print(f"{ts.strftime('%H:%M')} - {col_b_value}")

# Check if column B looks like cumulative or interval data
print("\n" + "=" * 80)
print("ANALYSIS:")
print("-" * 80)

if len(today_rows) >= 2:
    values = []
    for ts, row in today_rows:
        try:
            val_str = str(list(row.values())[1]).replace('kWh', '').replace('kwh', '').replace('W', '').replace('w', '').replace(',', '').strip()
            if val_str:
                values.append(float(val_str))
        except:
            pass
    
    if len(values) >= 2:
        print(f"First value of day: {values[0]}")
        print(f"Last value of day: {values[-1]}")
        print(f"Difference: {values[-1] - values[0]}")
        
        if values[0] < values[-1] and values[-1] > values[0] * 2:
            print("\n⚠️  Column B appears to be CUMULATIVE (running total)")
            print("    We should take the LAST value minus FIRST value as daily total")
        else:
            print("\n✓  Column B appears to be INTERVAL data (power readings)")
            print("    We should SUM all values and convert properly")

print("\n" + "=" * 80)
