#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, random, requests, json, datetime, time
import xbmc
from resources.lib.tools import AMtools
from resources.lib.logon import AMlogon
from resources.lib.api import AMapi

class AMcall( AMtools ):
#class AMcall( ):
    """
    Common class for the Amazon API calls
    """
    LIBRARY_ALBUM_ATTRIBUTES = ['albumName', 'albumArtistName', 'albumAsin', 'objectId',
                                'albumCoverImageFull', 'sortAlbumName', 'albumReleaseDate', 'primaryGenre']
    LIBRARY_TRACK_ATTRIBUTES = ['trackNum', 'discNum', 'duration', 'albumReleaseDate', 'primaryGenre',
                                'albumName', 'artistName', 'title', 'asin', 'objectId', 'albumAsin',
                                'artistAsin', 'purchased', 'status', 'primeStatus', 'albumCoverImageFull']
    signedIn = False

    def libraryData( self, attributes, filters, sort, order='ASC', paged=False ):
        """
        Request body of a Cirrus v3 library call
        :param array attributes:    item fields to return
        :param array filters:       filterList entries
        :param str sort:            attribute to sort by
        :param str order:           ASC or DESC
        :param bool paged:          pass on the page token of the current request
        """
        data = {
            'filterList':       filters,
            'attributeList':    attributes,
            'sortOrder':        {'sort': sort, 'order': order},
            'maxResults':       self.G['maxResults'],
            'musicTerritory':   self.credentials.MUSICTERRITORY,
            'customerId':       self.credentials.CUSTOMERID,
            'deviceId':         self.credentials.DEVICEID,
            'deviceType':       self.credentials.DEVICETYPE
        }
        token = self.G['addonArgs'].get('token', [None])[0] if paged else None
        if token:
            data['nextToken'] = token
        return json.dumps(data)

    @staticmethod
    def libraryFilter( name, value, comparison='EQUALS' ):
        return {'attributeName': name, 'comparisonType': comparison, 'attributeValue': value}

    # The player of the signed in web player (Vinyl) names itself; its id carries the first four letters.
    APP_NAME = 'GreenHornet_Web'
    APP_VERSION = '1.0.1468'

    def musicAgent( self ):
        """
        The music agent as the web player builds it: Vinyl/2.0 <app>/<version> (<random player id>)
        """
        def part( digits=4 ):
            return ''.join(random.choice('0123456789abcdef') for _ in range(digits))
        uid = '{}-{}-{}-{}-{}'.format( part(), part(), self.APP_NAME[:4], part(), part(5) )
        return 'Vinyl/2.0 {}/{} ({})'.format( self.APP_NAME, self.APP_VERSION, uid )

    def verifiedMediaPath( self ):
        """
        Whether Widevine can vouch for the player, which Amazon asks for before it licenses more than
        its lowest quality. The web player knows that a Linux desktop cannot and plays only the
        quality marked "LD" there; any other gets the license refused with VMP_VALIDATION_FAILED.
        Kodi has a Verified Media Path on Android only.
        """
        return bool(xbmc.getCondVisibility('System.Platform.Android')) and not self.vmpFailed()

    def licenseOutOfReach( self ):
        """
        Whether Amazon refused, within the last day, even the one quality a player without Verified
        Media Path may ask for. Seen with Kodi on Windows: Amazon expects Chrome for Windows to have
        such a path. Asking again only plays the unprotected start of song after song.
        """
        if xbmc.getCondVisibility('System.Platform.Android') or not self.vmpFailed():
            return False
        try:
            return time.time() - os.path.getmtime( self.dataFile(self.VMP_FLAG) ) < 24 * 60 * 60
        except OSError:
            return False

    def deviceToken( self ):
        """
        The device as the player of the web player names it to the music locator (dmls). \n
        Chrome on Linux has no Widevine Verified Media Path either and is handed a license without
        saying so. Only once Amazon refused a license for that reason does the device call itself
        unverified, as the web player does.
        """
        token = {
            'deviceTypeId' :    self.credentials.DEVICETYPE,
            'deviceId' :        self.credentials.DEVICEID
        }
        if self.vmpFailed():
            token['vmpValidationStatus'] = 'UNVERIFIED'
        return token

    def amzCall( self, amzUrl, mode, referer=None, asin=None, mediatype=None ):
        """
        Main function for the Amazon Call
        :param str amzUrl:  Endpoint ID
        :param str mode:    Request Addon Data ID
        :param str referer: no longer in use
        :param str asin:    Playlist-, Albums-, Song-, Artist-ID
        :param str/array mediatype: content depends on the caller function
        """
        # Kodi starts the add-on anew for every call, so the sign-in is read once per call.
        if not self.signedIn:
            self.credentials = self.load()
            self.signedIn = True

        amPath = AMapi.getAPI( amzUrl )

        url  = '{}/{}/api/{}'.format(
            self.musicURL.format( self.credentials.USERTLD ),
            self.credentials.REGION,
            amPath['path']
        )

        head = self.prepReqHeader(amPath['target'])
        data = self.prepReqData( mode, asin, mediatype )

        resp = requests.post( url=url, headers=head, data=data, cookies=self.credentials.COOKIE, timeout=self.TIMEOUT )
        # The tokens of the web player expire after some days, the sign-in cookies last longer.
        if resp.status_code == 401 and self.renewTokens():
            head = self.prepReqHeader(amPath['target'])
            data = self.prepReqData( mode, asin, mediatype )
            resp = requests.post( url=url, headers=head, data=data, cookies=self.credentials.COOKIE, timeout=self.TIMEOUT )
        if resp.status_code == 401 and 'Authorization' in head:
            # The web player also knows a sign-in by cookies alone. A refused access token
            # must not lock out a sign-in whose cookies are still good.
            del head['Authorization']
            resp = requests.post( url=url, headers=head, data=data, cookies=self.credentials.COOKIE, timeout=self.TIMEOUT )

        if self.G['logging']:
            self.log('url: ' + url)
            self.log('reason: ' + resp.reason + ', code: ' + str(resp.status_code))
            self.log(resp.text)

        if mode in ('getTrackDash', 'getTrackCoid'):
            return resp
        else:
            return resp.json()

    def renewTokens( self ):
        """
        Load fresh tokens from the web player configuration and store them with the sign-in
        """
        logon = AMlogon()
        logon.credentials = self.credentials
        # The configuration carries fresh CSRF tokens and an access token; without it the
        # web player's own way of renewing the access token is left.
        app_config = logon.fetchAppConfig()
        if app_config and app_config.get('accessToken'):
            logon._appConfig( app_config )
        else:
            token = logon.fetchAccessToken()
            if not token:
                return False
            self.credentials.ACCESSTOKEN = 'Bearer {}'.format(token)
        self.save( self.credentials )
        return True

    AUDIO_QUALITY = 'HIGH'

    # One function per request: what the add-on calls a request, and the function that fills it in.
    REQUESTS = {
        'recentlyaddedsongs':       'reqRecentlyAddedSongs',
        'getLibraryAlbums':         'reqLibrary',
        'itemLookup':               'reqItemLookup',
        'getTrackDash':             'reqTrackDash',
        'getTrackCoid':             'reqTrackCoid',
        'getLicenseForPlaybackV2':  'reqLicense'
    }

    def prepReqData( self, mode, asin=None, mediatype=None ):
        """
        Provide request data structure for Amazon API calls

        requestedContent:   FULL_CATALOG, KATANA, MUSIC_SUBSCRIPTION, PRIME_UPSELL_MS, ALL_STREAMABLE, PRIME
        features:           fullAlbumDetails, playlistLibraryAvailability, childParentOwnership, trackLibraryAvailability,
                            hasLyrics, expandTracklist, ownership, popularity, albumArtist, collectionLibraryAvailability
        types:              artist, track, album, similarArtist, playlist, station

        :param str mode:            Request Addon Data ID
        :param str asin:            Playlist-, Albums-, Song-, Artist-ID
        :param str/array mediatype: content depends on the caller function
        """
        data = getattr( self, self.REQUESTS[mode] )( mode, asin, mediatype )
        return data if isinstance(data, str) else json.dumps(data)

    def customer( self ):
        """
        Who asks and from where: the four fields nearly every request carries
        """
        return {
            'deviceId' :        self.credentials.DEVICEID,
            'deviceType' :      self.credentials.DEVICETYPE,
            'musicTerritory' :  self.credentials.MUSICTERRITORY,
            'customerId' :      self.credentials.CUSTOMERID
        }

    def reqRecentlyAddedSongs( self, mode, asin, mediatype ):
        return self.libraryData(
            self.LIBRARY_TRACK_ATTRIBUTES,
            [
                self.libraryFilter('status', 'AVAILABLE'),
                self.libraryFilter('creationDate',
                                   str(datetime.date.today() - datetime.timedelta(days=90)),
                                   'GREATER_THAN')
            ],
            'creationDate', 'DESC', paged=True
        )

    def reqLibrary( self, mode, asin, mediatype ):
        """Albums of the library: the albums bought, as the albums of the library come from GraphQL"""
        filters = [ self.libraryFilter('status', 'AVAILABLE'), self.libraryFilter('purchased', 'true') ]
        return self.libraryData( self.LIBRARY_ALBUM_ATTRIBUTES, filters, 'albumName', paged=True )

    def reqItemLookup( self, mode, asin, mediatype ):
        return dict({
            'asins': asin, # [asin], is an array!!
            'features': mediatype, # is an array!!
            'requestedContent': 'MUSIC_SUBSCRIPTION'
        }, **self.customer())

    def reqTrackDash( self, mode, asin, mediatype ):
        # As the player of the signed in web player asks for a manifest (getDashManifestsV2),
        # recorded with Chrome on Linux in November 2026.
        data = {
            'appInfo' : {
                'musicAgent': self.musicAgent()
            },
            'customerId' :          self.credentials.CUSTOMERID,
            'customerInfo' : {
                'marketplaceId' :   self.credentials.MARKETPLACEID,
                'territoryId' :     self.credentials.MUSICTERRITORY
            },
            'contentIdList' : [{
                'identifier' :      asin,
                'identifierType' :  mediatype
            }],
            'deviceToken' :         self.deviceToken()
        }
        if self.verifiedMediaPath():
            # The manifest version Kodi for Android is known to play, in the best quality.
            data['musicDashVersionList'] = [ 'V2' ]
            data['bitrateTypeList'] = [ self.AUDIO_QUALITY ]
        else:
            # Exactly what the web player asks for. Amazon refuses the license for every quality
            # of a V2 manifest without a Verified Media Path; of these manifests it licenses
            # the lowest quality, the one the web player then plays.
            data['musicDashVersionList'] = [ 'SIREN_KATANA' ]
            data['contentProtectionList'] = [ 'TRACK_PSSH' ]
            data['tryAsinSubstitution'] = False
        return data

    def reqTrackCoid( self, mode, asin, mediatype ):
        # As the web player asks for the streaming URL of a song the customer owns
        # (getStreamingURLs). Such a song comes as a plain file, without DRM.
        return {
            'contentIdList' : [{
                'identifier' :      asin,
                'identifierType' :  'COID'
            }],
            'bitRate' :             self.AUDIO_QUALITY,
            'deviceToken' :         self.deviceToken(),
            'appMetadata' : {
                'https' :           True,
                'appId' :           self.APP_NAME,
                'appVersion' :      self.APP_VERSION,
                'userAgent' :       self.userAgent
            },
            'clientMetadata' : {
                'clientId' :        'WebCP',
                'clientRequestId' : ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in range(19))
            },
            'customerId' :          self.credentials.CUSTOMERID
        }

    def reqLicense( self, mode, asin, mediatype ):
        return {
            'DrmType':'WIDEVINE',
            # placeholder inputstream adaptive replaces with the challenge
            'licenseChallenge':mediatype,
            'customerId':self.credentials.CUSTOMERID,
            'deviceToken':self.deviceToken(),
            'appInfo':{
                'musicAgent':self.musicAgent()
            },
            'Authorization':self.credentials.ACCESSTOKEN
        }
