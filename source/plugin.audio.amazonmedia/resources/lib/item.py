#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from urllib.parse import urlencode as urlencode
from urllib.parse import quote_plus as urlquoteplus
from resources.lib.tools import AMtools
import xbmcgui

class AMitem( AMtools ):
    """
    Main Item Class to assign request content to the Addon list item data structure
    """
    def setListItem( self, item, param ):
        """
        Entry point for Kodi list item creation, returns a item tupel
        :param array/json item:     Single data object from Amazon API call
        :param array/json param:    Addon mode parameter for the item
        """
        inf, met = self.setData( item, param )
        url, li  = self.setItem( inf, met )
        return (url, li, True)

    def setData( self, item, filter ):
        """
        Common Addon data structure for all items. Received data from Amazon API call will be assigned to the respective Addon data structure. \n
        Returns data structure 'info' and 'meta'.
        :param array/json item:     Single data object from Amazon API call
        :param array/json filter:   Addon mode parameter for the item
        """
        if 'update' in filter and filter['update']:
            info = filter['info']
            meta = filter['meta']
        else:
            info = {
                'tracknumber':  None,
                'discnumber':   None,
                'duration':     None,
                'year':         None,
                'genre':        None,
                'album':        None,
                'artist':       None,
                'title':        None,
                'rating':       None
            }
            meta = {
                'mode':         None,
                'asin':         None,
                'objectId':     None,
                'thumb':        None,
                'purchased':    False,
                'isPrime':      False,
                'isUnlimited':  False,
                'color':        '%s',
                'isPlayable':   True
            }
            meta['mode'] = filter['mode']
        # tracknumber : discnumber : duration : year : genre : album : artist : title : rating
        # if 'isAlbum' in filter and filter['isAlbum']:
        #     #filter['isAlbum'] = filter['isAlbum']
        #     if 'totalNumberOfTracks' in item:
        #         info['tracknumber'] = item['totalNumberOfTracks']
        # else:
        #     if 'trackNum' in item:
        #         info['tracknumber'] = item['trackNum']
        #     if 'trackCount' in item:
        #         info['tracknumber'] = item['trackCount']
        #     if 'totalTrackCount' in item:
        #         info['tracknumber'] = item['totalTrackCount']

        if 'trackNum' in item:              info['tracknumber'] = item['trackNum']
        elif 'trackCount' in item:          info['tracknumber'] = item['trackCount']
        elif 'totalTrackCount' in item:     info['tracknumber'] = item['totalTrackCount']
        elif 'totalNumberOfTracks' in item: info['tracknumber'] = item['totalNumberOfTracks']

        if 'discNum' in item:               info['discnumber'] = item['discNum']

        if 'duration' in item:              info['duration'] = item['duration']
        elif 'durationSeconds' in item:     info['duration'] = item['durationSeconds']

        if 'albumReleaseDate' in item:      info['year'] = item['albumReleaseDate'][:4]

        if 'primaryGenre' in item:          info['genre'] = item['primaryGenre']
        elif 'genreName' in item:           info['genre'] = item['genreName']
        elif 'productDetails' in item:      info['genre'] = item['productDetails']['primaryGenreName']

        if 'albumName' in item:             info['album'] = item['albumName']
        if 'description' in item:           info['album'] = item['description']
        if 'stationTitle' in item:          info['album'] = item['stationTitle']
        if 'album' in item:
            try:
                info['album'] = item['album']['name']
            except:
                info['album'] = item['album']['title']

        if 'isAlbumFolder' in filter and filter['isAlbumFolder'] == True:
            pass # this is only for folder views ...field 'artist' break Kodi visualization for albums
        else:
            if 'albumArtistName' in item:       info['artist'] = item['albumArtistName']
            if 'artist' in item:                info['artist'] = item['artist']['name']
            if 'artistName' in item:            info['artist'] = item['artistName']

        if 'stationTitle' in item:          info['title'] = item['stationTitle']
        if 'displayName' in item:           info['title'] = item['displayName']

        if 'isAlbum' in filter and filter['isAlbum']:
            if info['title'] == None and 'albumName' in item:
                info['title'] = item['albumName']
        else:
            if 'title' in item:
                info['title'] = item['title']
            if info['title'] == None and 'name' in item:
                info['title'] = item['name']

        if 'reviews' in item:               info['rating'] = item['reviews']['average']
        if 'rating' in item:                info['rating'] = item['rating']
        if 'averageOverallRating' in item:  info['rating'] = item['averageOverallRating']

        # mode : asin : objectId : thumb : purchased : isPrime : isUnlimited
        # order of 'playlistId' and 'asin' is important. Do not change the order -> reason: followed playlists
        if 'playlistId' in item:            meta['asin'] = item['playlistId']
        if 'asin' in item:                  meta['asin'] = item['asin']
        if 'seedId' in item:                meta['asin'] = item['seedId']
        if 'categoryId' in item:            meta['asin'] = item['categoryId']
        if 'stationKey' in item:            meta['asin'] = item['stationKey']
        if 'identifier' in item:            meta['asin'] = item['identifier']
        if 'isAlbum' in filter and filter['isAlbum']:
            if 'albumAsin' in item:
                meta['asin'] = item['albumAsin']

        if 'trackId' in item:               meta['objectId'] = item['trackId']
        if 'objectId' in item:              meta['objectId'] = item['objectId']
        if 'stationSeedId' in item:         meta['objectId'] = item['stationSeedId']

        # images - 'icon','thumb','fanart','poster','banner','landscape'
        if 'image' in item:                 meta['thumb'] = item['image']
        if 'imageFull' in item:             meta['thumb'] = item['imageFull']
        if 'albumCoverImageFull' in item:   meta['thumb'] = item['albumCoverImageFull']
        if 'albumArtImageUrl' in item:      meta['thumb'] = item['albumArtImageUrl']
        if 'stationImageUrl' in item and item['stationImageUrl'] is not None:
            meta['thumb'] = item['stationImageUrl']
        if 'foregroundImageUrl' in item and item['foregroundImageUrl'] is not None:
            meta['thumb'] = item['foregroundImageUrl']
        if 'artOriginal' in item:           meta['thumb'] = item['artOriginal']['URL']
        if 'artFull' in item:               meta['thumb'] = item['artFull']['URL']
        if 'artUrlMap' in item:             meta['thumb'] = item['artUrlMap']['FULL']
        if 'fourSquareImage' in item:       meta['thumb'] = item['fourSquareImage']['url']
        try:
            meta['thumb'] = item['album']['image']
        except:
            pass

        if (('purchased' in item and (item['purchased'] == True or item['purchased'] == 'true')) or
            ('isPurchased' in item and (item['isPurchased'] == True or item['isPurchased'] == 'true'))):
            meta['purchased'] = True

        if (('isPrime' in item and (item['isPrime'] == True or item['isPrime'] == 'true')) or
            ('primeStatus' in item and item['primeStatus'] == 'PRIME') or
            ('serviceTier' in item and item['serviceTier'] == 'PRIME') or
            ('playlistId' in item) or
            ('isStation' in filter and filter['isStation'] == True)):
            meta['isPrime'] = True

        if ('isMusicSubscription' in item and (item['isMusicSubscription'] == True or item['isMusicSubscription'] == 'true')):
            meta['isUnlimited'] = True

        if self.G['showcolentr']:
            if meta['purchased']:
                meta['color'] = '[COLOR gold]%s[/COLOR]'
            elif meta['isPrime'] or 'stationMapIds' in item:
                meta['color'] = '%s'
            elif meta['isUnlimited']:
                meta['color'] = '[COLOR blue]%s[/COLOR]'
            else:
                meta['color'] = '[COLOR red]%s[/COLOR]'

        if ((self.credentials.ACCESSTYPE == 'PRIME'     and not meta['isPrime'] and not meta['purchased']) or
            (self.credentials.ACCESSTYPE == 'UNLIMITED' and not meta['isPrime'] and not meta['purchased'] and not meta['isUnlimited'] )):
            meta['isPlayable'] = False
        else:
            meta['isPlayable'] = True

        if (self.credentials.ACCESSTYPE == 'UNLIMITED' and meta['isUnlimited']):
            meta['isPlayable'] = True
        
        if 'isList' in filter and filter['isList'] and info['tracknumber'] is not None:
            info['title'] =  '{}  ({} Hits'.format(info['title'],info['tracknumber'])
            if info['duration'] is not None:
                info['title'] =  '{} - {}'.format(info['title'],datetime.timedelta(seconds=info['duration']))
            info['title'] =  '{})'.format(info['title'])
            info['tracknumber'] = None

        #self.log(info)
        #self.log(meta)
        return ( info, meta )

    def setItem( self, inf, met ):
        """
        Provides a Kodi List Item, based on Addon data structures and Addon parameters
        :param array/json inf:  Addon data structure for Item information
        :param array/json met:  Addon data structure for Meta information
        """
        li = xbmcgui.ListItem(label=met['color'] % (inf['title']))
        if not met['thumb'] == None:
            li.setArt( self.setImage( met['thumb'] ) )
        li.setInfo( type='music', infoLabels=inf )
        if not met['isPlayable']: # workaround for unplayable items
            met['mode'] = '1234'
        url = self.setUrl( inf, met )
        li.setProperty( 'IsPlayable', str(met['isPlayable']) )
        # self.log(url)
        # self.log(inf)
        # self.log(met)
        return ( url, li )

    def setImage( self, img ):
        """
        Assign image to the Kodi list item property
        :param str img: link to the image
        """
        if self.G['showimages']:
            return ({'icon':img,'thumb':img,'fanart':img,'poster':img,'banner':img,'landscape':img})
        else:
            return ({'thumb':img}) # there is a bug in the listitems, after setting multiple arts, setInfo shows the Genre only

    def setUrl( self, inf, met ):
        """
        Generate item url based on common Addon data structures
        :param array/json inf:  Addon data structure for Item information
        :param array/json met:  Addon data structure for Meta information
        """
        url = {
            'mode':     met['mode'],
            'asin':     met['asin']
        }
        if met['objectId'] is not None:     url['objectId']     = met['objectId']
        if inf['title'] is not None:        url['title']        = inf['title']
        if inf['genre'] is not None:        url['genre']        = inf['genre']
        if inf['album'] is not None:        url['album']        = inf['album']
        if inf['artist'] is not None:       url['artist']       = inf['artist']
        if inf['year'] is not None:         url['year']         = inf['year']
        if inf['rating'] is not None:       url['rating']       = inf['rating']
        if inf['duration'] is not None:     url['duration']     = inf['duration']
        if inf['tracknumber'] is not None:  url['tracknumber']  = inf['tracknumber']
        #if met['thumb'] is not None:        url['art']          = met['thumb']

        return '{}?{}'.format(self.G['addonBaseUrl'],urlencode(url))

    def addPaginator( self, resultToken, resultLen ):
        """
        Generate paginator as an additional list item
        :param str resultToken: paginator token from the Amazon API
        :param array resultLen: received item array
        """
        if not resultToken == None and not len(resultLen) < self.G['maxResults']: # next page
            return True, self.setPaginator(resultToken)
        else:
            return False, ''

    def setPaginator( self, nextToken, query=None, asin=None ):
        """
        Provides a Kodi List Item as paginator, returns item tupel
        :param str nextToken:   page token
        :param str query:       request query
        :param str asin:        Album-, Artist-, Station-, Playlist-ID
        """
        li = xbmcgui.ListItem(label=self.getTranslation(30020))
        li.setProperty('IsPlayable', 'false')
        url = "{}?mode={}&token={}".format(self.G['addonBaseUrl'],str(self.getMode()),str(nextToken))
        if query:
            url += "&query={}".format( urlquoteplus( query.encode("utf8") ) )
        if asin:
            url += "&asin={}".format( urlquoteplus( asin.encode("utf8") ) )
        return (url, li, True)