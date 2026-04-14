import pandas as pd
datapath = './budapest_gtfs' #provide filepath of gtfs data folder here


routes = pd.read_csv(f'{datapath}/routes.txt', dtype={'route_id': str}).set_index('route_id')
trips = pd.read_csv(f'{datapath}/trips.txt', dtype={'trip_id': str, 'route_id': str}).set_index('trip_id')
stops = pd.read_csv(f'{datapath}/stops.txt', dtype={'stop_id': str}).set_index('stop_id')
stop_times = pd.read_csv(f'{datapath}/stop_times.txt', dtype={'stop_id': str, 'trip_id': str})

#strip diacritics and create a new stop_name_normal column (normalized means no diacritics, all lowercase)
import unicodedata
def strip_accents(text):
    """Strips accents from a string"""
    return ''.join(char for char in unicodedata.normalize('NFD', text) if unicodedata.category(char)!='Mn').strip()
stops['stop_name_normal'] = stops['stop_name'].apply(strip_accents).str.lower()
routes['route_name_normal'] = routes['route_desc'].apply(strip_accents).str.lower()
trips['trip_headsign_normal'] = trips['trip_headsign'].apply(strip_accents).str.lower()

def get_modes(stop_name):
    '''
    Returns the modes that serve a stop, for a given NORMALIZED name
    e.g. get_modes('harminckettesek tere')
    '''
    matched_stop_id = stops[stops['stop_name_normal'] == stop_name].index
    matched_trip_id = stop_times[stop_times['stop_id'].isin(matched_stop_id)]['trip_id'].unique()
    matched_route_id = trips.loc[matched_trip_id, 'route_id'].unique()

    resultModes = routes.loc[routes.index.isin(matched_route_id), ['route_short_name', 'route_type', 'route_desc']]
    modeMap = {0: 'tram', 3: 'bus', 11: 'trolleybus'}
    resultModes['route_type'] = resultModes['route_type'].replace(modeMap)

    return resultModes.rename(columns={'route_short_name': 'Route Number', 'route_type': 'Mode', 'route_desc': 'Destination'})


def get_timetable(stop_name, route_filter = None, hour_filter = None):
    '''
    Returns a schedule of departure times and routes, for a given normalized stop name.
    e.g. get_timetable('harminckettesek tere', 9, 8)
    '''
    matched_stop_id = stops[stops['stop_name_normal'] == stop_name].index
    ttable = stop_times[stop_times['stop_id'].isin(matched_stop_id)][['trip_id', 'departure_time']]
    ttable = ttable.sort_values('departure_time')
    ttable = ttable.merge(trips[['trip_headsign', 'route_id']], left_on='trip_id', right_index = True)
    ttable = ttable.merge(routes[['route_short_name']], left_on='route_id', right_index = True)

    if route_filter is not None:
        ttable = ttable[ttable['route_short_name'] == str(route_filter)]
        
    if hour_filter is not None:
        hour_str = str(hour_filter).zfill(2)
        ttable = ttable[ttable['departure_time'].str.startswith(f"{hour_str}:")]
        
    return ttable[['departure_time', 'route_short_name', 'trip_headsign']].rename(columns = {
        'departure_time': 'Time', 
        'route_short_name': 'Route No', 
        'trip_headsign': 'Destination'
        })

# TODO: all the funcs below  

def get_route_stops(route_short_name, direction_id=0):
    '''
    Returns an ordered list of stops for a given route, sorted by stop_sequence.
    '''
    pass

def get_direct_connection(start_stop, end_stop):
    '''
    Returns a list of routes that provide a direct connection between two normalized stop names.
    '''
    pass
