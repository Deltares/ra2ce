from pathlib import Path

import pandas as pd
from tabulate import tabulate
import plotly.graph_objs as go
from .gws_convertor import GWSRDConvertor
# N:\Projects\11210000\11210292\B. Measurements and calculations\Dealing with uncertainties


path_to_metadata = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\scenariolist2024_0_1.csv")

df = pd.read_csv(path_to_metadata)

rename_dict = {
    'y-coordinaten doorbraaklocatie': 'y',
    'x-coordinaten doorbraaklocatie': 'x',
    "Overschrijdingsfrequentie": "return_period",
}

df = df.rename(columns=rename_dict)
print(df.head())
print(tabulate(df.head(), headers='keys', tablefmt='psql'))

# put X and Y coordinates in a  tuple:
df['point'] = list(zip(df['x'], df['y']))

# filter only return period below 100000
# df = df[df['return_period'] < 1e5]
df = df[df['return_period'] > 1e5]
# df = df[df['Projectnaam'] == "VNK2 Zuid Holland"]
_coordinates_wgs = [
    GWSRDConvertor().to_wgs(pt[0], pt[1]) for pt in df['point']
]  # convert in GWS coordinates:
df["lat"] = [coord[0] for coord in _coordinates_wgs]
df["lon"] = [coord[1] for coord in _coordinates_wgs]

_fig = go.Figure()
_fig.add_trace(go.Scattermapbox(
    mode="markers",
    lon=[coord[1] for coord in _coordinates_wgs],
    lat=[coord[0] for coord in _coordinates_wgs],
    marker=go.scattermapbox.Marker(size=14, color=df['return_period'],  # Color by return periods
                                   colorscale='Viridis',  # Color scale
                                   showscale=True  # Show color scale
                                   ),

    text=[f'Scenario: {row["Scenarionaam"]}<br>Return Period: {row["return_period"]}<br>Value: {row["Beschrijving scenario"]}<br>ID: {row["Scenario ID"]}' for index, row in df.iterrows()],    hoverinfo='text+lat+lon',  # Display hover text and coordinates
    name="Points",
))

path_to_token = Path("")
with open(path_to_token) as f:
        token = f.read()
        
_fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=True,
    mapbox=dict(
        center=dict(lat=52.370216, lon=4.895168),
        zoom=6,
        accesstoken=token,
    ),
)
_fig.show()
