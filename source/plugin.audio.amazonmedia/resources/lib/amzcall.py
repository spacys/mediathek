#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math, random, requests, json, datetime
from resources.lib.tools import AMtools
from resources.lib.api import AMapi

class AMcall( AMtools ):
    """
    Common class for the Amazon API calls
    """
    def getMaestroID( self ):
        """
        Calculate random Player ID
        """
        a = str(
            float.hex(
                float(
                    math.floor(16 * (1 + random.random()))
                )
            )
        )[4:5]
        uid = '{}-{}-dmcp-{}-{}{}'.format(
            self.doCalc(),
            self.doCalc(),
            self.doCalc(),
            self.doCalc(),
            a
        )
        return 'Maestro/1.0 WebCP/1.0.202638.0 ({})'.format( uid )
    
    @staticmethod
    def doCalc():
        """
        Calculate random ID
        """
        return str(
            float.hex(
                float(
                    math.floor(65536 * (1 + random.random()))
                )
            )
        )[4:8]

    def amzCall( self, amzUrl, mode, referer=None, asin=None, mediatype=None ):
        """
        Main function for the Amazon Call
        :param str amzUrl:  Endpoint ID
        :param str mode:    Request Addon Data ID
        :param str referer: no longer in use
        :param str asin:    Playlist-, Albums-, Song-, Artist-, Station-ID
        :param str/array mediatype: content depends on the caller function
        """
        self.credentials = self.load()

        amPath = AMapi.getAPI( amzUrl )

        url  = '{}/{}/api/{}'.format(
            self.musicURL.format( self.credentials.USERTLD ),
            self.credentials.REGION,
            amPath['path']
        )

        head = self.prepReqHeader(amPath['target'])
        data = self.prepReqData( mode, asin, mediatype )

        resp = requests.post( url=url, headers=head, data=data, cookies=self.credentials.COOKIE )
        self.saveCookie( self.credentials.COOKIE )

        if self.G['logging']:
            self.log('url: ' + url)
            self.log('reason: ' + resp.reason + ', code: ' + str(resp.status_code))
            self.log(resp.text)

        if mode == 'getTrack' or mode == 'getTrackHLS' or mode == 'getTrackDash':
            return resp
        else:
            return resp.json()

    def prepReqData( self, mode, asin=None, mediatype=None ):
        """
        Provide request data structure for Amazon API calls

        rankType:           newly-added, popularity-rank, top-sellers, newly-released
        requestedContent:   FULL_CATALOG, KATANA, MUSIC_SUBSCRIPTION, PRIME_UPSELL_MS, ALL_STREAMABLE, PRIME
        features:           fullAlbumDetails, playlistLibraryAvailability, childParentOwnership, trackLibraryAvailability,
                            hasLyrics, expandTracklist, ownership, popularity, albumArtist, collectionLibraryAvailability
        types:              artist, track, album, similarArtist, playlist, station

        :param str mode:            Request Addon Data ID
        :param str asin:            Playlist-, Albums-, Song-, Artist-, Station-ID
        :param str/array mediatype: content depends on the caller function
        """
        #data = json.dumps(data)
        #data = json.JSONEncoder().encode(data)
        token = self.G['addonArgs'].get('token', [''])
        if   mode == 'searchItems':
            if self.G['addonArgs'].get('token', [None])[0] == None:
                prop = 'maxResults'
                val = self.G['maxResults']
            else:
                prop = 'pageToken'
                val = self.G['addonArgs'].get('token', [None])[0]

            data = {
                'customerIdentity': {
                    'deviceId': self.credentials.DEVICEID,
                    'deviceType': self.credentials.DEVICETYPE,
                    'sessionId': '',
                    'customerId': self.credentials.CUSTOMERID
                },
                'features': {
                    'spellCorrection': {
                        'allowCorrection': 'true'
                    }
                },
                'locale': self.credentials.LOCALE,
                'musicTerritory': self.credentials.MUSICTERRITORY,
                'query': asin,
                'requestContext': 'true',
                'resultSpecs': [{
                    'label': mediatype[0], #'albums',
                    'documentSpecs': [{
                        'type': mediatype[1], #'catalog_album',
                        'fields': [
                            '__DEFAULT',
                            'artOriginal',
                            'artMedium',
                            'artLarge',
                            'artFull',
                            'isMusicSubscription',
                            'primeStatus',
                            'albumName',
                            'albumReleaseDate'
                        ]
                    }],
                    prop : val,
                    'contentRestrictions': {
                        'allowedParentalControls': {
                            'hasExplicitLanguage': 'true'
                        },
                        'eligibility': {
                            'tier': self.credentials.ACCESSTYPE
                        }
                    }
                }]
            }
            data = json.JSONEncoder().encode(data)

        elif mode == 'getArtistDetails':
            if self.credentials.ACCESSTYPE == 'UNLIMITED':
                tier = 'MUSIC_SUBSCRIPTION'
            else:
                tier = self.credentials.ACCESSTYPE
            data  = {
                'requestedContent': tier,
                'asin': asin,
                'types':[{
                    'sortBy':'popularity-rank',
                    'type':'album',
                    'maxCount':     self.G['maxResults'],
                    'nextToken':    self.G['addonArgs'].get('token', [''])[0]
                }],
                'features':[
                    #'expandTracklist',
                    #'collectionLibraryAvailability',
                    'popularity'
                ],
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'recentlyplayed':
            data = {
                'activityTypeFilters': [mediatype],
                'pageToken':        token[0],
                'lang':             self.credentials.LOCALE,
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID,
            }
            data = json.dumps(data)

        elif mode == 'getMetaTracks':
            """
            available fields in attributeList:
            ['uploaded', 'composer', 'primaryGenre', 'albumArtistName', 'albumCoverImageFull', 'sortAlbumArtistName', 'purchased', 'fileExtension', 'albumReleaseDate',
            'albumAsin', 'fileName', 'albumCoverImageXL', 'albumContributors', 'songWriter', 'albumCoverImageMedium', 'albumCoverImageLarge', 'orderId', 'assetType',
            'parentalControls', 'marketplace', 'lyricist', 'localFilePath', 'albumRating', 'creationDate', 'bitrate', 'albumArtistAsin', 'performer', 'purchaseDate',
            'sortArtistName', 'albumPrimaryGenre', 'primeStatus', 'discNum', 'status', 'rogueBackfillDate', 'physicalOrderId', 'artistName', 'lastUpdatedDate', 'albumCoverImageTiny',
            'duration', 'audioUpgradeDate', 'albumCoverImageSmall', 'errorCode', 'asin', 'title', 'isMusicSubscription', 'contributors', 'sortTitle', 'objectId', 'albumName',
            'trackNum', 'sortAlbumName', 'publisher', 'fileSize', 'rating', 'md5', 'artistAsin']
            """
            data = {
                'filterList':[
                    {
                        'attributeName':'albumAsin',
                        'comparisonType':'EQUALS',
                        'attributeValue':asin
                    },
                    {
                        'attributeName':'status',
                        'comparisonType':'EQUALS',
                        'attributeValue':'AVAILABLE'
                    }
                ],
                'attributeList':[
                    'trackNum',
                    'discNum',
                    'duration',
                    'albumReleaseDate',
                    'primaryGenre',
                    'albumName',
                    'artistName',
                    'title',
                    'asin',
                    'objectId',

                    'albumAsin',
                    'artistAsin',
                    'purchased',
                    'status',
                    'primeStatus'
                ],
                'sortOrder':{
                    'sort':'albumName',
                    'order':'ASC'
                },
                'maxResults':       self.G['maxResults'],
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID,
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE
            }
            data = json.JSONEncoder().encode(data)

        elif mode == 'recentlyaddedsongs':
            data = {
                'selectCriteria': None,
                'albumArtUrlsRedirects': 'false',
                'distinctOnly': 'false',
                'countOnly': 'false',
                'sortCriteriaList': None,
                'maxResults': self.G['maxResults'],
                'nextResultsToken': self.G['addonArgs'].get('token', [0])[0],
                'selectCriteriaList.member.1.attributeName': 'status',
                'selectCriteriaList.member.1.comparisonType': 'EQUALS',
                'selectCriteriaList.member.1.attributeValue': 'AVAILABLE',
                'selectCriteriaList.member.2.attributeName': 'creationDate',
                'selectCriteriaList.member.2.comparisonType': 'GREATER_THAN',
                'selectCriteriaList.member.2.attributeValue': datetime.date.today()-datetime.timedelta(days=90),
                'sortCriteriaList.member.1.sortColumn': 'creationDate',
                'sortCriteriaList.member.1.sortType': 'DESC',
                'Operation': 'selectTrackMetadata',
                'caller': 'getServerSmartList',
                'ContentType': 'JSON',
                'customerInfo.customerId':  self.credentials.CUSTOMERID,
                'customerInfo.deviceId':    self.credentials.DEVICEID,
                'customerInfo.deviceType':  self.credentials.DEVICETYPE
            }

        elif mode == 'followedplaylists':
            data = {
                'optIntoSharedPlaylists': 'true',
                'entryOffset':      0, # todo
                'pageSize':         self.G['maxResults'],
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'getownedplaylists':
            data = {
                'entryOffset':      0, #todo
                'pageSize':         self.G['maxResults'],
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'getplaylistsbyid':
            data = {
                'playlistIds':      [asin],
                'requestedMetadata':['asin','albumName','sortAlbumName','artistName','primeStatus','isMusicSubscription','duration','sortArtistName','sortAlbumArtistName','objectId','title','status','assetType','discNum','trackNum','instantImport','purchased'],
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'playlist':
            data  = {
                'rankType':         mediatype,
                'requestedContent': 'PRIME',#self.credentials.ACCESSTYPE,
                'features':         ['playlistLibraryAvailability','collectionLibraryAvailability'],
                'types':            ['playlist'],
                'nextTokenMap':     {'playlist' : token[0]},
                'maxCount':         self.G['maxResults'],
                'lang':             self.credentials.LOCALE,
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'recommendations':
            # mediatypes:
            # mp3-prime-browse-carousels_playlistStrategy
            # mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy
            # mp3-prime-browse-carousels_mp3PrimeTracksStrategy
            # mp3-prime-browse-carousels_mp3ArtistStationStrategy
            token = self.G['addonArgs'].get('token', [0])
            data  = {
                'maxResultsPerWidget' : self.G['maxResults'],
                'minResultsPerWidget' : 1,
                'lang' :                self.credentials.LOCALE,
                'requestedContent' :    'PRIME', #self.credentials.ACCESSTYPE,
                'musicTerritory' :      self.credentials.MUSICTERRITORY,
                'deviceId' :            self.credentials.DEVICEID,
                'deviceType' :          self.credentials.DEVICETYPE,
                'customerId' :          self.credentials.CUSTOMERID,
                'widgetIdTokenMap' : { mediatype : int(token[0]) }
            }
            data = json.dumps(data)

        elif mode == 'new_recommendations':
            data = {
                'deviceId' :            self.credentials.DEVICEID,
                'deviceType' :          self.credentials.DEVICETYPE,
                'customerId' :          self.credentials.CUSTOMERID,
                'musicTerritory' :      self.credentials.MUSICTERRITORY,
                'lang' :                self.credentials.LOCALE,
                'requestedContent' :    'PRIME_UPSELL_MS',#,
                'options' :             ['populateRecentlyPlayed']
                #'options' :             'requestBundesligaContent'
            }
            data = json.dumps(data)
            #data = json.JSONEncoder().encode(data)

        elif mode == 'getPurchased': # purchased and all Songs / purchased Albums
            data = {
                'searchReturnType': mediatype[0],
                'searchCriteria.member.1.attributeName': 'assetType',
                'searchCriteria.member.1.comparisonType': 'EQUALS',
                'searchCriteria.member.1.attributeValue': 'AUDIO',
                'searchCriteria.member.2.attributeName':  'status',
                'searchCriteria.member.2.comparisonType': 'EQUALS',
                'searchCriteria.member.2.attributeValue': 'AVAILABLE',
                #'searchCriteria.member.3.attributeName':  filter[0],
                #'searchCriteria.member.3.comparisonType': filter[1],
                #'searchCriteria.member.3.attributeValue': filter[2],
                'albumArtUrlsRedirects': 'false',
                'distinctOnly': 'false',
                'countOnly': 'false',
                'selectedColumns.member.1': 'trackNum',
                'selectedColumns.member.2': 'discNum',
                'selectedColumns.member.3': 'duration',
                'selectedColumns.member.4': 'albumReleaseDate',
                'selectedColumns.member.5': 'primaryGenre',
                'selectedColumns.member.6': 'albumName',
                'selectedColumns.member.7': 'artistName',
                'selectedColumns.member.8': 'title',
                'selectedColumns.member.9': 'asin',
                'selectedColumns.member.10': 'objectId',
                'selectedColumns.member.11': 'albumCoverImageFull',
                'selectedColumns.member.12': 'purchased',
                'selectedColumns.member.13': 'status',
                'selectedColumns.member.14': 'primeStatus',
                'selectedColumns.member.15': 'sortAlbumName',
                'selectedColumns.member.16': 'sortTitle',
                'sortCriteriaList': None,
                'maxResults': self.G['maxResults'],
                'nextResultsToken': token[0],
                'Operation': 'searchLibrary',
                'caller': mediatype[1],
                'sortCriteriaList.member.1.sortColumn': mediatype[2],
                'sortCriteriaList.member.1.sortType': 'ASC',
                'ContentType': 'JSON',
                'customerInfo.customerId': self.credentials.CUSTOMERID,
                'customerInfo.deviceId': self.credentials.DEVICEID,
                'customerInfo.deviceType': self.credentials.DEVICETYPE
            }
            if self.getMode() == 'getPurSongs' or self.getMode() == 'getPurAlbums':
                data['searchCriteria.member.3.attributeName']  = 'purchased'
                data['searchCriteria.member.3.comparisonType'] = 'EQUALS'
                data['searchCriteria.member.3.attributeValue'] = 'true'
            #else:
                #filter = ['primeStatus','NOT_EQUALS','NOT_PRIME']

        elif mode == 'songs':
            data  = {
                'asins' : [ asin ],
                'features' : [ 'collectionLibraryAvailability','expandTracklist','playlistLibraryAvailability','trackLibraryAvailability','hasLyrics'],
                'requestedContent' : 'MUSIC_SUBSCRIPTION',
                'deviceId' : self.credentials.DEVICEID,
                'deviceType' : self.credentials.DEVICETYPE,
                'musicTerritory' : self.credentials.MUSICTERRITORY,
                'customerId' : self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'itemLookup':
            data = {
                'asins': asin, # [asin], is an array!!
                'features': mediatype, # is an array!!
                'requestedContent': 'MUSIC_SUBSCRIPTION',
                'deviceId': self.credentials.DEVICEID,
                'deviceType': self.credentials.DEVICETYPE,
                'musicTerritory': self.credentials.MUSICTERRITORY,
                'customerId': self.credentials.CUSTOMERID
            }
            data = json.JSONEncoder().encode(data)

        elif mode == 'itemLookup2ndRound':
            data = {
                'selectCriteriaList.member.1.attributeName':'status',
                'selectCriteriaList.member.1.comparisonType':'EQUALS',
                'selectCriteriaList.member.1.attributeValue':'AVAILABLE',
                'selectCriteriaList.member.2.attributeName':'trackStatus',
                'selectCriteriaList.member.2.comparisonType':'IS_NULL',
                'selectCriteriaList.member.2.attributeValue':'',
                'selectCriteriaList.member.3.attributeName':'albumAsin',
                'selectCriteriaList.member.3.comparisonType':'EQUALS',
                'selectCriteriaList.member.3.attributeValue':asin,
                'sortCriteriaList':'',
                'albumArtUrlsSizeList.member.1':'FULL',
                'albumArtUrlsSizeList.member.2':'LARGE',
                'albumArtUrlsRedirects':'false',
                'maxResults':   self.G['maxResults'],
                'nextResultsToken':0,
                'Operation':'selectTrackMetadata',
                'distinctOnly':'false',
                'countOnly':'false',
                'caller':'getServerData',
                'selectedColumns.member.1':'albumArtistName',
                'selectedColumns.member.2':'albumAsin',
                'selectedColumns.member.3':'albumName',
                'selectedColumns.member.4':'albumReleaseDate',
                'selectedColumns.member.5':'artistAsin',
                'selectedColumns.member.6':'artistName',
                'selectedColumns.member.7':'asin',
                'selectedColumns.member.8':'assetType',
                'selectedColumns.member.9':'creationDate',
                'selectedColumns.member.10':'discNum',
                'selectedColumns.member.11':'duration',
                'selectedColumns.member.12':'extension',
                'selectedColumns.member.13':'purchased',
                'selectedColumns.member.14':'lastUpdatedDate',
                'selectedColumns.member.15':'name',
                'selectedColumns.member.16':'objectId',
                'selectedColumns.member.17':'orderId',
                'selectedColumns.member.18':'primaryGenre',
                'selectedColumns.member.19':'purchaseDate',
                'selectedColumns.member.20':'size',
                'selectedColumns.member.21':'sortAlbumArtistName',
                'selectedColumns.member.22':'sortAlbumName',
                'selectedColumns.member.23':'sortArtistName',
                'selectedColumns.member.24':'sortTitle',
                'selectedColumns.member.25':'status',
                'selectedColumns.member.26':'title',
                'selectedColumns.member.27':'trackNum',
                'selectedColumns.member.28':'trackStatus',
                'selectedColumns.member.29':'payerId',
                'selectedColumns.member.30':'physicalOrderId',
                'selectedColumns.member.31':'primeStatus',
                'selectedColumns.member.32':'purchased',
                'selectedColumns.member.33':'uploaded',
                'selectedColumns.member.34':'instantImport',
                'selectedColumns.member.35':'parentalControls',
                'selectedColumns.member.36':'albumCoverImageFull',
                'selectedColumns.member.37':'albumCoverImageLarge',
                'selectedColumns.member.38':'albumCoverImageMedium',
                'selectedColumns.member.39':'albumCoverImageSmall',
                'selectedColumns.member.40':'isMusicSubscription',
                'sortCriteriaList.member.1.sortColumn':'discNum',
                'sortCriteriaList.member.1.sortType':'ASC',
                'sortCriteriaList.member.2.sortColumn':'trackNum',
                'sortCriteriaList.member.2.sortType':'ASC',
                'ContentType':'JSON',
                'customerInfo.customerId':  self.credentials.CUSTOMERID,
                'customerInfo.deviceId':    self.credentials.DEVICEID,
                'customerInfo.deviceType':  self.credentials.DEVICETYPE
            }

        elif mode == 'getStations':
            data = {
                'requestedContent': 'PRIME', #self.credentials.ACCESSTYPE,
                'lang':             self.credentials.LOCALE,
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE,
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID
            }
            data = json.dumps(data)

        elif mode == 'createQueue':
            data = {
                'identifier': asin,
                'identifierType':'STATION_KEY',
                'customerInfo': {
                    'deviceId':     self.credentials.DEVICEID,
                    'deviceType':   self.credentials.DEVICETYPE,
                    'musicTerritory':self.credentials.MUSICTERRITORY,
                    'customerId':   self.credentials.CUSTOMERID
                },
                'allowedParentalControls':{}
            }
            data = json.dumps(data)

        elif mode == 'getNextTracks':
            data = {
                'pageToken' : mediatype,
                'numberOfTracks':10,
                'customerInfo': {
                    'deviceId':     self.credentials.DEVICEID,
                    'deviceType':   self.credentials.DEVICETYPE,
                    'musicTerritory':self.credentials.MUSICTERRITORY,
                    'customerId':   self.credentials.CUSTOMERID
                },
                'allowedParentalControls':{}
            }
            data = json.dumps(data)

        elif mode == 'getGenrePlaylist':
            data = {
                'identifier': asin,
                'identifierType': 'STATION_KEY',
                'customerInfo': {
                    'deviceId':     self.credentials.DEVICEID,
                    'deviceType':   self.credentials.DEVICETYPE,
                    'musicTerritory':self.credentials.MUSICTERRITORY,
                    'customerId':   self.credentials.CUSTOMERID
                },
                'allowedParentalControls': {}
            }

        elif mode == 'getMetaData':
            data = {
                'trackIdList': asin,
                'attributeList': [
                    'albumCoverImageFull',
                    'albumCoverImageLarge',
                    'albumCoverImageMedium',
                    'albumCoverImageSmall',
                    'albumName',
                    'albumAsin',
                    'sortAlbumName',
                    'artistName',
                    'artistAsin',
                    'sortArtistName',
                    'sortAlbumArtistName',
                    'objectId',
                    'asin',
                    'title',
                    'status',
                    'primeStatus',
                    'isMusicSubscription',
                    'assetType',
                    'duration',
                    'discNum',
                    'trackNum',
                    'instantImport',
                    'purchased',
                    'uploaded',
                    'albumReleaseDate'
                ],
                'musicTerritory':   self.credentials.MUSICTERRITORY,
                'customerId':       self.credentials.CUSTOMERID,
                'deviceId':         self.credentials.DEVICEID,
                'deviceType':       self.credentials.DEVICETYPE
            }
            data = json.dumps(data)

        elif mode == 'getTrack':
            data = {
                'customerId' : self.credentials.CUSTOMERID,
                'deviceToken' : {
                    'deviceTypeId': self.credentials.DEVICETYPE,
                    'deviceId' :    self.credentials.DEVICEID
                },
                'bitRate' : 'HIGH',
                'appMetadata' : { 'https' : 'true' },
                'clientMetadata' : { 'clientId' : 'WebCP' },
                'contentId' : {
                    'identifier' : asin,
                    'identifierType' : mediatype #, # 'ASIN',
                    #'bitRate' : 'HIGH'
                }
            }
            data = json.dumps(data)

        elif mode == 'getTrackHLS':
            data = {
                'customerId' : self.credentials.CUSTOMERID,
                'deviceToken' : {
                    'deviceTypeId': self.credentials.DEVICETYPE,
                    'deviceId' :    self.credentials.DEVICEID
                },
                'bitRate' : 'HIGH',
                'appMetadata' : { 'https' : 'true' },
                'clientMetadata' : { 'clientId' : 'WebCP' },
                'contentId' : {
                    'identifier' : asin,
                    'identifierType' : mediatype #, # 'ASIN',
                },
                'bitRateList' : [ 'HIGH' ],
                'hlsVersion': 'V3'
            }
            data = json.dumps(data)

        elif mode == 'getTrackDash':
            mID = self.getMaestroID()
            data = {
                'customerId' :          self.credentials.CUSTOMERID,
                'deviceToken' : {
                    'deviceTypeId' :    self.credentials.DEVICETYPE,
                    'deviceId' :        self.credentials.DEVICEID
                },
                'contentIdList' : [{
                    'identifier' :      asin,
                    'identifierType' :  mediatype
                }],
                'bitrateTypeList' : [ 'HIGH' ],
                'musicDashVersionList' : [ 'V2' ],
                'appInfo' : {
                    'musicAgent': mID # 'Maestro/1.0 WebCP/1.0.202513.0 (9a46-5ad0-dmcp-8d19-ee5c6)'
                },
                'customerInfo' : {
                    'marketplaceId' :   self.credentials.MARKETPLACEID,
                    'customerId' :      self.credentials.CUSTOMERID,
                    'territoryId' :     self.credentials.MUSICTERRITORY,
                    'entitlementList' : [ 'HAWKFIRE' ]
                }
            }
            data = json.dumps(data)

        elif mode == 'getLicenseForPlaybackV2':
            mID = self.getMaestroID()
            # 'b{SSM}' base64NonURLencoded
            # 'B{SSM}' Base64URLencoded
            # 'R{SSM}' Raw format.
            data = {
                'DrmType':'WIDEVINE',
                #'licenseChallenge':'b{SSM}',
                'customerId':self.credentials.CUSTOMERID,
                'deviceToken':{
                    'deviceTypeId':self.credentials.DEVICETYPE,
                    'deviceId':self.credentials.DEVICEID
                },
                'appInfo':{
                    'musicAgent':mID
                }
            }
            if mediatype:
                data['licenseChallenge'] = mediatype
            else:
                data['licenseChallenge'] = 'b{SSM}'
            data = json.dumps(data)

        return data