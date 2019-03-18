# https://github.com/googlemaps/google-maps-services-python
import googlemaps
from datetime import datetime
import traceback
import psycopg2
import time
import logging

# I personally use large try blocks
try:
    # for logging if needed
    logging.basicConfig(filename='errors.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    # simple postgres database connection, for more information see psycopg2
    conn = psycopg2.connect("host=host_address dbname=database_name user=database_user password=database_password")

    # if encoding is needed
    conn.set_client_encoding('WIN1250')

    cur = conn.cursor()

    # simple sql query to get streets data from database, change as needed
    cur.execute("SELECT streets_db.uuid, streets_db.name, streets_db.number, streets_db.city, streets_db.state \
                FROM streets_db \
                WHERE streets_db.lat = 0 \
                order by streets_db.uuid\
                limit 600;")

    res = cur.fetchall()

    # number of Google API calls
    google_calls = 0

    # Google Api key
    gmaps = googlemaps.Client(key='your_key')

    # array with street names that have multiple records returned from Google Maps
    multiple_results = []
    # dict containing all other dicts with street results
    dicts_with_streets = {}

    streets_with_no_result = []

    for each in res:

        # if length of street name is less than 1 character, or it can be changed to fit your needs
        if len( each[1] ) <= 1:
            continue

        # strip is used to delete white spaces if any are present
        street = each[1].strip()
        number = each[2].strip()
        city = each[3].strip()
        state = each[4].strip()
        uuid = each[0]
        lat = 0
        lng = 0

        # since google only lets you make a certain number of calls and you need to wait, this keeps track if application should wait before making another call
        wait = False

        # This is used if there are users with same address but different number, example 5/3, 5/4, etc. for them use the same GPS coordinates, no need to make another API call
        divide = False

        # print the current street we are working for
        print('\n'+street + ' ' + number + ', '+ city + ', ' + state)

        # checks if number is not empty or blank or whatever you may need
        if number == None or number == '     ' or number == '':
            # users exist with no street number, just use overall Google Api GPS coordinates, usually it is middle of the street, for first call it is empty, later it will lookup and see if it exist already so we don't waste another API call
            if street in dicts_with_streets:
                lat = dicts_with_streets[street]['lat']
                lng = dicts_with_streets[street]['lng']

        # checks if street number has divide in it or appartment
        elif '/' in number:
            divide = number.split('/')
            # we need only the first part for coordinates of the building and API call, users street address remains the same and in database - must point it out for not so tech savy people
            number = divide[0]

            # here we check if street is in dicts_with_streets
            if street in dicts_with_streets:
                # and if this number exists in street
                if number in street:
                    # if it exist use these coordinates
                    lat = dicts_with_streets[street][number]['lat']
                    lng = dicts_with_streets[street][number]['lng']

        # if no coordinates are found, make API call
        if lat == 0:
            # check how many calls are made to limit application API calls
            if google_calls > 300:
                break

            if street in multiple_results:
                # Since I haven't chosen what to do with streets with multiple results, this will simply skip it
                print('street in multiple_results')
                continue

            if street in streets_with_no_result:
                print('streets_with_no_result')
                continue

            # Geocoding an address
            geocode_result = gmaps.geocode(street + ' ' + number + ', '+ city + ', ' + state)

            google_calls += 1

            print('google_calls',google_calls, '\n')
            print('\ngeocode_result',geocode_result)

            # Since we made Google API call, we need to wait 5s
            wait = True

            # if we got empty result
            if len(geocode_result) == 0:
                # we can also keep track of streets with no result
                streets_with_no_result.append(street)
                continue

            # if there are more than 1 results, put it in the list to be skipped
            if len(geocode_result) > 1:
                multiple_results.append(street)
                continue

            # only if and when there is 1 result we get to here
            lng = geocode_result[0]['geometry']['location']['lng']
            lat = geocode_result[0]['geometry']['location']['lat']

        # Here I update dict with results
        # check if street exist in dict with streets
        if street in dicts_with_streets:
            if number in dicts_with_streets[street]:
                lat = dicts_with_streets[street][number]['lat']
                lng = dicts_with_streets[street][number]['lng']
            else:
                dicts_with_streets[street][number] = {'lng':lng, 'lat':lat}
        else:
            # we create dict for said street and add all other values
            dicts_with_streets[street] = {}
            dicts_with_streets[street][number] = {}
            dicts_with_streets[street][number] = {'lat':lat, 'lng':lng}

        # The dict
        if not 'lat' in dicts_with_streets[street]:
            dicts_with_streets[street]['lat'] = lat
            dicts_with_streets[street]['lng'] = lng

        print('\nlat, lng, uuid',lat, lng, uuid)

        print('dicts_with_streets',dicts_with_streets,'\n')

        # sql to be run to update
        sql = "UPDATE streets_db SET lng=(%s), lat=(%s) WHERE uuid = (%s)"

        # execut sql with said values
        cur.execute(sql, (lat, lng, uuid));

        # commit
        conn.commit()

        # if we made API call we need to wait no less than 5s
        if wait:
            time.sleep(6)
    
    # If you want to have log of the streets with no results, not needed since SQL will always skip those with latitude and longitude 
    # logging.warning(streets_with_no_result)
    # logging.warning(multiple_results)
    cur.close()
    conn.close()

except Exception as e:
    # traceback will print whatever error we get
    traceback.print_exc()
    # and we close connection to database
    # note there is no rollback here
    logging.error(e)
    # if no connection was established
    try:
        cur.close()
        conn.close()
    except:
        pass
