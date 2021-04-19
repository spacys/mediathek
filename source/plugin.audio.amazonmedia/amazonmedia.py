#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# import urllib.parse as urlparse
from urllib.parse import quote as urlquote
from urllib.parse import quote_plus as urlquoteplus
from urllib.parse import urlencode as urlencode

import requests
# import mechanize
# import http.cookiejar as cookielib
# import sys
import re
import os
import json
# import shutil
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
# import xbmcaddon
import xbmcvfs
# from bs4 import BeautifulSoup
import datetime
#import base64
import urllib.parse as urlparse

from resources.lib.singleton import Singleton
from resources.lib.settings import Settings
from resources.lib.menu import MainMenu
from resources.lib.api import API
# from resources.lib.logon import Logon
from resources.lib.amzcall import AMZCall

class AmazonMedia(Singleton):
    def __init__(self):
        self.setVariables()
        if self.AMs.logging:
            self.AMs.log( 'Handle: ' + self.addonHandle.__str__() + '\n'
                        + 'Args  : ' + self.addonArgs.__str__() + '\n'
                        + 'Mode  : ' + self.AMs.addonMode.__str__())
    def setVariables(self):
        self.addonBaseUrl   = sys.argv[0]
        self.addonHandle    = int(sys.argv[1])
        self.addonArgs      = urlparse.parse_qs(sys.argv[2][1:])
        self.AMs    = Settings()
        self.AMm    = MainMenu(self.AMs)
        # self.AMl    = Logon(self.AMs)
        self.AMapi  = API()
        #self.AMc    = AMZCall(self.AMs,self.AMl,self.addonArgs)
        self.AMc    = AMZCall(self.AMs, self.addonArgs)
        self.AMs.addonMode  = self.addonArgs.get('mode', None)
    def reqDispatch(self):
        # reset addon
        if self.AMs.addonMode is not None and self.AMs.addonMode[0] == 'resetAddon':
            self.AMs.resetAddon()
            xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self.AMs.translation(30071)))
            return

        if self.AMs.addonMode is None:
            mode = None
        else:
            mode = self.AMs.addonMode[0]

        if mode is None:
            self.createList(self.AMm.menuHome())
            return
        # elif mode == 'menuPlaylists':
        #     self.createList(self.AMm.menuPlaylists(),True)
        # elif mode == 'menuAlbums':
        #     self.createList(self.AMm.menuAlbums(),True)
        # elif mode == 'menuSongs':
        #     self.createList(self.AMm.menuSongs(),True)
        # elif mode == 'menuStations':
        #     self.createList(self.AMm.menuStations(),True)
        # elif mode == 'menuArtists':
        #     self.createList(self.AMm.menuArtists(),True)
        elif mode in ['menuPlaylists','menuAlbums','menuSongs','menuStations','menuArtists']:
            exec('self.createList(self.AMm.{}(),True)'.format(mode))
            return
        elif mode == 'menuSoccer':
            self.createList(self.AMm.menuSoccer())
            return

        if self.AMs.logging: self.AMs.log('Access: {}'.format(self.AMs.access))
        if not self.AMs.access:
            if not self.AMc.doLogon():
               xbmc.executebuiltin('Notification("Error:", {}, 5000, )'.format(self.AMs.translation(30070)))
               return

        if mode == 'searchPlayLists':
            self.searchItems(['playlists','catalog_playlist'],30013)
        elif mode in ['search1PlayLists','search2PlayLists','search3PlayLists']:
            exec('self.searchItems([\'playlists\',\'catalog_playlist\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchAlbums':
            self.searchItems(['albums','catalog_album'],30010)
        elif mode in ['search1Albums','search2Albums','search3Albums']:
            exec('self.searchItems([\'albums\',\'catalog_album\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchSongs':
            self.searchItems(['tracks','catalog_track'],30011)
        elif mode in ['search1Songs','search2Songs','search3Songs']:
            exec('self.searchItems([\'tracks\',\'catalog_track\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchArtist':
            self.searchItems(['artists','catalog_artist'],30014)
        elif mode in ['search1Artists','search2Artists','search3Artists']:
            exec('self.searchItems([\'artists\',\'catalog_artist\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchStations':
            self.searchItems(['stations','catalog_station'],30016)
        elif mode in ['search1Stations','search2Stations','search3Stations']:
            exec('self.searchItems([\'stations\',\'catalog_station\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'getArtistDetails':
            asin = self.addonArgs.get('asin', [None])
            self.getArtistDetails(asin[0])

        elif mode == 'getRecentlyPlayed':
            self.getRecentlyPlayed('PLAYED')
        elif mode == 'getRecentlyAddedSongs':
            self.getRecentlyAddedSongs()

        elif mode == 'getPopularPlayLists':
            self.getPlayLists('popularity-rank')
        elif mode == 'getNewPlayLists':
            self.getPlayLists('newly-released')
        elif mode == 'getFollowedPlayLists':
            self.getFollowedPlayLists()
        elif mode == 'getOwnedPlaylists':
            self.getOwnedPlaylists()
        elif mode == 'getPlaylistsByIdV2':
            asin = self.addonArgs.get('asin', [None])
            self.getPlaylistsByIdV2(asin[0])

        elif mode == 'getRecomPlayLists':
            self.getRecommendations('playlists','mp3-prime-browse-carousels_playlistStrategy')
        elif mode == 'getRecomAlbums':
            self.getRecommendations('albums','mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy')
        elif mode == 'getRecomStations':
            self.getRecommendations('stations','mp3-prime-browse-carousels_mp3ArtistStationStrategy')

        elif mode == 'getNewRecom':
            self.getNewRecommendations()
        elif mode == 'getNewRecomDetails':
            asin = self.addonArgs.get('target', [None])
            self.getNewRecomDetails(asin[0])
        # get own music, differentiate betwenn purchased and own lib
        # param: searchReturnType , caller, sortCriteriaList.member.1.sortColumn
        elif mode in ['getPurAlbums','getAllAlbums']:
            self.getPurchased(['ALBUMS','getAllDataByMetaType','sortAlbumName'],'albums')
        elif mode in ['getAllSongs','getPurSongs']:
            self.getPurchased(['TRACKS','getServerSongs','sortTitle'],'songs')
        # get amazon stations
        elif mode in ['getStations','getAllArtistsStations','getGenres','getGenres2']:
            self.getStations(mode.replace('get','').lower())
        elif mode in ['getGenrePlaylist','createQueue']:
            asin = self.addonArgs.get('asin', None)
            exec('self.{}(asin[0])'.format(mode))
        # get song lists
        elif mode == 'lookup':
            asin = self.addonArgs.get('asin', None)
            self.lookup(asin)
        # play the song
        elif mode == 'getTrack':
            asin = self.addonArgs.get('asin', [None])[0]
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getTrack(asin,objectId)
        # Amazon Soccer Live
        elif mode in ['soccerBUND','soccerBUND2','soccerCHAMP','soccerDFBPOKAL','soccerSUPR']:
            self.getSoccerFilter(mode.replace('soccer',''))
        elif mode == 'getSoccerLive':
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'LIVE')
        elif mode == 'getSoccerOnDemand':
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'ONDEMAND')
    def createList(self,data,dynentry=False,soccer=False):
        itemlist = []
        url = None
        for item in data:
            # self.AMs.log(item)
            isFolder = True
            if dynentry and 'search' in item and self.AMs.getSetting(item['search']) == '':
                continue
            # if soccer:
            if soccer or ('special' in item and item['special'] == 'newrecom'):
                title = item['txt']
            else:
                title = self.AMs.translation(item['txt'])
            if dynentry and 'search' in item:
                title += self.AMs.getSetting(item['search'])
            li = xbmcgui.ListItem(label=title)
            li.setInfo(type="music", infoLabels={"title": title})
            if 'img' in item:
                if 'http' in item['img']:
                    url = item['img']
                else:
                    url = '{}/resources/images/{}'.format(self.AMs.addonFolder, self.AMs.getSetting(item['img']) )
                li.setArt({'icon':url,'thumb':url,'fanart':url,'poster':url,'banner':url,'landscape':url})
            url = '{}?mode={}'.format(self.addonBaseUrl,str(item['fct']))
            if soccer:
                url+="&objectId={}".format(str(item['target']))
                if item['playable']:
                    pl = 'true'
                else:
                    pl = 'false'
                li.setProperty('IsPlayable', pl)
                isFolder = False
            if 'special' in item and item['special'] == 'newrecom' and 'target' in item:
                url+='&target={}'.format(str(item['target']))
            itemlist.append((url, li, isFolder))
        self.finalizeContent(itemlist,'albums')
    # get music information
    def lookup(self,asin):
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        data = self.AMc.amzCall( self.AMapi.lookup,'itemLookup',None,asin,mediatype)
        sel = ''
        if   len(data['albumList']) > 0:
            sel = 'albumList'
        elif len(data['artistList']) > 0:
            sel = 'artistList'
        elif len(data['playlistList']) > 0:
            sel = 'playlistList'
        elif len(data['trackList']) > 0:
            sel = 'trackList'
        else:
            data = self.AMc.amzCall(self.AMapi.cirrus, 'itemLookup2ndRound', '/my/albums', [asin], None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
            sel = 'trackInfoList'
        self.setAddonContent(sel,data[sel],'songs')
    def getRecentlyPlayed(self,mediatype):
        items = self.AMc.amzCall(self.AMapi.GetRecentTrackActivity,'recentlyplayed',None,None,mediatype)['recentActivityMap']['PLAYED']
        self.setAddonContent('recentlyplayed',items,'songs')
    def getRecentlyAddedSongs(self):
        items = self.AMc.amzCall(self.AMapi.cirrus,'recentlyaddedsongs',None,None,None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
        self.setAddonContent('recentlyaddedsongs',items,'songs')
    def getPlayLists(self,mediatype):
        items = self.AMc.amzCall(self.AMapi.getTopMusicEntities,'playlist',None,None,mediatype)
        # data structure is similar to lookup
        self.setAddonContent('playlists',items,'albums')
    def getFollowedPlayLists(self):
        items = self.AMc.amzCall(self.AMapi.getFollowedPlaylistsInLibrary,'followedplaylists',None,None,None)
        self.setAddonContent('followedplaylists',items,'albums')
    def getOwnedPlaylists(self):
        items = self.AMc.amzCall(self.AMapi.getOwnedPlaylistsInLibrary,'getownedplaylists',None,None,None)
        self.setAddonContent('ownedplaylists',items,'albums')
    def getPlaylistsByIdV2(self,asin):
        items = self.AMc.amzCall(self.AMapi.getPlaylistsByIdV2,'getplaylistsbyid',None,asin,None)
        self.setAddonContent('getplaylistsbyid',items,'songs')
    def getStations(self,mediatype):
        items = self.AMc.amzCall(self.AMapi.getStationSections,'getStations','/stations')
        self.setAddonContent(mediatype,items,'albums')
    def getGenrePlaylist(self,asin):
        items = self.AMc.amzCall(self.AMapi.createQueue,'getGenrePlaylist',None,asin)
        self.setAddonContent('genreplaylist',items,'albums')
    def getRecommendations(self,mode,mediatype):
        resp = self.AMc.amzCall(self.AMapi.getBrowseRecommendations,'recommendations',None,None,mediatype)
        sel = ''
        if   resp['recommendations'][0]['recommendationType'] == 'PLAYLIST':
            sel = 'recplaylists'
        elif resp['recommendations'][0]['recommendationType'] == 'ALBUM':
            sel = 'recalbums'
        elif resp['recommendations'][0]['recommendationType'] == 'STATION':
            sel = 'recstations'
        self.setAddonContent(sel,resp['recommendations'][0],'albums')
    def getNewRecommendations(self):
        menuEntries = []
        resp = self.AMc.amzCall(self.AMapi.getHome,'new_recommendations')
        for item in resp['blocks']:
            if (('ButtonGrid' in item['__type']) or ('Barker' in item['__type'])):
                continue
            menuEntries.append({
                'txt':      item['title'],
                'fct':      'getNewRecomDetails',
                'special':  'newrecom',
                'target':   urlquote(item['title'].encode('utf8')),
                'img':      'newrecom.jpg'
            })
        self.createList(menuEntries)
    def getNewRecomDetails(self,target):
        menuEntries = []
        items = None
        resp = self.AMc.amzCall(self.AMapi.getHome,'new_recommendations')
        for item in resp['blocks']:
            if (('ButtonGrid' in item['__type']) or ('Barker' in item['__type'])): # ignore button fields
                continue
            if target in item['title']: # find the category
                items = item['blocks']
                break
        if items == None: # in case of empty list
            return
        self.setAddonContent('newrecom',items,'albums')
    def getPurchased(self,mode,ctype):
        resp = self.AMc.amzCall(self.AMapi.cirrus,'getPurchased',None,None,mode)
        items = resp['searchLibraryResponse']['searchLibraryResult']
        if ctype == 'songs':
            mode = 'purchasedsongs'
        elif ctype == 'albums':
            mode = 'purchasedalbums'
        self.setAddonContent(mode,items,ctype)
    def searchItems(self,mode=None,txt=None,query=None):
        if query == None:
            if self.addonArgs.get('token', False):
                query = self.addonArgs.get('query', [''])[0]
            else:
                query = self.AMs.getUserInput(self.AMs.translation(txt), '')
                if not query:
                    return
        resp = self.AMc.amzCall( self.AMapi.search , 'searchItems' , '/search' , query,mode )
        items = resp['results'][0]
        if   mode[0] == 'albums':
            if not txt == None:
                self.AMs.setSearch('albums',query)
            self.setAddonContent('searchitems',items,'albums','albums',query)
        elif mode[0] == 'tracks':
            if not txt == None:
                self.AMs.setSearch('tracks',query)
            self.setAddonContent('searchitems',items,'songs','tracks',query)
        elif mode[0] == 'playlists':
            if not txt == None:
                self.AMs.setSearch('playlists',query)
            self.setAddonContent('searchplaylists',items,'albums',None,query)
        elif mode[0] == 'artists':
            if not txt == None:
                self.AMs.setSearch('artists',query)
            self.setAddonContent('searchartists',items,'songs',None,query)
        elif mode[0] == 'stations':
            if not txt == None:
                self.AMs.setSearch('stations',query)
            self.setAddonContent('searchstations',items,'albums',None,query)
    def getArtistDetails(self,asin):
        resp = self.AMc.amzCall(self.AMapi.artistDetailsMetadata,'getArtistDetails',None,asin,None)
        items = resp
        self.setAddonContent('artistdetails',items,'albums',None,asin)
    def createQueue(self,asin):
        resp = self.AMc.amzCall(self.AMapi.createQueue,'createQueue',None,asin,None)
        token = resp['queue']['pageToken']
        tracklist = resp['trackMetadataList']
        i = 1
        while token: # 5 songs per loop
            resp = self.AMc.amzCall(self.AMapi.QueueGetNextTracks,'getNextTracks',None,asin,token)
            token = resp['nextPageToken']
            for item in resp['trackMetadataList']:
                tracklist.append(item)
            if i == 10:
                break
            i += 1
        self.setAddonContent('stationList',tracklist,'songs')
    # kodi visualization
    def getMeta(self,resp,filter):
        meta = []
        for item in resp:
            if len(filter) == 1:
                meta.append(item[filter['array1']])
            else:
                meta.append(item[filter['array1']][filter['array2']])
        seen = set()
        uniq = [x for x in meta if x not in seen and not seen.add(x)] # make it unique
        return self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,uniq,['fullAlbumDetails'])#['albumList']
    def getMetaTracks(self,filter):
        return self.AMc.amzCall(self.AMapi.V3getTracks,'getMetaTracks',None,filter,None)
    def setData(self,item,filter):
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

        if 'trackNum' in item:
            info['tracknumber'] = item['trackNum']
        elif 'trackCount' in item:
            info['tracknumber'] = item['trackCount']
        elif 'totalTrackCount' in item:
            info['tracknumber'] = item['totalTrackCount']
        elif 'totalNumberOfTracks' in item:
            info['tracknumber'] = item['totalNumberOfTracks']

        if 'discNum' in item:           info['discnumber'] = item['discNum']

        if 'duration' in item:
            info['duration'] = item['duration']
        elif 'durationSeconds' in item:
            info['duration'] = item['durationSeconds']

        if 'albumReleaseDate' in item:  info['year'] = item['albumReleaseDate'][:4]

        if 'primaryGenre' in item:
            info['genre'] = item['primaryGenre']
        elif 'genreName' in item:
            info['genre'] = item['genreName']
        elif 'productDetails' in item:
            info['genre'] = item['productDetails']['primaryGenreName']

        if 'albumName' in item:             info['album'] = item['albumName']
        if 'description' in item:           info['album'] = item['description']
        if 'stationTitle' in item:          info['album'] = item['stationTitle']
        if 'album' in item:
            try:
                info['album'] = item['album']['name']
            except:
                info['album'] = item['album']['title']

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

        if self.AMs.showcolentr:
            if meta['purchased']:
                meta['color'] = '[COLOR gold]%s[/COLOR]'
            elif meta['isPrime'] or 'stationMapIds' in item:
                meta['color'] = '%s'
            elif meta['isUnlimited']:
                meta['color'] = '[COLOR blue]%s[/COLOR]'
            else:
                meta['color'] = '[COLOR red]%s[/COLOR]'

        if ((self.AMs.accessType == 'PRIME'     and not meta['isPrime'] and not meta['purchased']) or
            (self.AMs.accessType == 'UNLIMITED' and not meta['isPrime'] and not meta['purchased'] and not meta['isUnlimited'] )):
            meta['isPlayable'] = False
        else:
            meta['isPlayable'] = True

        if (self.AMs.accessType == 'UNLIMITED' and meta['isUnlimited']):
            meta['isPlayable'] = True
        
        #self.AMs.log('vor: ' + str(info['tracknumber']))
        if 'isList' in filter and filter['isList'] and info['tracknumber'] is not None:
            info['title'] =  '{}  ({} Hits'.format(info['title'],info['tracknumber'])
            if info['duration'] is not None:
                info['title'] =  '{} - {}'.format(info['title'],datetime.timedelta(seconds=info['duration']))
            info['title'] =  '{})'.format(info['title'])
            info['tracknumber'] = None
        #self.AMs.log('nach: ' + str(info['tracknumber']))
        #self.AMs.log(info)
        #self.AMs.log(meta)
        return (info,meta)
    def setItem(self,inf,met):
        li = xbmcgui.ListItem(label=met['color'] % (inf['title']))
        if not met['thumb'] == None:
            li.setArt(self.setImage(met['thumb']))
        li.setInfo(type="music", infoLabels=inf)
        if not met['isPlayable']: # workaround for unplayable items
            met['mode'] = '1234'
        url = self.setUrl(inf,met)
        li.setProperty('IsPlayable', str(met['isPlayable']))
        # self.AMs.log(url)
        # self.AMs.log(inf)
        # self.AMs.log(met)
        return (url,li)
    def setListItem(self,itemList,item,param):
        inf, met = self.setData(item,param)
        url, li  = self.setItem(inf,met)
        itemList.append((url, li, True))
        return itemList
    def setImage(self,img):
        if self.AMs.showimages:
            return ({'icon':img,'thumb':img,'fanart':img,'poster':img,'banner':img,'landscape':img})
        else:
            return ({'thumb':img}) # there is a bug in the listitems, after setting multiple arts, setInfo shows the Genre only
    def addPaginator(self,itemList,resultToken,resultLen):
        if not resultToken == None and not len(resultLen) < self.AMs.maxResults: # next page
            itemList.append(self.setPaginator(resultToken))
        return itemList
    def setPaginator(self,nextToken,query=None,asin=None):
        li = xbmcgui.ListItem(label=self.AMs.translation(30020))
        li.setProperty('IsPlayable', 'false')
        url = "{}?mode={}&token={}".format(self.addonBaseUrl,str(self.AMs.addonMode[0]),str(nextToken))
        if query:
            url += "&query={}".format(urlquoteplus(query.encode("utf8")))
        if asin:
            url += "&asin={}".format(urlquoteplus(asin.encode("utf8")))
        return (url, li, True)
    def setUrl(self,inf,met):
        url = {
            'mode':     met['mode'],
            'asin':     met['asin']
        }
        if met['objectId'] is not None:
            url['objectId'] = met['objectId']
        return '{}?{}'.format(self.addonBaseUrl,urlencode(url))
    def setAddonContent(self,mode,param,ctype,stype=None,query=None):
        itemlist = []
        meta = []
        mod = None
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        if   mode == 'albumList' or mode == 'playlistList':
            meta = self.getMetaTracks(param[0]['asin'])['resultList']
            for item in param[0]['tracks']:
                inf, met = self.setData(item,{'mode':'getTrack'})
                for i in meta:
                    if item['asin'] == i['metadata']['asin']:
                        inf, met = self.setData(i['metadata'],{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                inf['album'] = param[0]['title']
                inf['rating'] = param[0]['reviews']['average']
                met['thumb'] = param[0]['image']
                met['album'] = param[0]['title']
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'artistList':      # no content at the moment
            self.AMs.log('artistList')
        elif mode == 'trackInfoList':           # track info list
            for item in param:
                meta.append(item['metadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'stationList':             # station playlist
            for item in param:
                meta.append(item['identifier'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self.setData(item,{'mode':'getTrack'})
                for i in meta:
                    if item['identifier'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                itemlist.append((url, li, False))
        elif mode == 'playlists':               # playlists
            for item in param['playlistList']:
                self.setListItem(itemlist,item,{'mode':'lookup','isList':True})
            self.addPaginator(itemlist,param['nextTokenMap']['playlist'],param['playlistList'])
        elif mode == 'followedplaylists':       # followed playlists
            for item in param['playlists']:
                self.setListItem(itemlist,item,{'mode':'lookup','isList':True})
        elif mode == 'ownedplaylists':          # owned playlists
            for item in param['playlists']:
                inf, met = self.setData(item,{'mode':'getPlaylistsByIdV2','isList':True})
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, True))
        elif mode == 'getplaylistsbyid':        # playlists by Id
            for item in param['playlists']:
                for track in item['tracks']:
                    meta.append(track['metadata']['requestedMetadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param['playlists']:
                for track in item['tracks']:
                    inf, met = self.setData(track['metadata']['requestedMetadata'],{'mode':'getTrack'})
                    for i in meta:
                        if track['metadata']['requestedMetadata']['asin'] == i['asin']:
                            inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                        else:
                            continue
                    url, li  = self.setItem(inf,met)
                    if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                        continue
                    itemlist.append((url, li, False))
        elif mode == 'recplaylists':            # recommended playlists
            for item in param['playlists']:
                self.setListItem(itemlist,item,{'mode':'lookup','isList':True})
            self.addPaginator(itemlist,param['nextResultsToken'],param['playlists'])
        elif mode == 'recalbums':               # recommended albums
            for item in param['albums']:
                self.setListItem(itemlist,item,{'mode':'lookup','isAlbum':True,'isList':True})
            self.addPaginator(itemlist,param['nextResultsToken'],param['albums'])
        elif mode == 'recstations':             # recommended stations
            for item in param['stations']:
                self.setListItem(itemlist,item,{'mode':'createQueue'})
            self.addPaginator(itemlist,param['nextResultsToken'],param['stations'])
        elif mode == 'recentlyplayed':          # recently played songs
            for item in param['recentTrackList']:
                inf, met = self.setData(item,{'mode':'getTrack'})
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextToken'],param['recentTrackList'])
        elif mode == 'newrecom':                # new recommendations
            for item in param:
                i = item['hint']['__type']
                #self.AMs.log(i)
                if (('AlbumHint'    in i) or
                    ('PlaylistHint' in i) or
                    ('ArtistHint'   in i)):
                    ctype   = 'albums'
                    mod     = {'mode':'lookup'}
                    fold    = True
                elif 'StationHint' in i:
                    ctype   = 'albums'
                    mod     = {'mode':'createQueue'}
                    fold    = True
                elif 'TrackHint' in i:
                    ctype   = 'songs'
                    mod    = {'mode':'getTrack'}
                    fold    = False
                inf, met = self.setData(item['hint'],mod)
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
        elif mode == 'recentlyaddedsongs':      # recently added songs
            for item in param['trackInfoList']:
                meta.append(item['metadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param['trackInfoList']:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextResultsToken'],param['trackInfoList'])
        elif mode == 'stations':                # (all) stations
            items = param['categories'].get('allStations')['stationMapIds']
            for item in items:
                self.setListItem(itemlist,param['stations'].get(item),{'mode':'createQueue'})
        elif mode == 'allartistsstations':      # (all artists) stations
            items = param['stations']
            for item in items:
                i = param['stations'].get(item)
                if not i['seedType'] == 'ARTIST':
                    continue
                self.setListItem(itemlist,i,{'mode':'createQueue'})
        elif mode == 'genres':                  # genre 1st level
            for sec in param['sections']:
                if sec['sectionId'] == 'genres':
                    for item in sec['categoryMapIds']:
                        self.setListItem(itemlist,param['categories'].get(item),{'mode':'getGenres2','isStation':True})
                else:
                    continue
        elif mode == 'genres2':                 # genres 2nd level
            asin = self.addonArgs.get('asin', None)[0]
            items = param['categories'].get(asin)['stationMapIds']
            for item in items:
                self.setListItem(itemlist,param['stations'].get(item),{'mode':'createQueue'})
        elif mode == 'purchasedalbums':         # purchased and owned albums
            for item in param['searchReturnItemList']:
                meta.append(item['metadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,['fullAlbumDetails'])['albumList']
            for item in param['searchReturnItemList']:
                inf, met = self.setData(item['metadata'],{'mode':'lookup','isAlbum':True})
                for i in meta:
                    if item['metadata']['albumAsin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'isAlbum':True,'update':True,'isList':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                itemlist.append((url, li, True))
            self.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])
        elif mode == 'purchasedsongs':          # purchased and owned songs
            meta = self.getMeta(param['searchReturnItemList'],{'array1':'metadata','array2':'albumAsin'})['albumList']
            for item in param['searchReturnItemList']:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])
        elif mode == 'searchitems':             # search items (songs / albums)
            for item in param['hits']:
                if stype == 'albums':
                    mod  = {'mode':'lookup','isList':True}
                    fold = True
                elif stype == 'tracks' or stype == 'artists':
                    mod  = {'mode':'getTrack'}
                    fold = False
                inf, met = self.setData(item['document'],mod)
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchplaylists':         # search playlists
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'lookup','isList':True})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchartists':           # search artists
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'getArtistDetails'})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchstations':          # search stations
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'createQueue','query':query})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'artistdetails':           # artitist details (albums)
            for item in param['albumList']:
                self.setListItem(itemlist,item,{'mode':'lookup'})
            try:
                if len(param['albumList']) == self.AMs.maxResults:
                    itemlist.append(self.setPaginator(param['nextTokenMap']['album'],None,query))
                    itemlist.append((url, li, True))
            except:
                pass
        self.finalizeContent(itemlist,ctype)
        xbmc.sleep(100)
    def finalizeContent(self,itemlist,ctype):
        xbmcplugin.addDirectoryItems(self.addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(self.addonHandle, ctype)
        xbmcplugin.endOfDirectory(self.addonHandle)
    # play music
    def getTrack(self,asin,objectId):
        song    = self.tryGetStream(asin,objectId)
        stream  = {'ia':False, 'lic':False}
        if song == None:
            manifest = self.tryGetStreamHLS(asin,objectId)
            if manifest:
                song = self.writeSongFile(manifest,'m3u8')
        if song == None:
            manifest = self.tryGetStreamDash(asin,objectId)
            if manifest:
                song = self.writeSongFile(manifest,'mpd')
                ''' proxy try - START '''
                song = 'http://{}/mpd/{}'.format(self.AMs.getSetting('proxy'),'song.mpd')
                ''' proxy try - END '''
                stream['ia']  = True
                stream['lic'] = True
        if song == None:
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.AMs.translation(30073),' ',self.AMs.translation(30074)))
            return False
        self.finalizeItem(song,stream['ia'],stream['lic'])        
    def tryGetStream(self,asin,objectId):
        if objectId == None:
            resp = self.AMc.amzCall(self.AMapi.stream,'getTrack',None,asin,'ASIN')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['statusCode'] == 'MAX_CONCURRENCY_REACHED':
                xbmc.PlayList(0).clear()
                xbmc.Player().stop()
                xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.AMs.translation(30073),' ',self.AMs.translation(30075)))
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        else:
            resp = self.AMc.amzCall(self.AMapi.stream,'getTrack',None,objectId,'COID')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['contentResponse']['statusCode'] == 'CONTENT_NOT_ELIGIBLE' or obj['contentResponse']['statusCode'] == 'BAD_REQUEST':
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        return song
    def tryGetStreamHLS(self,asin,objectId):
        resp = self.AMc.amzCall(self.AMapi.streamHLS,'getTrackHLS',None,asin,'ASIN')
        return re.compile('manifest":"(.+?)"',re.DOTALL).findall(resp.text)
    def tryGetStreamDash(self,asin,objectId):
        resp = self.AMc.amzCall(self.AMapi.streamDash,'getTrackDash',None,asin,'ASIN')
        return json.loads(resp.text)['contentResponseList'][0]['manifest']
    def finalizeItem(self,song,ia=False,lic=False):
        li = xbmcgui.ListItem(path=song)
        if ia:
            li.setMimeType('application/xml+dash')
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.stream_headers', 'user-agent={}'.format(self.AMs.userAgent))
            # for live soccer only - test start
            li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            # for live soccer only - test end
            if lic:
                li.setProperty('inputstream.adaptive.license_key', self.getLicenseKey() )
            li.setProperty('isFolder', 'false')
            li.setProperty('IsPlayable', 'true')
            li.setInfo('video', {})
        li.setInfo('audio', {'codec': 'aac'})
        li.addStreamInfo('audio', {'codec': 'aac'})
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.addonHandle, True, listitem=li)
    def writeSongFile(self,manifest,ftype='m3u8'):
        song = '{}{}song.{}'.format(self.AMs.addonUDatFo,os.sep,ftype)
        m3u_string = ''
        temp_file = xbmcvfs.File(song, 'w')
        if ftype == 'm3u8':
            m3u_string = manifest[0]
        if ftype == 'mpd':
            m3u_string = manifest
            song = song.replace("\\","/") # windows fix that inputstream can work properly
        m3u_string = m3u_string.replace("\\n", os.linesep)
        temp_file.write(m3u_string)
        temp_file.close()
        return song
    def getLicenseKey(self):
        amzUrl = self.AMapi.LicenseForPlaybackV2
        url = '{}/{}/api/{}'.format(self.AMs.url, self.AMs.region, amzUrl['path'])
        head = self.AMs.prepReqHeader(amzUrl['target'])

        cookiedict = {}
        for cookie in self.AMs.cj:
            cookiedict[cookie.name] = cookie.value

        cj_str = ';'.join(['%s=%s' % (k, v) for k, v in cookiedict.items()])

        head['Cookie'] = cj_str
        licHeader = '&'.join(['%s=%s' % (k, urlquote(v, safe='')) for k, v in head.items()])
        licBody = self.AMc.prepReqData('getLicenseForPlaybackV2')
        # licURL expected (req / header / body / response)
        return '{}|{}|{}|JBlicense'.format(url,licHeader,licBody)
    def getSoccerFilter(self,target=None): # 'BUND', 'BUND2', 'CHAMP', 'DFBPOKAL', 'SUPR'
        menuEntries = []
        resp = self.AMc.amzCall(self.AMapi.GetSoccerMain,'getSoccerMain',None,None,target)
        idx = resp['blocks'][0]['positionSelector']['currentPosition']['blockIndex'] # current matchday
        if idx == -1: # if no entries are available
            menuEntries.append({'txt':'Empty List','fct':None,'target':None,'img':self.AMs.getSetting('img_soccer'),'playable':False})
            self.createList(menuEntries,False,True)
            return
        param = resp['blocks'][0]['positionSelector']['positionOptions']
        idx1 = 0
        for item in param: # find last matchday based on current matchday
            if item['blockIndex'] < idx:
                idx1+=1
                continue
            break
        idx1-= 1
        if idx1 < 0:
            idx1 = 0
        idx1 = resp['blocks'][0]['positionSelector']['positionOptions'][idx1]['blockIndex'] # last matchday index
        playable = True
        fct = None
        while idx1 <= idx: # + 1: # next match day is now visible
            dat = resp['blocks'][0]['blocks'][idx1]['title'] # day of matchday
            for item in resp['blocks'][0]['blocks'][idx1]['blocks']:
                img = None
                if 'programHint' in item: # show matches only
                    target = item['programHint']['programId']
                    streamStatus = item['programHint']['streamStatus']
                else:
                    target = None
                    streamStatus = None
                    continue
                title = '{}  {}'.format(dat,item['title'])
                if 'decorator1' in item and item['decorator1'] is not None:
                    if len(str(item['decorator1'])) > 0:
                        title+= '   {}:{}'.format(str(item['decorator1']),str(item['decorator2']))
                if 'title1' in item:
                    title+= '   {}'.format(item['title1'])
                if 'title2' in item and item['title2'] is not None:
                    title+= ' - {}'.format(item['title2'])
                if 'image3' in item:
                    img = item['image3']['IMAGE_PROGRAM_COVER']
                else:
                    img = item['image']
                if streamStatus == 'PAST': # ignore outdated conferences
                    continue
                elif streamStatus == 'FUTURE': # future matches are not playable
                    playable = False
                    fct = None
                elif streamStatus == 'AVAILABLE':
                    playable = True
                    fct = 'getSoccerOnDemand'
                elif streamStatus == 'LIVE':
                    playable = True
                    fct = 'getSoccerLive'
                else: # unknown status
                    playable = False
                    fct = None
                menuEntries.append({'txt':title,'fct':fct,'target':target,'img':img,'playable':playable})
            idx1 += 1
        self.createList(menuEntries,False,True)
    def getSoccer(self,target,status):
        if status == 'LIVE':
            amz = { 'path': self.AMapi.GetSoccerLiveURLs,
                    'target': 'getSoccerLiveURL' }
        elif status == 'ONDEMAND':
            amz = { 'path': self.AMapi.GetSoccerOnDemandURLs,
                    'target': 'getSoccerOnDemandURL' }
        else:
            return False
        resp = self.AMc.amzCall(self.AMapi.GetSoccerProgramDetails,'getSoccerProgramDetails',None,None,target)
        try:
            target = resp['program']['mediaContentList'][0]['mediaContentId']
        except:
            return False
        # target for xml source
        resp = self.AMc.amzCall(amz['path'],amz['target'],'soccer',None,target)
        target = resp['Output']['contentResponseList'][0]['urlList'][0] # link to mpd file
        r = requests.get(target)
        song = self.writeSongFile(r.content.decode('utf-8'),'mpd')

        ''' proxy try - START '''
        song = 'http://{}/mpd/{}'.format(self.AMs.getSetting('proxy'),'song.mpd')
        ''' proxy try - END '''
        self.finalizeItem(song,True)

if __name__ == '__main__':
    AmazonMedia().reqDispatch()
