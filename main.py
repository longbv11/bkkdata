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

def get_modes(stop_name, hour_filter=None):
    '''
    Returns the modes that serve a stop, for a given NORMALIZED name
    e.g. get_modes('harminckettesek tere', hour_filter=14)
    '''
    matched_stop_id = stops[stops['stop_name_normal'] == stop_name].index
    
    st = stop_times[stop_times['stop_id'].isin(matched_stop_id)]
    if hour_filter is not None:
        hour_str = str(hour_filter).zfill(2)
        st = st[st['departure_time'].str.startswith(f"{hour_str}:")]
        
    matched_trip_id = st['trip_id'].unique()
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

def get_route_stops(route_number, direction_id=0):
    '''
    Returns an ordered list of stops for a given route, sorted by stop_sequence.
    e.g. get_route_stops(83, 0)
    '''
    matched_route_id = routes[routes['route_short_name'] == str(route_number)].index
    matched_trips = trips[(trips['route_id'].isin(matched_route_id)) & (trips['direction_id'] == direction_id)]

    rep_trip = matched_trips.index[0]

    route_stops = stop_times[stop_times['trip_id'] == rep_trip][['stop_id', 'stop_sequence']]
    route_stops = route_stops.merge(stops[['stop_name']], left_on = 'stop_id', right_index = True)
    route_stops = route_stops.sort_values('stop_sequence')

    return (f'Stops for route number {route_number} on direction {direction_id}:'), route_stops[['stop_sequence', 'stop_name']].set_index('stop_sequence')

def get_direct_connection(start_stop, end_stop, hour_filter = None):
    '''
    Returns a list of routes that provide a direct connection between two normalized stop names.
    e.g. get_direct_connection('astoria', 'kalvin ter', 14)
    '''
    start_stopid = stops[stops['stop_name_normal'] == start_stop].index
    end_stopid = stops[stops['stop_name_normal'] == end_stop].index
    
    st_start = stop_times[stop_times['stop_id'].isin(start_stopid)][['trip_id', 'stop_sequence', 'departure_time']]
    if hour_filter is not None:
        hour_str = str(hour_filter).zfill(2)
        st_start = st_start[st_start['departure_time'].str.startswith(f"{hour_str}:")]
        
    st_start = st_start[['trip_id', 'stop_sequence']]
    st_end = stop_times[stop_times['stop_id'].isin(end_stopid)][['trip_id', 'stop_sequence']]

    common_trip = st_start.merge(st_end, on = 'trip_id', suffixes = ('_start', '_end'))
    valid_trip = common_trip[common_trip['stop_sequence_start'] < common_trip['stop_sequence_end']]

    if valid_trip.empty:
        return (f'No direct connection between {start_stop} and {end_stop}, attempting to find one-transfer connections:'), get_transfer_connection(start_stop, end_stop)
    
    valid_trips_info = trips.loc[valid_trip['trip_id'].unique(), ['route_id', 'trip_headsign']].drop_duplicates()
    result = valid_trips_info.merge(routes[['route_short_name', 'route_type']], left_on='route_id', right_index=True)
    
    modeMap = {0: 'tram', 3: 'bus', 11: 'trolleybus', '0': 'tram', '3': 'bus', '11': 'trolleybus'}
    result['route_type'] = result['route_type'].replace(modeMap)
    
    return result[['route_short_name', 'route_type', 'trip_headsign']].rename(columns={
        'route_short_name': 'Route Number', 
        'route_type': 'Mode', 
        'trip_headsign': 'Destination'
    }).reset_index(drop=True)

#TODO: all these by tuesday

def get_transfer_connection(start_stop, end_stop, hour_filter=None):
    '''
    An upgrade to get_direct_connection that finds a path between two stops requiring exactly 
    ONE transfer. Returns the suggested transfer station and both route numbers.
    '''
    start_stopid = stops[stops['stop_name_normal'] == start_stop].index
    end_stopid = stops[stops['stop_name_normal'] == end_stop].index

    #finds all stopping events that serves the start and end
    st_start = stop_times[stop_times['stop_id'].isin(start_stopid)][['trip_id', 'stop_sequence', 'stop_id', 'departure_time']]
    if hour_filter is not None:
        hour_str = str(hour_filter).zfill(2)
        st_start = st_start[st_start['departure_time'].str.startswith(f"{hour_str}:")]
        
    st_start = st_start[['trip_id', 'stop_sequence', 'stop_id']]
    st_end = stop_times[stop_times['stop_id'].isin(end_stopid)][['trip_id', 'stop_sequence', 'stop_id']]

    #finds all potential transfer points
    first_leg = st_start.merge(stop_times[['trip_id', 'stop_id', 'stop_sequence']], on= 'trip_id', suffixes=('_start', '_first_leg'))
    first_leg = first_leg[first_leg['stop_sequence_start'] < first_leg['stop_sequence_first_leg']]

    second_leg = st_end.merge(stop_times[['stop_id', 'trip_id', 'stop_sequence']], on = 'trip_id', suffixes=('_end', '_second_leg'))
    second_leg = second_leg[second_leg['stop_sequence_end'] > second_leg['stop_sequence_second_leg']]

    # Map stop IDs to their normalized names to allow transfers within the same station complex
    first_leg['transfer_match_name'] = first_leg['stop_id_first_leg'].map(stops['stop_name_normal'])
    second_leg['transfer_match_name'] = second_leg['stop_id_second_leg'].map(stops['stop_name_normal'])

    # Merge for common transfer points using the normalized station name
    transfer_points = first_leg.merge(second_leg[['trip_id', 'transfer_match_name']], on='transfer_match_name', suffixes=('_leg1', '_leg2'))
    
    if transfer_points.empty:
        return f'No single-transfer routes between {start_stop} and {end_stop} :('
    
    unique_transfers = transfer_points[['trip_id_leg1', 'trip_id_leg2', 'stop_id_first_leg']].drop_duplicates()

    unique_transfers['route_id1'] = unique_transfers['trip_id_leg1'].map(trips['route_id'])
    unique_transfers['route_id2'] = unique_transfers['trip_id_leg2'].map(trips['route_id'])

    valid_transfers = unique_transfers[unique_transfers['route_id1'] != unique_transfers['route_id2']].copy()
    if valid_transfers.empty:
        return f'A direct connection exists for this stop pairing, attempting to find:', get_direct_connection(start_stop, end_stop)
    valid_transfers['First Route'] = valid_transfers['route_id1'].map(routes['route_short_name'])
    valid_transfers['Transfer Station'] = valid_transfers['stop_id_first_leg'].map(stops['stop_name'])
    valid_transfers['Second Route'] = valid_transfers['route_id2'].map(routes['route_short_name'])

    final_results = valid_transfers[['First Route', 'Transfer Station', 'Second Route']].drop_duplicates()

    return final_results


def get_route_frequency(route_number, stop_name, start_hour=7, end_hour=9):
    '''
    Calculates the average headway (time between departures) in minutes for a specific route 
    at a given stop during a specified time window (e.g., morning peak hours).
    '''
    pass

def get_busiest_stops(top_n=10):
    '''
    Analyzes the entire network to find the stops with the highest volume of daily departures 
    or the highest number of unique intersecting routes.
    '''
    pass


def get_service_span(route_number, direction_id=0):
    '''
    Returns the first departure (opening) and last departure (closing) times for a route, 
    calculating the total active hours of service for the day.
    '''
    pass



    
