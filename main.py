import pandas as pd
datapath = './budapest_gtfs' #filepath of gtfs data folder here


routes = pd.read_csv(f'{datapath}/routes.txt', dtype={'route_id': str}).set_index('route_id')
trips = pd.read_csv(f'{datapath}/trips.txt', dtype={'trip_id': str, 'route_id': str}).set_index('trip_id')
stops = pd.read_csv(f'{datapath}/stops.txt', dtype={'stop_id': str}).set_index('stop_id')
stop_times = pd.read_csv(f'{datapath}/stop_times.txt', dtype={'stop_id': str, 'trip_id': str})

#strip diacritics and create a new stop_name_normal column (normalized: no diacritics, all lowercase)
import unicodedata
def strip_accents(text):
    """Strips accents from a string"""
    return ''.join(char for char in unicodedata.normalize('NFD', text) if unicodedata.category(char)!='Mn').strip()
stops['stop_name_normal'] = stops['stop_name'].apply(strip_accents).str.lower()
routes['route_name_normal'] = routes['route_desc'].apply(strip_accents).str.lower()
trips['trip_headsign_normal'] = trips['trip_headsign'].apply(strip_accents).str.lower()

def get_modes(stop_name):
    '''
    Returns the modes that serve a stop, for a given normalized name
    '''
    matched_stop_id = stops[stops['stop_name_normal'] == stop_name].index
    matched_trip_id = stop_times[stop_times['stop_id'].isin(matched_stop_id)]['trip_id'].unique()
    matched_route_id = trips.loc[matched_trip_id, 'route_id'].unique()
    
    return routes.loc[routes.index.isin(matched_route_id), ['route_short_name', 'route_type', 'route_desc']]
    