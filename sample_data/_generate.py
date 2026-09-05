import csv
import random
from datetime import datetime, timedelta
import os

random.seed(42)

categories = ['Electronics', 'Clothing', 'Food & Beverage', 'Home & Garden', 'Sports', 'Books', 'Health & Beauty']
regions = ['North', 'South', 'East', 'West', 'Central']
payment_methods = ['Credit Card', 'Debit Card', 'Cash', 'Digital Wallet', 'Bank Transfer']

rows = []
start_date = datetime(2023, 1, 1)

for i in range(1, 301):
    tid = f'T{i:04d}'
    days_offset = random.randint(0, 545)
    tdate = (start_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')
    
    # customer_id with ~3% missing
    cid = f'C{random.randint(1, 50):03d}' if random.random() > 0.03 else ''
    
    cat = random.choice(categories)
    region = random.choice(regions)
    payment = random.choice(payment_methods)
    
    # Quantity: mostly 1-20, few outliers
    if random.random() < 0.02:
        qty = random.randint(100, 500)
    else:
        qty = random.randint(1, 20)
    
    # Unit price: mostly 5-500, few outliers
    if random.random() < 0.02:
        price = round(random.uniform(2000, 5000), 2)
    else:
        price = round(random.uniform(5, 500), 2)
    
    # Discount: 0-30%, with ~5% missing
    if random.random() < 0.05:
        discount = ''
    else:
        discount = round(random.uniform(0, 0.30), 2)
    
    # Revenue
    if discount != '':
        rev = round(qty * price * (1 - float(discount)), 2)
    else:
        rev = round(qty * price, 2)
    
    # Revenue with ~4% missing
    if random.random() < 0.04:
        rev = ''
    
    # Cost
    if rev != '':
        cost = round(float(rev) * random.uniform(0.4, 0.85), 2)
        profit = round(float(rev) - cost, 2)
        # Some negative profits
        if random.random() < 0.05:
            profit = round(-abs(profit) * random.uniform(0.1, 0.5), 2)
    else:
        cost = ''
        profit = ''
    
    rows.append([tid, tdate, cid, cat, region, payment, qty, price, discount, rev, cost, profit])

# Add 3 duplicate rows
for _ in range(3):
    rows.append(rows[random.randint(0, len(rows)-1)])

random.shuffle(rows[-10:])

os.makedirs('sample_data', exist_ok=True)
with open('sample_data/sample_finance.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['transaction_id', 'transaction_date', 'customer_id', 'category', 'region', 'payment_method', 'quantity', 'unit_price', 'discount', 'revenue', 'cost', 'profit'])
    writer.writerows(rows)
