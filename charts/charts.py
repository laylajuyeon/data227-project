import pandas as pd
import altair as alt 
import json
import warnings
import numpy as np
warnings.filterwarnings('ignore')
alt.data_transformers.disable_max_rows()

def base_theme():
    return {
        "config": {
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 14},
            "legend": {"labelFontSize": 12, "titleFontSize": 14},
        }
    }

top6 = pd.read_csv('top6.csv')
with open('custom.geo.json') as f:
    world_geojson = json.load(f)
world_df = pd.DataFrame(world_geojson['features'])
world_df['name'] = world_df['properties'].apply(lambda x: x['name'])
world_df['pop'] = world_df['properties'].apply(lambda x: x['pop_est'])
regions = top6['region'].unique()
missing_countries = set(regions) - set(world_df['name'])
top6.loc[top6['region'] == 'Czech Republic', 'region'] = 'Czechia'
top6.loc[top6['region'] == 'Dominican Republic', 'region'] = 'Dominican Rep.'
top6.loc[top6['region'] == 'United States', 'region'] = 'United States of America'
top6 = top6[['title','date','region','streams']]
song_streams_by_country = top6.groupby(['title', 'region','date'])['streams'].sum().reset_index()
song_streams_by_country = song_streams_by_country.merge(world_df[['name', 'pop']], left_on='region', right_on='name', how='left')
song_streams_by_country = song_streams_by_country.drop(columns=['name'])
song_streams_by_country['streams_per_capita'] = ((song_streams_by_country['streams'] / song_streams_by_country['pop'])*100000).round(2)
song_streams_by_country = song_streams_by_country.dropna()
song_streams_by_country.rename(columns={'region':'name'},inplace=True)
brush = alt.selection_interval(encodings=['x'])
song_list = ['Dance Monkey','Shape of You','Someone You Loved','Sunflower - Spider-Man: Into the Spider-Verse','bad guy']
song_dropdown = alt.binding_select(options=song_list, name="Select Song: ")
song_select = alt.selection_point(fields=['title'], bind=song_dropdown, value=song_list[0])
other_line = alt.Chart(song_streams_by_country).mark_line(
    point=alt.OverlayMarkDef(size=20, filled=True)
).transform_filter(
    song_select 
).encode(
    x='date:T',
    y='mean(streams_per_capita):Q',
    color=alt.condition(
        brush, 
        alt.Color('mean(streams_per_capita):Q'), 
        alt.value('lightgray')
    )
).add_params(
    song_select, 
    brush
)
bl_line = alt.Chart(song_streams_by_country).mark_line(point=alt.OverlayMarkDef(size=20, filled=True)
).encode(
    x='date:T',
    y='mean(streams_per_capita):Q',
    color=alt.condition(
        brush, 
        alt.Color('mean(streams_per_capita):Q'), 
        alt.value('lightgray')
    )
).transform_filter(
    alt.datum.title == 'Blinding Lights'
).add_params(
    brush
)
background = alt.Chart(alt.Data(values=world_geojson, format=alt.DataFormat(property='features'))).mark_geoshape(
    fill='lightgray',
    stroke='white'
).properties(
    width=600,
    height=400
).project('equalEarth')

other_choropleth = alt.Chart(song_streams_by_country).transform_filter(
    brush
).transform_filter(
    song_select
).transform_aggregate(
    mean_spc = 'mean(streams_per_capita)',
    groupby = ['name']
).transform_lookup(
    lookup='name',
    from_=alt.LookupData(
        data=alt.Data(values=world_geojson, format=alt.DataFormat(property='features')), 
        key='properties.name'
    ),
    as_='geo'
).mark_geoshape().encode(
    shape='geo:G',
    color=alt.Color('mean_spc:Q', title='Avg Streams/100k'),
    tooltip=['name:N', alt.Tooltip('mean_spc:Q', format='.2f', title='Avg Streams')]
).project('equalEarth')

bl_choropleth = alt.Chart(song_streams_by_country).transform_filter(
    alt.datum.title == 'Blinding Lights'
).transform_aggregate(
    mean_spc = 'mean(streams_per_capita)',
    groupby = ['name']
).transform_lookup(
    lookup='name',
    from_=alt.LookupData(
        data=alt.Data(values=world_geojson, format=alt.DataFormat(property='features')), 
        key='properties.name'
    ),
    as_='geo'
).mark_geoshape().encode(
    shape='geo:G',
    color=alt.Color('mean_spc:Q', title='Avg Streams/100k'),
    tooltip=['name:N', alt.Tooltip('mean_spc:Q', format='.2f', title='Avg Streams')]
).project('equalEarth')

other_map = (background+other_choropleth)
bl_map = (background+bl_choropleth)

other = other_map & other_line
bl = bl_map & bl_line

dashboard = other|bl
