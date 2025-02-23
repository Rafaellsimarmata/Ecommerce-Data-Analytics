import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import streamlit as st
import requests
from io import StringIO
from streamlit_folium import folium_static
from babel.numbers import format_currency

sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    product_category_counts = df['product_category_name'].value_counts()
    product_category_counts = pd.DataFrame({'product_category_name': product_category_counts.index, 'counts': product_category_counts.values})
    return product_category_counts

def create_top_10_order_city_df(df):
    customer_city_counts = df['customer_city'].value_counts()
    return customer_city_counts.head(10)

def create_map(df):
    customer_loc = df[['customer_unique_id', 'geolocation_lat', 'geolocation_lng']]
    gdf = gpd.GeoDataFrame(customer_loc, geometry=gpd.points_from_xy(customer_loc.geolocation_lng, customer_loc.geolocation_lat))
    return gdf

#import dataset
url = "https://raw.githubusercontent.com/Rafaellsimarmata/Ecommerce-Data-Analytics/refs/heads/main/dashboard/all_df.csv"
response = requests.get(url)

if response.status_code != 200:
    st.error("Failed to load data from GitHub.")

all_df = pd.read_csv(StringIO(response.text))

datetime_columns = ['order_purchase_timestamp', 'order_approved_at',
       'order_delivered_carrier_date', 'order_delivered_customer_date',
       'order_estimated_delivery_date']
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp"].min()
max_date = min_date + pd.Timedelta(days=30)

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://tse3.mm.bing.net/th?id=OIP.EPNNa5m6VV5DCBj8HUumWwHaEO&pid=Api&P=0&h=180")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & (all_df["order_purchase_timestamp"] <= str(end_date))]

st.header('E-commerce Public Dashboard :sparkles:')

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
customer_loc_gdf = create_map(main_df)
top_10_order_city = create_top_10_order_city_df(main_df)

st.subheader('Daily Orders')
 
col1, col2 = st.columns(2)
 
with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)
 
with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

st.subheader("Best & Worst Performing Product")
 
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

colors = ["#67eb34", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="counts", y="product_category_name", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel("Kategori Produk")
ax[0].set_xlabel("Volume Order")
ax[0].set_title("Kategori Produk Tertinggi", loc="center", fontsize=18)
ax[0].tick_params(axis ='y', labelsize=15)

sns.barplot(x="counts", y="product_category_name", data=sum_order_items_df.tail(5), palette=colors, ax=ax[1])
ax[1].set_ylabel("Kategori Produk")
ax[1].set_xlabel("Volume Order")
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Kategori Produk Terendah", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)
st.pyplot(fig)


st.subheader("Top 10 City based volume order")
 
fig, ax = plt.subplots(figsize=(16, 8))

ax.bar(top_10_order_city.index, top_10_order_city.values)
ax.set_xlabel("Customer City")
ax.set_ylabel("Order Count")
ax.set_title("Top 10 Kota dengan order volume tertinggi")
# ax.xticks(rotation=45, ha="right")
# ax.tight_layout()
st.pyplot(fig)



st.subheader("Customer Order Location")
customer_loc_gdf = customer_loc_gdf.set_crs(epsg=4326, inplace=True)
customer_loc_gdf.crs
m = customer_loc_gdf.explore()
folium_static(m)


