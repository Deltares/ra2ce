
from pathlib import Path
import geopandas as gpd
# make pretty map
import folium
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# import tabulate
import pandas
# from IPython.display import display

path_results = Path(r'P:\moonshot2-casestudy\RA2CE_HACKATHON_JULY\results')

# loop over all directiories and get names:

events = [x for x in path_results.iterdir() if x.is_dir()]
event = "TC_0631"
category = "hospital"

print(events)