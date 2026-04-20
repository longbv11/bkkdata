# BKKData, an entry-level data science personal project

### Introduction

This is a program written using Python and Pandas in order to filter through and wrangle GTFS data. The program, in its current state, is intended to be run as a Jupyter notebook, but I prefer writing in python files and using VSCode's interactive window function to run code blocks. CLI and eventually UI implementation will come, eventually.

Theoretically the program should work with any properly formatted GTFS-Static file. However, this specific program is intended to handle specifically [Budapest's data acquired from BKK OpenData](https://opendata.bkk.hu/home), hence the name.

This is a work in progress.

### Current functionality:
- `get_modes(stop_name, hour_filter=None)`: Returns the modes that serve a stop, for a given stop name.
- `get_timetable(stop_name, route_filter=None, hour_filter=None)`: Returns a schedule of departure times and routes, for a given stop name.
- `get_route_stops(route_number, direction_id=0)`: Returns an ordered list of stops for a given route, sorted by stop_sequence.
- `get_direct_connection(start_stop, end_stop, hour_filter=None)`: Returns a list of routes that provide a direct connection between two normalized stop names.
- `get_transfer_connection(start_stop, end_stop, hour_filter=None)`: Returns a possible routing between two stops that have no direct connection and require ONE transfer