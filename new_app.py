import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd               #Package untuk pemrosesan data

import numpy as np                #Package untuk perhitungan

import matplotlib.pyplot as plt   #Package untuk visualisasi data dasar

import matplotlib.dates as mdates #Package untuk menyediakan format visualisasi data deret waktu

from matplotlib import cm         #Package untuk penentuan warna peta

import plotly.express as px       #Package untuk visualisasi data lain

import plotly.graph_objects as go #Package untuk visualisasi data lain

import seaborn as sns             #Package untuk visualisasi data lanjut

import os                         #Package untuk mengatur akses file

from datetime import datetime     #Package untuk mengatur format tanggal

import gc                         #Package untuk menghapus dataframe yang sudah tidak dipakai

import warnings                   #Package untuk mematikan peringatan eror user
warnings.filterwarnings('ignore')

path = 'D:/Local Disk C/Python project/src/Boom ITS/Data/' #Replace with your own path
bike = pd.read_csv(path+'daily_rent_detail.csv')
# station = pd.read_csv(path+'station_list.csv') #Memiliki kolom yang ada pada tabel lain. Redundant
usage = pd.read_csv(path+'usage_frequency.csv')
# weather = pd.read_csv(path+'weather.csv') #Cuaca tidak dipilih dalam analisis data

usage['date'] = usage['date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

bike['started_at'] = pd.to_datetime(bike['started_at'], format='mixed')
bike['ended_at'] = pd.to_datetime(bike['ended_at'], format='mixed')
bike['date'] = bike['started_at'].dt.date
bike.fillna('Others', inplace=True)
for i in bike.columns:
    bike = bike[bike[i]!='Others']
bike['gap'] = bike['ended_at'] - bike['started_at']

# Extract minute and hours from the time difference
bike['minute'] = bike['gap'].dt.seconds //60
bike['hours'] = bike['gap'].dt.seconds // 3600
bike = bike.drop('ride_id', axis=1)
bike = bike.drop('end_lat', axis=1)
bike = bike.drop('end_lng', axis=1)

# Membuat method pembuatan tabel agregasi berdasarkan kebutuhan

def group_by_method(stat_metric, keycol):

 return bike.groupby(keycol).agg(

    minute = ('minute', stat_metric),

    hours = ('hours', stat_metric),

    lat = ('start_lat', stat_metric),

    lng = ('start_lng', stat_metric)

)
# Pembuatan tabel agregasi berdasarkan stasiun
agg = group_by_method('mean',['start_station_id','start_station_name'])
agg.reset_index(inplace=True)

rent_day =  bike.groupby('date').agg(

    minute = ('minute', 'mean'),

    hours = ('hours', 'mean'),

    lat = ('start_lat', 'mean'),

    lng = ('start_lng', 'mean')

)
agg.rename(columns = {'start_station_name':'station_name'}, inplace = True)
agg.rename(columns = {'start_station_id':'station_id'}, inplace = True)
agg.rename(columns = {'start_lat':'Latitude'}, inplace = True)
agg.rename(columns = {'start_lng':'Longitude'}, inplace = True)

usage_agg = usage.groupby('station_name').agg(

    pickup_counts = ('pickup_counts', 'mean'),

    dropoff_counts = ('dropoff_counts', 'mean')

)
pick_usage = usage_agg.sort_values(by=['pickup_counts'], ascending=False)
drop_usage = usage_agg.sort_values(by=['dropoff_counts'], ascending=False)
pick_usage.reset_index(inplace=True)
drop_usage.reset_index(inplace=True)

# Inisialisasi aplikasi Dash
app = dash.Dash(__name__)
# Define functions for visualizations
def plot_pie(column):
    df_tree = bike[column].value_counts().reset_index()
    df_tree.columns = ['mode', 'count']
    df_tree['mode'] = df_tree['mode'].astype(str)
    df_tree = df_tree.sort_values(by=['mode']).head(10)
    
    fig = px.pie(
        df_tree,
        names='mode',
        values='count',
        color_discrete_sequence=px.colors.qualitative.Antique,
        title=f"Top 10 {column} distribution"
    )
    return fig

def time_series(data, indicator, daftar_stasiun):
    timeseries = data[data['station_name'].isin(daftar_stasiun)]
    fig = px.line(
        timeseries,
        x='date',
        y=indicator,
        color='station_name',
        title=f"Time Series Analysis: {indicator}"
    )
    fig.update_layout(xaxis_title='Date', yaxis_title='Count')
    return fig
def boxplot(data):
    numerik = data.select_dtypes(include=['float64', 'int64', 'int32']).columns
    fig = go.Figure()
    for column in numerik:
        fig.add_trace(go.Box(y=data[column], name=column))
    fig.update_layout(title="Boxplot for Numerical Columns")
    return fig

def histogram(data):
    numerik = data.select_dtypes(include=['float64', 'int64', 'int32']).columns
    fig = go.Figure()
    for column in numerik:
        fig.add_trace(go.Histogram(x=data[column], name=column, opacity=0.75))
    fig.update_layout(title="Histogram for Numerical Columns", barmode="overlay")
    return fig

def plot_tree_1(df, column):
    fig = px.treemap(
        df,
        path=['station_name'],
        values=column,
        color_discrete_sequence=px.colors.qualitative.Antique
    )
    return fig

def plot_map(data, indicator, color_map, title):
    fig = px.scatter_mapbox(
        data,
        lat="lat",
        lon="lng",
        color=indicator,
        color_continuous_scale=color_map,
        size_max=15,
        zoom=10,
        hover_name="station_name",
        title=title,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=10,
        mapbox_center={"lat": data["lat"].mean(), "lon": data["lng"].mean()},
        title=title,
    )
    return fig
def gap_time(indicator):
    fig = px.line(
        rent_day,
        x='date',
        y='minute',
        color='station_name',
        title=f"Time Series Analysis: Rent time per day & {indicator}"
    )
    fig.update_layout(xaxis_title='Date', yaxis_title='Count')
    return fig
# Layout
app.layout = html.Div([
    html.H1("Bike Usage Dashboard by Ikhsan Robbani", style={'textAlign': 'center'}),

    html.H2("Pie Charts"),
    dcc.Graph(id='rideable_type_pie', figure=plot_pie('rideable_type')),
    dcc.Graph(id='member_casual_pie', figure=plot_pie('member_casual')),

    html.H2("Boxplots for Numerical Columns"),
    dcc.Graph(id='boxplot_pick_usage', figure=boxplot(pick_usage)),
    dcc.Graph(id='boxplot_rent_day', figure=boxplot(rent_day)),

    html.H2("Histograms for Numerical Columns"),
    dcc.Graph(id='histogram_pick_usage', figure=histogram(pick_usage)),
    dcc.Graph(id='histogram_rent_day', figure=histogram(rent_day)),

    html.H2("Treemap Plots"),
    dcc.Graph(id='tree_pickup_counts', figure=plot_tree_1(pick_usage.head(20), 'pickup_counts')),
    dcc.Graph(id='tree_dropoff_counts', figure=plot_tree_1(drop_usage.head(20), 'dropoff_counts')),

    html.H2("Map Visualization"),
    dcc.Graph(id='map_hours', figure=plot_map(data=agg, indicator='hours', color_map='Plasma', title='Rata-rata lama peminjaman per jam')),

    html.H2("Time Series Analysis"),
    dcc.Dropdown(
        id='station_dropdown',
        options=[
            {'label': station, 'value': station} for station in usage['station_name'].unique()
        ],
        value=['10th & E St NW', 'Eads St & 15th St S'],
        multi=True,
        placeholder="Select stations for time series analysis"
    ),
    dcc.Graph(id='timeseries_pickup'),
    dcc.Graph(id='timeseries_dropoff'),
    html.H2("Another Time Series Analysis"),
    dcc.Graph(id='timeseries_gap_per_minute', figure=gap_time(indicator='hours'))
])

# Callbacks for interactive updates
@app.callback(
    Output('timeseries_pickup', 'figure'),
    Output('timeseries_dropoff', 'figure'),
    Input('station_dropdown', 'value')
)
def update_time_series(selected_stations):
    if not selected_stations:
        selected_stations = usage['station_name'].unique()  # default to all stations if none selected
    
    pickup_fig = time_series(data=usage, indicator='pickup_counts', daftar_stasiun=selected_stations)
    dropoff_fig = time_series(data=usage, indicator='dropoff_counts', daftar_stasiun=selected_stations)
    
    return pickup_fig, dropoff_fig

if __name__ == '__main__':
    app.run_server(debug=True)