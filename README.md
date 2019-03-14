# google-maps-gps-lookup

#Create virtualenv, and run pip install
```
    pip install googlemaps
    pip install traceback
    pip install psycopg2
```
# Dict format
```
dicts_with_streets = {
'StreetName': {
    'lat': lat, - This is for those with no street number
    'lng': lng, - This is for those with no street number
    'street_number_1': {'lat': lat1, 'lng': lng1},
    'street_number_2': {'lng': lng2, 'lat': lat2},
    'street_number_3': {'lng': lng3, 'lat': lat3}
}
```
