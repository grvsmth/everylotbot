#!/usr/env python
# -*- coding: utf-8 -*-
# This file is part of everylotbot
# Copyright 2016 Neil Freeman, forked by Angus B. Grieve-Smith and Timm Dapper
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sqlite3
import logging
from io import BytesIO
import requests
import csv, random

TABLE = 'trees'
ID = 'tree_id'
SORT_ORDER = 'RANDOM()'

SVAPI = "https://maps.googleapis.com/maps/api/streetview"
GCAPI = "https://maps.googleapis.com/maps/api/geocode/json"

# constants for column names

LAT = 'Latitude'
LON = 'longitude'

QUERY = """SELECT
    {}
    FROM {}
    where {}
    ORDER BY {} ASC
    LIMIT 1;
"""

FIELDS = [
    'tree_id',
    'address',
    'boroname',
    'health',
    'latitude',
    'longitude',
    'spc_common',
    'spc_latin',
    'steward',
    'state',
    'status',
    'zip_city'
    ]

class EveryLot(object):

    def __init__(
        self,
        database,
        search_format=None,
        print_format=None,
        id_=None,
        phrasefile='data/phrases.csv',
        logger=logging.getLogger('everylot')
        ):
        """
        An everylot class immediately checks the database for the next available entry,
        or for the passed 'id_'. It stores this data in self.lot.
        :database str file name of database
        """
        self.logger = logger
        self.phrasefile = phrasefile

        # set address format for fetching from DB
        self.search_format = search_format or '{address}, {zip_city} {state}'
        self.print_format = print_format or '{spc_common} in {health} health at {address}, {boroname}\nhttps://tree-map.nycgovparks.org/#treeinfo-{tree_id}'

        self.logger.debug('searching google sv with %s', self.search_format)
        self.logger.debug('posting with %s', self.print_format)

        self.conn = sqlite3.connect(database)

        cond = 'tweeted = 0'
        if id_:
            cond = "{} = '{}'".format(ID, id_)

        fieldlist = ', '.join(FIELDS)
        curs = self.conn.execute(QUERY.format(fieldlist, TABLE, cond, SORT_ORDER))
        keys = [c[0] for c in curs.description]
        foo = list(curs.fetchone())
        self.lot = dict(zip(keys, foo))

    def aim_camera(self):
        '''Set field-of-view and pitch'''
        fov, pitch = 65, 10
        try:
            floors = float(self.lot.get('floors', 0)) or 2
        except TypeError:
            floors = 2

        if floors == 3:
            fov = 72

        if floors == 4:
            fov, pitch = 76, 15

        if floors >= 5:
            fov, pitch = 81, 20

        if floors == 6:
            fov = 86

        if floors >= 8:
            fov, pitch = 90, 25

        if floors >= 10:
            fov, pitch = 90, 30

        return fov, pitch

    def get_streetview_image(self, key):
        '''Fetch image from streetview API'''
        params = {
            "location": '{},{}'.format(self.lot[LAT], self.lot[LON]),
            "key": key,
            "size": "1000x1000"
        }

        params['fov'], params['pitch'] = self.aim_camera()

        r = requests.get(SVAPI, params=params)
        self.logger.debug(r.url)

        sv = BytesIO()
        for chunk in r.iter_content():
            sv.write(chunk)

        sv.seek(0)
        return sv


    def pick_sentence(self):
        """ Randomly select a sentence appropriate to the species and
        health status

        The function takes a dictionary with the tree dataset for a
        single tree as input, randomly selects a sentence that
        fullfills the spc_latin, health and steward criteria (if
        given) and replaces any mention of tree parameters inside
        curly braces.

        """
        treeInfo = self.lot
        pickedSentence = ''

        # pick a sentence
        with open(self.phrasefile, 'rU') as csvfile:
            reader = csv.DictReader(csvfile)

            sentenceList = []
            for row in reader:
                sentenceList.append(row)

            random.shuffle(sentenceList)

            for row in sentenceList:
                isRejected = False
                for myfilter in ['spc_latin', 'health', 'steward', 'status']:
                    if len(row[myfilter]) > 0 and not row[myfilter] == treeInfo[myfilter]:
                        isRejected = True
                        break

                if isRejected:
                    continue

                pickedSentence = row['sentence']
                break

            # do replacements
            return pickedSentence.format(**treeInfo)

        return ""

    def compose(self, media_id_string):
        '''
        Compose a tweet, including media ids and location info.
        :media_id_string str identifier for an image uploaded to Twitter
        '''
        self.logger.debug("media_id_string: %s", media_id_string)

        # Let missing addresses play through here, let the program leak out a bit
        self.lot['address'] = self.lot['address'].title()
        if ('Honeylocust var. inermis' == self.lot['spc_common']):
            self.lot['spc_common'] = 'Honey locust'

        status = self.pick_sentence()

        return {
            "status": status,
            "lat": self.lot.get(LAT, 0.),
            "long": self.lot.get(LON, 0.),
            "media_ids": [media_id_string]
        }

    def mark_as_tweeted(self):
        tweetedq = "UPDATE {} SET tweeted = 1 WHERE {} = ?".format(TABLE, ID)
        self.conn.execute(tweetedq, (self.lot[ID],))
        self.conn.commit()

