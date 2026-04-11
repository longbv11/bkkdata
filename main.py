import pandas as pd
import re # Import the regular expression module
datapath = './budapest_gtfs' #filepath of gtfs data folder here


routes = pd.read_csv(f'{datapath}/routes.txt').set_index('route_id')
trips = pd.read_csv(f'{datapath}/trips.txt').set_index('trip_id')
stops = pd.read_csv(f'{datapath}/stops.txt').set_index('stop_id')
stop_times = pd.read_csv(f'{datapath}/stop_times.txt')

#strip diacritics and create a new stop_name_normal column
import unicodedata
def strip_accents(text):
    """Strips accents from a string"""
    return ''.join(char for char in unicodedata.normalize('NFD', text) if unicodedata.category(char)!='Mn').strip()
stops['stop_name_normal'] = stops['stop_name'].apply(strip_accents)

