#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from urllib.parse import quote as urlquote
from urllib.parse import urlencode as urlencode
from resources.lib.menu import AMmenu
from resources.lib.item import AMitem
from resources.lib.tools import AMtools
from resources.lib.amzcall import AMcall

import xbmc

class AmazonMedia():
    def __init__(self):
        self._t = AMtools()
        self._i = AMitem()
        self._m = AMmenu()
        self._c = AMcall()
        self.setVariables()

    def setVariables(self):
        self.showUnplayableSongs = self._t.getSetting('showUnplayableSongs')
        self.sPlayLists     = ["search1PlayLists",  "search2PlayLists", "search3PlayLists"]
        self.sAlbums        = ["search1Albums",     "search2Albums",    "search3Albums"]
        self.sSongs         = ["search1Songs",      "search2Songs",     "search3Songs"]
        self.sStations      = ["search1Stations",   "search2Stations",  "search3Stations"]
        self.sArtists       = ["search1Artists",    "search2Artists",   "search3Artists"]

        if self._t.logging:
            self._t.log(
                  'Handle: ' + self._t.addonHandle.__str__() + os.linesep
                + 'Args  : ' + self._t.addonArgs.__str__() + os.linesep
                + 'Mode  : ' + self._t.addonMode.__str__() + os.linesep
            )

    def reqDispatch(self):
        mode = self._t.getMode()
        # reset and initilialize the addon
        if mode == 'resetAddon':
            self._t.resetAddon()
            xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self._t.getTranslation(30071)))
        # build kodi menus
        elif mode is None:              self._m.createList(self._m.menuHome())
        elif mode == 'menuPlaylists':   self._m.createList(self._m.menuPlaylists(),True)
        elif mode == 'menuAlbums':      self._m.createList(self._m.menuAlbums(),True)
        elif mode == 'menuSongs':       self._m.createList(self._m.menuSongs(),True)
        elif mode == 'menuStations':    self._m.createList(self._m.menuStations(),True)
        elif mode == 'menuArtists':     self._m.createList(self._m.menuArtists(),True)
        elif mode == 'menuSoccer':      self._m.createList(self._m.menuSoccer())
        # search playlists
        elif mode == 'searchPlayLists': self.searchItems(['playlists','catalog_playlist'],30013)
        elif mode in ['search1PlayLists','search2PlayLists','search3PlayLists']:
            exec('self.searchItems([\'playlists\',\'catalog_playlist\'],None,self._t.getSetting("{}"))'.format(mode))
        # search albums
        elif mode == 'searchAlbums':    self.searchItems(['albums','catalog_album'],30010)
        elif mode in ['search1Albums','search2Albums','search3Albums']:
            exec('self.searchItems([\'albums\',\'catalog_album\'],None,self._t.getSetting("{}"))'.format(mode))
        # search songs
        elif mode == 'searchSongs':     self.searchItems(['tracks','catalog_track'],30011)
        elif mode in ['search1Songs','search2Songs','search3Songs']:
            exec('self.searchItems([\'tracks\',\'catalog_track\'],None,self._t.getSetting("{}"))'.format(mode))
        # search artists
        elif mode == 'searchArtist':    self.searchItems(['artists','catalog_artist'],30014)
        elif mode in ['search1Artists','search2Artists','search3Artists']:
            exec('self.searchItems([\'artists\',\'catalog_artist\'],None,self._t.getSetting("{}"))'.format(mode))
        # search stations
        elif mode == 'searchStations':  self.searchItems(['stations','catalog_station'],30016)
        elif mode in ['search1Stations','search2Stations','search3Stations']:
            exec('self.searchItems([\'stations\',\'catalog_station\'],None,self._t.getSetting("{}"))'.format(mode))

        elif mode == 'getArtistDetails':
            asin = self._t.addonArgs.get('asin', [None])
            self.getArtistDetails(asin[0])

        elif mode == 'getRecentlyPlayed':
            items = self._c.amzCall('APIGetRecentTrackActivity', 'recentlyplayed', None, None, 'PLAYED')['recentActivityMap']['PLAYED']
            self.setAddonContent('recentlyplayed',items,'songs')
        elif mode == 'getRecentlyAddedSongs':
            items = self._c.amzCall('APIcirrus','recentlyaddedsongs',None,None,None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
            self.setAddonContent('recentlyaddedsongs',items,'songs')
        elif mode == 'getPopularPlayLists':
            self.getPlayLists('popularity-rank')
        elif mode == 'getNewPlayLists':
            self.getPlayLists('newly-released')
        elif mode == 'getFollowedPlayLists':
            items = self._c.amzCall('APIgetFollowedPlaylistsInLibrary','followedplaylists',None,None,None)
            self.setAddonContent('followedplaylists',items,'albums')
        elif mode == 'getOwnedPlaylists':
            items = self._c.amzCall('APIgetOwnedPlaylistsInLibrary','getownedplaylists',None,None,None)
            self.setAddonContent('ownedplaylists',items,'albums')
        # TODO NEW ownedPlaylist selection
        elif mode == 'showLibraryPlaylists':
            self.showLib()
        elif mode == 'getPlaylistsByIdV2':
            asin = self._t.addonArgs.get('asin', [None])
            #self.getPlaylistsByIdV2(asin[0])
            items = self._c.amzCall('APIgetPlaylistsByIdV2','getplaylistsbyid',None,asin[0],None)
            self.setAddonContent('getplaylistsbyid',items,'songs')

        elif mode == 'getRecomPlayLists':   self.getRecommendations('mp3-prime-browse-carousels_playlistStrategy')
        elif mode == 'getRecomAlbums':      self.getRecommendations('mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy')
        elif mode == 'getRecomStations':    self.getRecommendations('mp3-prime-browse-carousels_mp3ArtistStationStrategy')

        elif mode == 'getNewRecom':         self.getNewRecommendations()
        elif mode == 'getNewRecomDetails':
            asin = self._t.addonArgs.get('target', [None])
            self.getNewRecomDetails(asin[0])
        # get own music, differentiate betwenn purchased and own lib
        # param: searchReturnType , caller, sortCriteriaList.member.1.sortColumn
        elif mode in ['getPurAlbums','getAllAlbums']:
            self.getPurchased(['ALBUMS','getAllDataByMetaType','sortAlbumName'],'albums')
        elif mode in ['getPurSongs','getAllSongs']:
            self.getPurchased(['TRACKS','getServerSongs','sortTitle'],'songs')
        # get amazon stations
        elif mode in ['getStations','getAllArtistsStations','getGenres','getGenres2']:
            #self.getStations(mode.replace('get','').lower())
            items = self._c.amzCall('APIgetStationSections','getStations','/stations')
            self.setAddonContent(mode.replace('get','').lower(),items,'albums')
        elif mode in ['getGenrePlaylist','createQueue']:
            asin = self._t.addonArgs.get('asin', None)
            exec('self.{}(asin[0])'.format(mode))
        # get song lists
        elif mode == 'lookup':
            asin = self._t.addonArgs.get('asin', None)
            self.lookup(asin)
        # play the song
        elif mode == 'getTrack':
            asin = self._t.addonArgs.get('asin', [None])[0]
            objectId = self._t.addonArgs.get('objectId', [None])[0]
            from resources.lib.play import AMplay
            AMplay().getTrack(asin,objectId)
        # Amazon Soccer Live
        elif mode in ['soccerBUND','soccerBUND2','soccerCHAMP','soccerDFBPOKAL','soccerSUPR']:
            self.getSoccerFilter(mode.replace('soccer',''))
        elif mode == 'getSoccerLive':
            objectId = self._t.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'LIVE')
        elif mode == 'getSoccerOnDemand':
            objectId = self._t.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'ONDEMAND')

    # get music information
    def lookup(self,asin):
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        data = self._c.amzCall( 'APIlookup','itemLookup',None,asin,mediatype)
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
            data = self._c.amzCall('APIcirrus', 'itemLookup2ndRound', '/my/albums', [asin], None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
            sel = 'trackInfoList'
        self.setAddonContent(sel,data[sel],'songs')
    def getPlayLists(self,mediatype):
        items = self._c.amzCall('APIgetTopMusicEntities','playlist',None,None,mediatype)
        # data structure is similar to lookup
        self.setAddonContent('playlists',items,'albums')
    def getGenrePlaylist(self,asin):
        items = self._c.amzCall('APIcreateQueue','getGenrePlaylist',None,asin)
        self.setAddonContent('genreplaylist',items,'albums')
    def getRecommendations(self,mediatype):
        resp = self._c.amzCall('APIgetBrowseRecommendations','recommendations',None,None,mediatype)
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
        resp = self._c.amzCall('APIgetHome','new_recommendations')
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
        self._m.createList(menuEntries)
    def getNewRecomDetails(self,target):
        items = None
        resp = self._c.amzCall('APIgetHome','new_recommendations')
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
        resp = self._c.amzCall('APIcirrus','getPurchased',None,None,mode)
        items = resp['searchLibraryResponse']['searchLibraryResult']
        if ctype == 'songs':
            mode = 'purchasedsongs'
        elif ctype == 'albums':
            mode = 'purchasedalbums'
        self.setAddonContent(mode,items,ctype)
    def searchItems(self,mode=None,txt=None,query=None):
        if query == None:
            if self._t.addonArgs.get('token', False):
                query = self._t.addonArgs.get('query', [''])[0]
            else:
                query = self._t.getUserInput(self._t.getTranslation(txt), '')
                if not query:
                    return
        resp = self._c.amzCall( 'APIsearch' , 'searchItems' , '/search' , query,mode )
        items = resp['results'][0]
        if   mode[0] == 'albums':
            if not txt == None:
                self._t.setSearch(self.sAlbums,query)
            self.setAddonContent('searchitems',items,'albums','albums',query)
        elif mode[0] == 'tracks':
            if not txt == None:
                self._t.setSearch(self.sSongs,query)
            self.setAddonContent('searchitems',items,'songs','tracks',query)
        elif mode[0] == 'playlists':
            if not txt == None:
                self._t.setSearch(self.sPlayLists,query)
            self.setAddonContent('searchplaylists',items,'albums',None,query)
        elif mode[0] == 'artists':
            if not txt == None:
                self._t.setSearch(self.sArtists,query)
            self.setAddonContent('searchartists',items,'songs',None,query)
        elif mode[0] == 'stations':
            if not txt == None:
                self._t.setSearch(self.sStations,query)
            self.setAddonContent('searchstations',items,'albums',None,query)
    def getArtistDetails(self,asin):
        resp = self._c.amzCall('APIartistDetailsMetadata','getArtistDetails',None,asin,None)
        items = resp
        self.setAddonContent('artistdetails',items,'albums',None,asin)
    def createQueue(self,asin):
        resp = self._c.amzCall('APIcreateQueue','createQueue',None,asin,None)
        token = resp['queue']['pageToken']
        tracklist = resp['trackMetadataList']
        i = 1
        while token: # 5 songs per loop
            resp = self._c.amzCall('APIQueueGetNextTracks','getNextTracks',None,asin,token)
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
        return self._c.amzCall('APIlookup','itemLookup',None,uniq,['fullAlbumDetails'])#['albumList']
    def getMetaTracks(self,filter):
        return self._c.amzCall('APIV3getTracks','getMetaTracks',None,filter,None)

    def setAddonContent(self,mode,param,ctype,stype=None,query=None):
        sortArray = []
        itemlist = []
        meta = []
        mod = None
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        if   mode == 'albumList' or mode == 'playlistList':
            meta = self.getMetaTracks(param[0]['asin'])['resultList']
            for item in param[0]['tracks']:
                inf, met = self._i.setData(item,{'mode':'getTrack'})
                for i in meta:
                    if item['asin'] == i['metadata']['asin']:
                        inf, met = self._i.setData(i['metadata'],{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                inf['album'] = param[0]['title']
                inf['rating'] = param[0]['reviews']['average']
                met['thumb'] = param[0]['image']
                met['album'] = param[0]['title']
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'artistList':      # no content at the moment
            self._t.log('artistList')
        elif mode == 'trackInfoList':           # track info list
            for item in param:
                meta.append(item['metadata']['asin'])
            meta = self._c.amzCall('APIlookup','itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self._i.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self._i.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'stationList':             # station playlist
            for item in param:
                meta.append(item['identifier'])
            meta = self._c.amzCall('APIlookup','itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self._i.setData(item,{'mode':'getTrack'})
                for i in meta:
                    if item['identifier'] == i['asin']:
                        inf, met = self._i.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self._i.setItem(inf,met)
                itemlist.append((url, li, False))

        elif mode == 'playlists':               # playlists
            for item in param['playlistList']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['title'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'lookup','isList':True})
            self._i.addPaginator(itemlist,param['nextTokenMap']['playlist'],param['playlistList'])

        elif mode == 'followedplaylists':       # followed playlists
            for item in param['playlists']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['title'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'lookup','isList':True})

        elif mode == 'ownedplaylists':          # owned playlists
            for item in param['playlists']:
                inf, met = self._i.setData(item,{'mode':'getPlaylistsByIdV2','isList':True})
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, True))

        elif mode == 'getplaylistsbyid':        # playlists by Id
            for item in param['playlists']:
                for track in item['tracks']:
                    meta.append(track['metadata']['requestedMetadata']['asin'])
            meta = self._c.amzCall('APIlookup','itemLookup',None,meta,mediatype)['trackList']
            for item in param['playlists']:
                for track in item['tracks']:
                    inf, met = self._i.setData(track['metadata']['requestedMetadata'],{'mode':'getTrack'})
                    for i in meta:
                        if track['metadata']['requestedMetadata']['asin'] == i['asin']:
                            inf, met = self._i.setData(i,{'info':inf,'meta':met,'update':True})
                        else:
                            continue
                    url, li  = self._i.setItem(inf,met)
                    if not self.showUnplayableSongs and not met['isPlayable']:
                        continue
                    itemlist.append((url, li, False))

        elif mode == 'recplaylists':            # recommended playlists
            for item in param['playlists']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['title'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'lookup','isList':True})
            self._i.addPaginator(itemlist,param['nextResultsToken'],param['playlists'])

        elif mode == 'recalbums':               # recommended albums
            for item in param['albums']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['albumName'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'lookup','isAlbum':True,'isList':True})
            self._i.addPaginator(itemlist,param['nextResultsToken'],param['albums'])

        elif mode == 'recstations':             # recommended stations
            for item in param['stations']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'createQueue'})
            self._i.addPaginator(itemlist,param['nextResultsToken'],param['stations'])

        elif mode == 'recentlyplayed':          # recently played songs
            for item in param['recentTrackList']:
                inf, met = self._i.setData(item,{'mode':'getTrack'})
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self._i.addPaginator(itemlist,param['nextToken'],param['recentTrackList'])

        elif mode == 'newrecom':                # new recommendations
            for item in param:
                i = item['hint']['__type']
                #self._t.log(i)
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
                inf, met = self._i.setData(item['hint'],mod)
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))

        elif mode == 'recentlyaddedsongs':      # recently added songs
            for item in param['trackInfoList']:
                meta.append(item['metadata']['asin'])
            meta = self._c.amzCall('APIlookup','itemLookup',None,meta,mediatype)['trackList']
            for item in param['trackInfoList']:
                inf, met = self._i.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self._i.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self._i.addPaginator(itemlist,param['nextResultsToken'],param['trackInfoList'])

        elif mode == 'stations':                # (all) stations
            items = param['categories'].get('allStations')['stationMapIds']
            for item in items:
                sortArray.append(param['stations'].get(item))
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'createQueue'})

        elif mode == 'allartistsstations':      # (all artists) stations
            items = param['stations']
            for item in items:
                i = param['stations'].get(item)
                if not i['seedType'] == 'ARTIST':
                    continue
                sortArray.append(i)
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'createQueue'})

        elif mode == 'genres':                  # genre 1st level
            for sec in param['sections']:
                if sec['sectionId'] == 'genres':
                    for item in sec['categoryMapIds']:
                        sortArray.append(param['categories'].get(item))
                else:
                    continue
            sortArray.sort(key=lambda x: x['title'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'getGenres2','isStation':True})

        elif mode == 'genres2':                 # genres 2nd level
            asin = self._t.addonArgs.get('asin', None)[0]
            items = param['categories'].get(asin)['stationMapIds']
            for item in items:
                sortArray.append(param['stations'].get(item))
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                self._i.setListItem(itemlist,i,{'mode':'createQueue'})

        elif mode == 'purchasedalbums':         # purchased and owned albums
            for item in param['searchReturnItemList']:
                meta.append(item['metadata']['asin'])
            meta = self._c.amzCall('APIlookup','itemLookup',None,meta,['fullAlbumDetails'])['albumList']

            for i in param['searchReturnItemList']:
                sortArray.append(i['metadata'])
            sortArray.sort(key=lambda x: x['sortAlbumName'])

            #for item in param['searchReturnItemList']:
            for item in sortArray:
                inf, met = self._i.setData(item,{'mode':'lookup','isAlbum':True})
                for i in meta:
                    if item['albumAsin'] == i['asin']:
                        inf, met = self._i.setData(i,{'info':inf,'meta':met,'isAlbum':True,'update':True,'isList':True})
                    else:
                        continue
                url, li  = self._i.setItem(inf,met)
                itemlist.append((url, li, True))
            self._i.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])

        elif mode == 'purchasedsongs':          # purchased and owned songs
            meta = self.getMeta(param['searchReturnItemList'],{'array1':'metadata','array2':'albumAsin'})['albumList']
            for item in param['searchReturnItemList']:
                inf, met = self._i.setData(item['metadata'],{'mode':'getTrack'})
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self._i.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])

        elif mode == 'searchitems':             # search items (songs / albums)
            for item in param['hits']:
                if stype == 'albums':
                    mod  = {'mode':'lookup','isList':True}
                    fold = True
                elif stype == 'tracks' or stype == 'artists':
                    mod  = {'mode':'getTrack'}
                    fold = False
                inf, met = self._i.setData(item['document'],mod)
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self._t.maxResults: # next page
                    itemlist.append(self._i.setPaginator(param['nextPage'],query))
            except:
                pass

        elif mode == 'searchplaylists':         # search playlists
            for item in param['hits']:
                self._i.setListItem(itemlist,item['document'],{'mode':'lookup','isList':True})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self._t.maxResults: # next page
                    itemlist.append(self._i.setPaginator(param['nextPage'],query))
            except:
                pass

        elif mode == 'searchartists':           # search artists
            for item in param['hits']:
                self._i.setListItem(itemlist,item['document'],{'mode':'getArtistDetails'})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self._t.maxResults: # next page
                    itemlist.append(self._i.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchstations':          # search stations
            for item in param['hits']:
                self._i.setListItem(itemlist,item['document'],{'mode':'createQueue','query':query})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self._t.maxResults: # next page
                    itemlist.append(self._i.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'artistdetails':           # artitist details (albums)
            for item in param['albumList']:
                self._i.setListItem(itemlist,item,{'mode':'lookup'})
            try:
                if len(param['albumList']) == self._t.maxResults:
                    itemlist.append(self._i.setPaginator(param['nextTokenMap']['album'],None,query))
                    #itemlist.append((url, li, True))
            except:
                pass
        self._m.finalizeContent(itemlist,ctype)

    # def getSoccerFilter(self,target=None): # 'BUND', 'BUND2', 'CHAMP', 'DFBPOKAL', 'SUPR'
    #     menuEntries = []
    #     resp = self._c.amzCall('APIGetSoccerMain','getSoccerMain',None,None,target)
    #     idx = resp['blocks'][0]['positionSelector']['currentPosition']['blockIndex'] # current matchday
    #     if idx == -1: # if no entries are available
    #         menuEntries.append({'txt':'Empty List','fct':None,'target':None,'img':self._t.getSetting('img_soccer'),'playable':False})
    #         self._m.createList(menuEntries,False,True)
    #         return
    #     param = resp['blocks'][0]['positionSelector']['positionOptions']
    #     idx1 = 0
    #     for item in param: # find last matchday based on current matchday
    #         if item['blockIndex'] < idx:
    #             idx1+=1
    #             continue
    #         break
    #     idx1-= 1
    #     if idx1 < 0:
    #         idx1 = 0
    #     idx1 = resp['blocks'][0]['positionSelector']['positionOptions'][idx1]['blockIndex'] # last matchday index
    #     playable = True
    #     fct = None
    #     while idx1 <= idx: # + 1: # next match day is now visible
    #         dat = resp['blocks'][0]['blocks'][idx1]['title'] # day of matchday
    #         for item in resp['blocks'][0]['blocks'][idx1]['blocks']:
    #             img = None
    #             if 'programHint' in item: # show matches only
    #                 target = item['programHint']['programId']
    #                 streamStatus = item['programHint']['streamStatus']
    #             else:
    #                 target = None
    #                 streamStatus = None
    #                 continue
    #             title = '{}  {}'.format(dat,item['title'])
    #             if 'decorator1' in item and item['decorator1'] is not None:
    #                 if len(str(item['decorator1'])) > 0:
    #                     title+= '   {}:{}'.format(str(item['decorator1']),str(item['decorator2']))
    #             if 'title1' in item:
    #                 title+= '   {}'.format(item['title1'])
    #             if 'title2' in item and item['title2'] is not None:
    #                 title+= ' - {}'.format(item['title2'])
    #             if 'image3' in item:
    #                 img = item['image3']['IMAGE_PROGRAM_COVER']
    #             else:
    #                 img = item['image']
    #             if streamStatus == 'PAST': # ignore outdated conferences
    #                 continue
    #             elif streamStatus == 'FUTURE': # future matches are not playable
    #                 playable = False
    #                 fct = None
    #             elif streamStatus == 'AVAILABLE':
    #                 playable = True
    #                 fct = 'getSoccerOnDemand'
    #             elif streamStatus == 'LIVE':
    #                 playable = True
    #                 fct = 'getSoccerLive'
    #             else: # unknown status
    #                 playable = False
    #                 fct = None
    #             menuEntries.append({'txt':title,'fct':fct,'target':target,'img':img,'playable':playable})
    #         idx1 += 1
    #     self._m.createList(menuEntries,False,True)
    # def getSoccer(self,target,status):
    #     if status == 'LIVE':
    #         amz = { 'path': self._a.getAPI('APIGetSoccerLiveURLs'),
    #                 'target': 'getSoccerLiveURL' }
    #     elif status == 'ONDEMAND':
    #         amz = { 'path': self._a.getAPI('APIGetSoccerOnDemandURLs'),
    #                 'target': 'getSoccerOnDemandURL' }
    #     else:
    #         return False
    #     resp = self._c.amzCall(
    #         self._a.getAPI('APIGetSoccerProgramDetails'),
    #         'getSoccerProgramDetails',
    #         None,
    #         None,
    #         target
    #     )
    #     try:
    #         target = resp['program']['mediaContentList'][0]['mediaContentId']
    #     except:
    #         return False
    #     # target for xml source
    #     resp = self._c.amzCall(
    #         amz['path'],
    #         amz['target'],
    #         'soccer',
    #         None,
    #         target
    #     )
    #     target = resp['Output']['contentResponseList'][0]['urlList'][0] # link to mpd file
    #     r = requests.get(target)
    #     from resources.lib.play import AMplay
    #     song = AMplay().writeSongFile(r.content.decode('utf-8'),'mpd')

    #     ''' proxy try - START '''
    #     song = 'http://{}/mpd/{}'.format(self._t.getSetting('proxy'),'song.mpd')
    #     ''' proxy try - END '''
    #     AMplay().finalizeItem(song,True)
    # def getPodcasts(self):
    #     resp = self._c.amzCall(self._a.getAPI('APIGetPodcast'),'getPodcasts',None,None,None)

if __name__ == '__main__':
    AmazonMedia().reqDispatch()
