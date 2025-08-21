import pandas as pd
import mysql.connector

# Update this path to your CSV location
csv_path = ("C:/Users/Navy/Downloads/claims_data.csv",
            "C:/Users/Navy/Downloads/food_listings_data.csv",
            "C:/Users/Navy/Downloads/receivers_data.csv",
            "C:/Users/Navy/Downloads/providers_data.csv")

df = pd.read_csv(csv_path)

# 'CustomerID' does not exist, but analogous columns could be dropped. For demonstration, let's apply to 'Receiver_ID'.
df = df.dropna(subset=['Receiver_ID'])

# There is no 'InvoiceDate'. Instead, use 'Timestamp' and convert to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# There is no 'UnitPrice', but if a numeric column is needed, we'll demonstrate with 'Claim_ID'
df['Claim_ID'] = pd.to_numeric(df['Claim_ID'], errors='coerce')

# Fill remaining NA values (if any) with empty string
df = df.fillna('')

# Connect to MySQL
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Naman@0305',  # Replace with your MySQL password
    database='food_availability'
)
cursor = conn.cursor()

conn.execute('''
-- Table for claims_data
CREATE TABLE claims_data (
    Claim_ID INTEGER PRIMARY KEY,
    Food_ID INTEGER,
    Receiver_ID INTEGER,
    Status TEXT,
    Timestamp TEXT
    );
''')

conn.execute('''
   -- Table for food_listings_data
CREATE TABLE food_listings_data (
    Food_ID INTEGER PRIMARY KEY,
    Food_Name TEXT,
    Quantity INTEGER,
    Expiry_Date TEXT,
    Provider_ID INTEGER,
    Provider_Type TEXT,
    Location TEXT,
    Food_Type TEXT,
    Meal_Type TEXT
    );
''')

conn.execute('''
     -- Table for receivers_data
CREATE TABLE receivers_data (
    Receiver_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    City TEXT,
    Contact TEXT
    );
''')

conn.execute('''
     -- Table for providers_data
CREATE TABLE providers_data (
    Provider_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    City TEXT,
    Contact TEXT
    );
''')

conn.commit()

