import streamlit as st
import folium
from folium.plugins import FastMarkerCluster
import pandas as pd
from streamlit_folium import folium_static
import geopandas as gpd
from branca.colormap import LinearColormap
import json
import re
import plotly.express as px

import folium
import geopandas as gpd
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim

#-------------------------------------------------------------------------------------------------------
st.set_page_config(page_title="AirBnB Odyssey", 
                   layout="wide")
def fmain():
    st.markdown("<h1 style='font-size: 40px; text-align: center; font-family: Futura;'>DISCOVER THE WORLD WITH AIRBNB 🌏</h1>", unsafe_allow_html=True)
    st.image("image.jpg", width=800)
    st.markdown("<h6 style='font-size: 15px; text-align: center;'>Airbnb is a popular hospitality service platform that enables people to list, discover, and book accommodations, offering a unique way for travelers to find affordable lodging options and for hosts to monetize their extra space or local expertise.</h6>", unsafe_allow_html=True)

with st.sidebar:
    st.title("LET'S GO...")
    options = ["🏨 Entryway","📍 AirBnB Facilities", "🛖 Property Type", "🕵️‍♀️ Country-wise Prices", "📈 Availability analysis","📊 Review-Rating Insights", "🌟 Verified Top Hosts","🏯 Wrap-up"]

#--------------------------------------------------------------------------------------------------------------------------------------------------
# Read data
df = pd.read_csv("airbnb.csv", low_memory=False)
countries = ['All'] + df['address.country'].unique().tolist()
with st.sidebar:
    selected_country = st.multiselect("Select one or more Countries", countries,default=["All"])
    if "All" not in selected_country:
        filtered_df = df[df['address.country'].isin(selected_country)]
    else:
        filtered_df = df
    count=filtered_df['_id'].count()
#---------------------------------------------------------------------------------------------------------------------------------------
region_avg_price = df.groupby('address.country')['price'].mean().round(2)
region_avg_price = region_avg_price.reset_index()
region_avg_price = region_avg_price.rename(columns={'address.country':'Country'})
#_______________________________________________________________________________________________________________________________________________
def map():
    mymap = folium.Map(location=[0, 0], zoom_start=2)

    room_type_styles = {
        'Private room': {'color': 'blue', 'size': 1},
        'Entire home/apt': {'color': 'green', 'size': 1},
        'Shared room': {'color': 'red', 'size': 1},
        'Hotel room': {'color': 'purple', 'size': 1}
    }

    for index, row in filtered_df.iterrows():
        lat = row['address.location.coordinates[1]']  
        lon = row['address.location.coordinates[0]']  
        price = row['price']
        name = row['name']
        room_type = row['room_type']
        rating =row['review_scores.review_scores_rating']
        country=row['address.country']
        
        name = re.sub(r'[^\w\s]', '', name)
        
        tooltip_text = f"Name: {name}<br>Room Type: {room_type}<br>Price: {price}$<br>Rating: {rating}<br>Country: {country}"  
        style = room_type_styles.get(room_type, {'color': 'gray', 'size': 5})  
        folium.CircleMarker(location=[lat, lon], tooltip=tooltip_text, radius=style['size'], color=style['color'], fill=True).add_to(mymap)
    
    folium_static(mymap)
#-------------------------------------------------------------------------------------------------------------------------------------
def room_type():    
    room_type_counts = filtered_df['room_type'].value_counts().reset_index()
    avg_price_by_room_type = filtered_df.groupby('room_type')['price'].mean().reset_index()
    room_type_counts.columns = ['Type', 'Listing']

    plot = px.bar(room_type_counts, x="Listing", y="Type", color="Type",
                height=500, width=800)
    st.plotly_chart(plot)
#--------------------------------------------------------------------------------------------------------------------------------------
avg_price_by_room_type = filtered_df.groupby('room_type')['price'].mean().reset_index()

fig2 = px.bar(avg_price_by_room_type, x='room_type', y='price', title='Average Price by Room Type', 
             labels={'price': 'Average Price ($)'}, color='room_type',height=500, width=800)

#-----------------------------------------------------------------------------------------------------------------
def average_price():
    fig = px.histogram(region_avg_price, y='price', x='Country', 
                title='Average Prices of Countries')
    fig.update_xaxes(title_text='Countries')
    fig.update_yaxes(title_text='Average Prices ($)')
    st.plotly_chart(fig)

#--------------------------------------------------------------------------------------------------------------------------------------
#top host
filtered_df = filtered_df.rename(columns={'host.host_name': 'Host Name'})
condition_1 = filtered_df['host.host_is_superhost'] == True
condition_2 = filtered_df['host.host_identity_verified'] == True

host_df = filtered_df[condition_1 & condition_2]

agg_dict = {'host.host_listings_count': 'max', 'address.country': 'first'}
listing_count_by_host = host_df.groupby(['Host Name', 'address.country']).agg(agg_dict)

listing_count_by_host = listing_count_by_host.rename(columns={'host.host_listings_count': 'Total Listing',
                                                              'address.country': 'Country'})
listing_count_by_host = listing_count_by_host.sort_values(by='Total Listing', ascending=False)
listing_count_by_host.reset_index(inplace=True)
#-----------------------------------------------------------------------------------------------------------------------------------
#availabily
def availability():
    option = st.selectbox('Select Availability Option for number of days:', ['30', '60', '90', '365'], index=0)

    filtered_df['availability.availability_30'] = filtered_df['availability.availability_30'].astype(int)
    filtered_df['availability.availability_60'] = filtered_df['availability.availability_60'].astype(int)
    filtered_df['availability.availability_90'] = filtered_df['availability.availability_90'].astype(int)
    filtered_df['availability.availability_365'] = filtered_df['availability.availability_365'].astype(int)

    if option == '30':
        availability_counts = filtered_df['availability.availability_30'].value_counts().sort_index()
    elif option == '60':
        availability_counts = filtered_df['availability.availability_60'].value_counts().sort_index()
    elif option == '90':
        availability_counts = filtered_df['availability.availability_90'].value_counts().sort_index()
    elif option == '365':
        availability_counts = filtered_df['availability.availability_365'].value_counts().sort_index()

    fig_line = px.line(x=availability_counts.index, y=availability_counts.values, 
                title=f'Availability Analysis for {option} Days',
                labels={'x': 'Days', 'y': 'Number of Listings'})

    st.plotly_chart(fig_line)
#-------------------------------------------------------------------------------------------------------------------------------------------
def review():
    fig = px.scatter(filtered_df, 
                    x='number_of_reviews', 
                    y='review_scores.review_scores_rating', 
                    title='Number of Reviews vs Review Scores',
                    labels={'number_of_reviews': 'Number of Reviews', 'review_scores.review_scores_rating': 'Review Scores'})

    fig.update_layout(showlegend=False)
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
    st.markdown(f"<div id='section{options.index("📍 AirBnB Facilities") + 1}'></div>", unsafe_allow_html=True)
    st.subheader("AirBnB Facilities in various countries 🏡")
    col1,col2=st.columns([5,1])
    with col1:
        map()
    with col2:
        with st.expander('Stats', expanded=True):
            st.write(f" <span style='font-size: 30px;'>{count}</span><br><span style='font-size: 14px;'> Total Entities</span>", unsafe_allow_html=True)
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 2
    st.markdown(f"<div id='section{options.index('🛖 Property Type') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Types of Rooms 🏙️ and Prices Analysis 💸")
    room_type()
    st.plotly_chart(fig2)

    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 3
    st.markdown(f"<div id='section{options.index('🕵️‍♀️ Country-wise Prices') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Country-wise Analysis of Property Prices 💰")
    average_price()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 4
    st.markdown(f"<div id='section{options.index('📈 Availability analysis') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Availability Analysis 🕒")
    availability()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 5
    st.markdown(f"<div id='section{options.index('📊 Review-Rating Insights') + 1}'></div>", unsafe_allow_html=True)
    st.subheader(" Rating Analysis 📑")
    review()
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    # Section 6
    st.markdown(f"<div id='section{options.index('🌟 Verified Top Hosts') + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Top Hosts in AirBnB 🏆")
    col1, col2=st.columns([5,1])
    with col1:
        st.write(listing_count_by_host[['Host Name','Country','Total Listing']])
    with col2:
        st.image("star.png",width=200)
    st.markdown("<hr style='height:2px;border-width:0;color:gray;background-color:gray'>", unsafe_allow_html=True)

    #Section T
    st.markdown(f"<div id='section{options.index("🏯 Wrap-up") + 1}'></div>", unsafe_allow_html=True)
    st.subheader("Humble Observations! 📜")
    conclusion_text = """
    1. **Booking Preferences by Room Type**: Entire homes are the most preferred booking option, followed by private rooms, and then shared rooms.

    2. **Average Room Rates by Room Type** : Shared rooms have the highest average room rates, followed by entire homes, and then private rooms.

    3. **Price Variation by Country** : Hong Kong has the highest average room rates, making it the most expensive destination.
        Portugal offers the most affordable accommodations with the lowest average room rates.

    4. **Listing Count by Country**: The United States has the highest number of listings with 1,222 properties.
        China has the least number of listings with only 19 properties.

    5. **Availability Options** : Property availability is offered in various durations:
            30 days, 60 days, 90 days and 365 days
        Demand exists for all these availability options.

    6. **Ratings and Reviews Analysis** : There is a positive correlation between the number of reviews and review scores.
        Properties with more reviews tend to have higher ratings, indicating customer satisfaction and trustworthiness.

    7. **Top Host Characteristics** : Top hosts on Airbnb are mostly verified, which adds credibility to their listings.
    They are also known to respond quickly to inquiries, enhancing the guest experience and satisfaction."""
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