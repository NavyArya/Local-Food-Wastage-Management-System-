import streamlit as st
import pandas as pd
import sqlite3

# Load data
@st.cache_data
def load_data():
    claims = pd.read_csv("claims_data.csv")
    food = pd.read_csv("food_listings_data.csv")
    receivers = pd.read_csv("receivers_data.csv")
    providers = pd.read_csv("providers_data.csv")
    return claims, food, receivers, providers

claims_df, food_df, receivers_df, providers_df = load_data()

# Filter options
cities = sorted(set(food_df['Location'].unique()) | set(providers_df['City'].unique()))
providers_list = sorted(providers_df['Name'].unique())
food_types = sorted(food_df['Food_Type'].unique())
meal_types = sorted(food_df['Meal_Type'].unique())

st.title("Food Claims Dashboard")

st.sidebar.header("Filter Options")
selected_city = st.sidebar.multiselect("City", cities)
selected_provider = st.sidebar.multiselect("Provider", providers_list)
selected_food_type = st.sidebar.multiselect("Food Type", food_types)
selected_meal_type = st.sidebar.multiselect("Meal Type", meal_types)

food_filtered = food_df.copy()
if selected_city:
    food_filtered = food_filtered[food_filtered['Location'].isin(selected_city)]
if selected_provider:
    provider_ids = providers_df[providers_df['Name'].isin(selected_provider)]['Provider_ID']
    food_filtered = food_filtered[food_filtered['Provider_ID'].isin(provider_ids)]
if selected_food_type:
    food_filtered = food_filtered[food_filtered['Food_Type'].isin(selected_food_type)]
if selected_meal_type:
    food_filtered = food_filtered[food_filtered['Meal_Type'].isin(selected_meal_type)]

# Setup in-memory SQLite database
conn = sqlite3.connect(':memory:')
claims_df.to_sql('claims', conn, index=False)
food_df.to_sql('food', conn, index=False)
receivers_df.to_sql('receivers', conn, index=False)
providers_df.to_sql('providers', conn, index=False)

# 15 example SQL Queries
queries = {
    "1. Pending Claims": """
        SELECT * FROM claims WHERE Status='Pending';
    """,
    "2. Completed Claims": """
        SELECT * FROM claims WHERE Status='Completed';
    """,
    "3. Cancelled Claims per City": """
        SELECT food.Location as City, COUNT(*) as Cancelled_Claims
        FROM claims
        JOIN food ON claims.Food_ID = food.Food_ID
        WHERE claims.Status='Cancelled'
        GROUP BY food.Location;
    """,
    "4. Meal Type Distribution": """
        SELECT Meal_Type, COUNT(*) as Count FROM food GROUP BY Meal_Type;
    """,
    "5. Food Type per City": """
        SELECT Location as City, Food_Type, COUNT(*) as Count FROM food GROUP BY Location, Food_Type;
    """,
    "6. Top Providers by Claims": """
        SELECT p.Name, COUNT(*) as Claims
        FROM claims c
        JOIN food f ON c.Food_ID=f.Food_ID
        JOIN providers p ON f.Provider_ID=p.Provider_ID
        GROUP BY p.Name
        ORDER BY Claims DESC
        LIMIT 10;
    """,
    "7. Claims by Receiver Type": """
        SELECT r.Type, COUNT(*) as Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID=r.Receiver_ID
        GROUP BY r.Type;
    """,
    "8. Expiring Food in Next Week": f"""
        SELECT * FROM food WHERE julianday('2025-08-24') - julianday(Expiry_Date) BETWEEN 0 AND 7;
    """,
    "9. Provider Contact Information": """
        SELECT Name, Type, City, Contact FROM providers;
    """,
    "10. Unique Food Items Offered": """
        SELECT Food_Name, COUNT(*) as Count FROM food GROUP BY Food_Name;
    """,
    "11. Claims for Vegan Foods": """
        SELECT * FROM claims
        JOIN food ON claims.Food_ID = food.Food_ID
        WHERE food.Food_Type='Vegan';
    """,
    "12. Receivers With Most Claims": """
        SELECT r.Name, COUNT(*) as Claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID=r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Claims DESC
        LIMIT 10;
    """,
    "13. Claims by Meal Type": """
        SELECT food.Meal_Type, COUNT(*) as Claims
        FROM claims
        JOIN food ON claims.Food_ID = food.Food_ID
        GROUP BY food.Meal_Type;
    """,
    "14. Food Listings by Provider": """
        SELECT p.Name, COUNT(*) as Listings
        FROM food f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
        ORDER BY Listings DESC
        LIMIT 10;
    """,
    "15. Open Claims With Contact Details": """
        SELECT c.Claim_ID, f.Food_Name, p.Name as Provider, p.Contact
        FROM claims c
        JOIN food f ON c.Food_ID=f.Food_ID
        JOIN providers p ON f.Provider_ID=p.Provider_ID
        WHERE c.Status='Pending';
    """
}

st.header("Query Results")

selected_query = st.selectbox("Select a query to view output", list(queries.keys()))

# Run the selected query on filtered data if filters applied, else on full data
def run_query(query):
    # Many queries are not affected by food_filtered, but for queries involving food table, use the filtered data.
    if any(tab in query for tab in ["food", "providers"]):
        # Overwrite the food table in the in-memory db with the filtered version
        food_filtered.to_sql('food', conn, if_exists='replace', index=False)
    else:
        # Reset food table to full data for other queries
        food_df.to_sql('food', conn, if_exists='replace', index=False)
        
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

result_df = run_query(queries[selected_query])

st.dataframe(result_df)

if selected_query == "9. Provider Contact Information" or selected_query == "15. Open Claims With Contact Details":
    st.subheader("Provider Contact Details")
    # If already shown in main table, skip.
    if not any(x in result_df.columns for x in ["Contact", "Provider Contact"]):
        provider_details = providers_df[['Name', 'Type', 'Address', 'City', 'Contact']]
        st.dataframe(provider_details)
