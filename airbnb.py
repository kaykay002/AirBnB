import streamlit as st
import folium
from folium.plugins import FastMarkerCluster
import pandas as pd
from streamlit_folium import folium_static
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pymongo import MongoClient


#-------------------------------------------------------------------------------------------------------
st.set_page_config(page_title="AirBnB Odyssey", 
                   layout="wide")
def fmain():
    st.markdown("<h1 style='font-size: 40px; text-align: center; font-family: Futura;'>Singapore's AirBnB Odyssey</h1>", unsafe_allow_html=True)
    st.image("sealion.jpg", width=800)
    st.markdown("<h5 style='font-size: 15px; text-align: center;'>Discover the vibrant city of Singapore. Find unique accommodations, from cozy apartments in the heart of the city to luxurious villas overlooking breathtaking skyline views. Immerse yourself in the diverse culture, delicious cuisine, and exciting attractions that Singapore has to offer, and make unforgettable memories during your stay with Airbnb.</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.title("LET'S GO...")
    options = ["🏨 Entryway","📍 Singapore's AirBnB Facilities", "🛖 Property Type", "🕵️‍♀️ Region-wise Prices", "📈 Booking Trends","📊 Booking Insights", "🌟 Verified Top Hosts","🏯 Wrap-up"]

#-----------------------------------------------------------------------------------------------------

#MongoDB Connection
connection = MongoClient("mongodb+srv://kamayanimgnf2021:12345@cluster0.rgwducf.mongodb.net/")
db=connection["Airbnb_Database"]
collection_names = ['listings', 'neighbourhoods', 'reviews']
dfs = {}

for collection_name in collection_names:
    collection = db[collection_name]
    
    cursor = collection.find()
    
    dfs[collection_name] = pd.DataFrame(list(cursor))

df = dfs['listings']
df1 = dfs['neighbourhoods']
df2 = dfs['reviews']
#-----------------------------------------------------------------------------------------------------

#creating a df for host details
host_cols=['host_id',
        'host_name', 'host_since', 
       'host_is_superhost',
       'host_total_listings_count',
        'host_identity_verified']
df_host = df[host_cols].copy()
df_host = df_host.drop_duplicates()
df_host = df_host.ffill()
df_host = df_host.bfill()

#creating a df for property details
property_cols=['id', 'listing_url', 'name',
       'latitude', 'longitude', 'property_type', 'room_type', 'accommodates',
       'bathrooms_text', 'beds', 'price',
       'minimum_nights', 'maximum_nights', 'has_availability',
       'availability_30', 'availability_60', 'availability_90',
       'availability_365',  'number_of_reviews',
       'review_scores_rating', 'instant_bookable','neighbourhood_group_cleansed'
       ]
df_property = df[property_cols].copy()
df_property = df_property.drop_duplicates()

#filling price cols null values, changing dtype, and fill in mean value
df_property['price'] = df_property['price'].str.replace('$', '')
df_property['price'] = pd.to_numeric(df_property['price'], errors='coerce')
df_property['price'] = df_property['price'].astype(float)
mean_price = round(df_property['price'].mean(), 2)
average_price = mean_price
average_nights_booked = df['number_of_reviews'].sum() / len(df)
average_nights_booked=average_nights_booked.round(2)

df_property['price'] = df_property['price'].fillna(mean_price)
region_avg_price = df_property.groupby('neighbourhood_group_cleansed')['price'].mean().round(2)
region_avg_price = region_avg_price.reset_index()
region_avg_price = region_avg_price.rename(columns={'neighbourhood_group_cleansed':'region'})
df_property['price'] = df_property['price'].apply(lambda x: f"${x}/night")

    
mean_rating = df_property['review_scores_rating'].mean()
df_property['review_scores_rating'] = round(df_property['review_scores_rating'].fillna(mean_rating),2)
df_property = df_property.fillna(value={'bathrooms_text': '1 bath'})
df_property = df_property.fillna(value={'beds': '1.5'})
df_property['has_availability'] = df_property['has_availability'].ffill()
df_property['has_availability'] = df_property['has_availability'].bfill()

#host data
top_hosts = df_host.sort_values(by='host_total_listings_count', ascending=False)
col=['host_since','host_is_superhost','host_identity_verified']
top_hosts = top_hosts.drop(columns=col)
desired_columns = df[['host_id', 'neighbourhood_group_cleansed']]
merged_df = pd.merge(top_hosts, desired_columns, on='host_id', how='inner')
df_region_host = merged_df.drop_duplicates()
df_region_host = df_region_host.rename(columns={
    'host_total_listings_count': 'Total listing',
    'neighbourhood_group_cleansed': 'Region',
    'host_name': 'Host'})

#activity data
col=['id','minimum_nights','price','number_of_reviews']
df_activity = df[col].copy()
df_activity = df_activity.drop_duplicates()
#_______________________________________________________________________________________________

unique_neighborhoods = ['Singapore'] + df_property['neighbourhood_group_cleansed'].unique().tolist()
with st.sidebar:
    selected_neighbourhood = st.multiselect("Select the Region", unique_neighborhoods,default=["Singapore"])
    if "Singapore" not in selected_neighbourhood:
        filtered_df = df_property[df_property['neighbourhood_group_cleansed'].isin(selected_neighbourhood)]
    else:
        filtered_df = df_property
#---------------------------------------------------------------------------------------------------

#room type bar graph
def room_type():    
    room_type_counts = filtered_df['room_type'].value_counts().reset_index()
    room_type_counts.columns = ['Type', 'Listing']

    plot = px.bar(room_type_counts, x="Listing", y="Type", color="Type",
                color_discrete_map={"Private room": "blue", 
                                    "Entire home/apt": "green", 
                                    "Shared room": "red", 
                                    "Hotel room": "purple"},
                height=500, width=800)
    st.plotly_chart(plot)
#________________________________________________________________________________________________

def map(df_property):
    lat = df_property['latitude'].tolist()
    lon = df_property['longitude'].tolist()
    property_names = df_property['name'].tolist()
    room_types = df_property['room_type'].tolist()
    property_prices = df_property['price'].tolist()
    property_ratings = df_property['review_scores_rating'].tolist()
    property_neighbourhood = df_property['neighbourhood_group_cleansed'].tolist()

    locations = list(zip(lat, lon, property_names, room_types, property_prices, property_ratings, property_neighbourhood))

    room_type_styles = {
        'Private room': {'color': 'blue', 'size': 1},
        'Entire home/apt': {'color': 'green', 'size': 1},
        'Shared room': {'color': 'red', 'size': 1},
        'Hotel room': {'color': 'purple', 'size': 1}
    }

    map1 = folium.Map(location=[1.3521, 103.8198], zoom_start=11.5)

    for location in locations:
        lat, lon, name, room_type, price, rating, neighbourhood = location
        tooltip_text = f"Name: {name}<br>Room Type: {room_type}<br>Price: {price}<br>Rating: {rating}"  # Custom tooltip text without host
        style = room_type_styles.get(room_type, {'color': 'gray', 'size': 5})  # Get style based on room type, default to gray color and size 5 if not found
        folium.CircleMarker(location=[lat, lon], tooltip=tooltip_text, radius=style['size'], color=style['color'], fill=True).add_to(map1)
  
    FastMarkerCluster(data=locations).add_to(map1)
    return map1
#--------------------------------------------------------------------------------------------------------

def region_avg_price_pie():
    fig = px.pie(region_avg_price, values='price', names='region', 
                title='Average Prices by Region in $', color='region',
                color_discrete_map={'Central Region': 'blue', 'East Region': 'green',
                                    'North Region': 'red', 'North-East Region': 'purple', 'West Region': 'orange'})
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig)
#---------------------------------------------------------------------------------------------------------

def year_trend():
    df2['date'] = pd.to_datetime(df2['date'])
    df2['year'] = df2['date'].dt.year
    yearly_counts = df2.groupby('year')['listing_id'].count().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=yearly_counts['year'], y=yearly_counts['listing_id'], mode='lines', name='Number of Listings'))
    fig.add_trace(go.Scatter(x=yearly_counts['year'], y=yearly_counts['listing_id'], mode='markers', marker=dict(color='red', size=5)))
    fig.update_layout(title='Number of Listings per Year',
                    xaxis_title='Year', yaxis_title='Listings',
                    showlegend=True)
    st.plotly_chart(fig)
#-------------------------------------------------------------------------------------------------------

def top_host(selected_neighbourhood):
    if "Singapore" not in selected_neighbourhood:
        filtered_df = df_region_host[df_region_host['Region'].isin(selected_neighbourhood)]
        filtered_df = filtered_df.drop(columns=['Region', 'host_id']).reset_index(drop=True)
    else:
        filtered_df = df_region_host
        filtered_df = filtered_df.drop(columns=['host_id']).reset_index(drop=True)
    #st.write(filtered_df.head(20))
    st.dataframe(filtered_df, height=450)
#---------------------------------------------------------------------------------------------------

def activity():
    fig = px.histogram(df_activity, x='minimum_nights',
                    labels={'minimum_nights': 'Minimum Stay', 'count': 'Listing'},
                    title='Distribution of Stay Days',
                    color_discrete_sequence=['#1f77b4'])
    fig.update_xaxes(range=[0, 400], dtick=30)
    st.plotly_chart(fig)



#-------------------------------------------STREAMLIT-----------------------------------------------------------------------------

def main():
    
    for option in options:
        st.sidebar.markdown(f"<a href='#section{options.index(option) + 1}' class='sidebar-button'>{option}</a>", unsafe_allow_html=True)

    #Section 0
    st.markdown(f"<div id='section{options.index("🏨 Entryway") + 1}'></div>", unsafe_allow_html=True)
    fmain()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)
    
    # Section 1
    st.markdown(f"<div id='section{options.index("📍 Singapore's AirBnB Facilities") + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Singapore's AirBnB Facilities")
    map(df_property)
    map_obj = map(filtered_df)
    folium_static(map_obj)
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 2
    st.markdown(f"<div id='section{options.index('🛖 Property Type') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Type of Room")
    room_type()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 3
    st.markdown(f"<div id='section{options.index('🕵️‍♀️ Region-wise Prices') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Regionwise Analysis of Property Prices")
    region_avg_price_pie()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 4
    st.markdown(f"<div id='section{options.index('📈 Booking Trends') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Trend analysis bookings in past years")
    year_trend()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 5
    st.markdown(f"<div id='section{options.index('📊 Booking Insights') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Booking Activity Analysis")
    col1,col2=st.columns([5,2])
    with col1:
        activity()
    with col2:
        with st.expander('Stats', expanded=True):
            st.write(f" <span style='font-size: 30px;'>{average_nights_booked}</span><br><span style='font-size: 14px;'> Average nights booked</span>", unsafe_allow_html=True)
            st.write(f"<span style='font-size: 30px;'>${average_price}</span><br><span style='font-size: 14px;'> Average price</span>", unsafe_allow_html=True)
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 6
    st.markdown(f"<div id='section{options.index('🌟 Verified Top Hosts') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Top Hosts in Singapore")
    
    col1,col2,col3=st.columns([1,5,1])
    with col2:
        top_host(selected_neighbourhood)
    with col3:
        st.image("star.png", width=200)
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)


    #Section T
    st.markdown(f"<div id='section{options.index("🏯 Wrap-up") + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Humble Observations! 📜")
    conclusion_text = """
    1. **Central Singapore - Expensive yet Attractive**: The central region emerges as the most expensive area for Airbnb listings, likely due to its proximity to popular attractions. Despite the higher cost, demand remains strong, indicating the allure of the central location. This part boasts the highest concentration of amenities and facilities, reflecting its status as a hub for tourist attractions and amenities.

    2. **Preference for Private Accommodation**: Analysis reveals preference for private accommodations such as rooms, apartments, or entire homes over shared accommodations for better privacy and comfort, so there is driving demand for such listings.

    3. **Impact of COVID-19**: The years 2020 and 2021 witnessed a significant decline in Airbnb bookings. However, bookings rebounded strongly in 2022, reaching an all-time high.

    4. **Booking Duration Trends**: Most Airbnb listings offer flexible booking durations, ranging from short-term stays of 2-50 days to longer-term options spanning 90-365 days. While shorter stays are more common, a notable number of listings cater to extended stays, reflecting diverse guest preferences.

    5. **Top Hosts' Profile**: The top Airbnb hosts in Singapore are characterized by their verified status. These hosts also demonstrate efficient response times. Additionally, their presence across multiple regions underscores their widespread appeal and success in catering to diverse guest needs."""
    st.markdown(conclusion_text)
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)
    

# custom CSS style 
st.markdown("""
<style>
.sidebar-button {
    color: white !important;
    font-size: 16px;
    text-decoration: none;
    transition: color 0.3s ease-in-out;
}
.sidebar-button:hover {
    color: lightgray !important;
}

</style>
""", unsafe_allow_html=True)
if __name__ == "__main__":
    main()