#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Copyright 2015 @lmorillas. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Based on
https://github.com/google/google-api-python-client/blob/master/samples/service_account/tasks.py
by jcgregorio@google.com


"""

__author__ = 'morillas@google.com (Luis Miguel Morillas)'

import httplib2
import pprint
import sys

from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials, AccessTokenRefreshError

from geopy import geocoders
google = geocoders.GoogleV3()
yandex = geocoders.Yandex()
nom = geocoders.Nominatim()


import shelve



# Credentials for Service Accout
EMAIL_CLIENT = '696801545616-44i6o78jdoa7me4lr416n1d5rniidmns@developer.gserviceaccount.com'
FILE_KEY = 'pycal.p12'

def connect_calendar():
    # Load the key in PKCS 12 format that you downloaded from the Google API
    # Console when you created your Service account.
    f = file(FILE_KEY, 'rb')
    key = f.read()
    f.close()

    credentials = SignedJwtAssertionCredentials(EMAIL_CLIENT,
          key,
          scope=['https://www.googleapis.com/auth/calendar',
               'https://www.googleapis.com/auth/calendar.readonly'])

    http = httplib2.Http()
    http = credentials.authorize(http)


    service = build(serviceName='calendar', version='v3', http=http)

    return service

def calendar_events(service, cal_id):
    # Today: only envents present and future
    timeMin = datetime.datetime.now().strftime('%Y-%m-%dT00:00:00.000Z')

    events = []
    try:
        page_token = None
        while True:
            event_list = service.events().list(calendarId=cal_id, pageToken=page_token,
                    timeMin=timeMin).execute()
            events.extend([event for event in event_list['items']])
            page_token = event_list.get('nextPageToken')
            if not page_token:
                break

    except AccessTokenRefreshError:
        print ('The credentials have been revoked or expired, please re-run'
          'the application to re-authorize.')
    return events


def geolocate(address):
    global geocache
    address = address.encode('utf-8')
    if address not in geocache.keys():
        loc = google.geocode(address)
        if not loc:
            try:
                loc = yandex.geocode(address)
            except:
                pass
            if not loc:
                try:
                    loc = google.geocode(','.join(address.split(',')[1:]))
                except:
                    pass
        if loc:
            loc = loc.latitude, loc.longitude, loc.raw
            geocache[address] = loc
    else:
        loc = geocache.get(address)[:2]
    return loc

def loc_to_country(latlon):
    loc = nom.reverse(latlon)
    if loc:
        return loc.raw.get('address').get('country')


def event_to_item(event, cal):
    print event.get('summary'), ' --> ' ,
    item = {}
    item['description'] = event.get('description')
    item['id'] = event.get('id')
    item['start'] = event.get('start').get('date')
    if not item['start']:
        item['start'] = event.get('start').get('dateTime')
    item['end'] = event.get('end').get('date')
    if not item['end']:
        item['end'] = event.get('end').get('dateTime')
    item['label'] = event.get('summary')
    item['url'] = event.get('htmlLink')
    item['cal'] = cal
    address = event.get('location')
    location = geolocate(address)
    if location:
        lat = location[0]
        lon = location[1]
        item['latlon'] = "{},{}".format(lat, lon)
        print item['latlon']
        country = loc_to_country(item['latlon'])
        item['country'] = contry
    return item



if __name__ == '__main__':
    import datetime
    import json

    geocache = shelve.open('geocache.dat')


    # Cals IDs from https://wiki.python.org/moin/PythonEventsCalendar
    cal_id_python_events = 'j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com'
    cal_id_user_group = '3haig2m9msslkpf2tn1h56nn9g@group.calendar.google.com'

    items = []

    service = connect_calendar()
    events = calendar_events(service, cal_id_python_events)

    for event in events:
        items.append(event_to_item(event, 'pe'))

    events = calendar_events(service, cal_id_user_group)

    for event in events:
        items.append(event_to_item(event, 'ug'))

    geocache.sync()
    geocache.close()

    json.dump(items, open('events_python.json', 'w'))
