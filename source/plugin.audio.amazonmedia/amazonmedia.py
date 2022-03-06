#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from urllib.parse import quote as urlquote
from urllib.parse import urlencode as urlencode

import os
import xbmc

from resources.lib.item import AMitem
from resources.lib.menu import AMmenu
from resources.lib.tools import AMtools
from resources.lib.logon import AMlogon
from resources.lib.amzcall import AMcall

class AmazonMedia( AMtools ):

    def reqDispatch( self ):
        """
        Dispatch the incoming Addon requests
        """
        if self.G['logging']:
            self.log(
                'AmazonMedia ' + os.linesep
                + 'Handle: ' + self.G['addonHandle'].__str__() + os.linesep
                + 'Args  : ' + self.G['addonArgs'].__str__() + os.linesep
                + 'Mode  : ' + self.G['addonMode'].__str__() + os.linesep
            )

        mode = self.getMode()
        # reset and initilialize the addon
        if mode == 'resetAddon':
            self.resetAddon()
            xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self.getTranslation(30071)))
            return
        elif mode == 'resetCredentials':
            self.resetCredentials()
            xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self.getTranslation(30076)))
            return

        try:
            self.credentials = self.load()
        except IOError: # no credentials available, start logon
            self.credentials = AMlogon().amazonLogon()

        self._c = AMcall()
        self._i = AMitem()

        self.showUnplayableSongs = self.getSetting('showUnplayableSongs')
        self.sPlayLists     = ['search1PlayLists',  'search2PlayLists', 'search3PlayLists']
        self.sAlbums        = ['search1Albums',     'search2Albums',    'search3Albums']
        self.sSongs         = ['search1Songs',      'search2Songs',     'search3Songs']
        self.sStations      = ['search1Stations',   'search2Stations',  'search3Stations']
        self.sArtists       = ['search1Artists',    'search2Artists',   'search3Artists']

        # build kodi menus
        if mode is None:                self.createList( AMmenu.menuHome() )
        elif mode == 'menuPlaylists':   self.createList( AMmenu.menuPlaylists(),True )
        elif mode == 'menuAlbums':      self.createList( AMmenu.menuAlbums(),True )
        elif mode == 'menuSongs':       self.createList( AMmenu.menuSongs(),True )
        elif mode == 'menuStations':    self.createList( AMmenu.menuStations(),True )
        elif mode == 'menuArtists':     self.createList( AMmenu.menuArtists(),True )

        try:
            # search playlists
            if mode == 'searchPlayLists': self.searchItems(['playlists','catalog_playlist'],30013)
            elif mode in ['search1PlayLists','search2PlayLists','search3PlayLists']:
                exec('self.searchItems([\'playlists\',\'catalog_playlist\'],None,self.getSetting("{}"))'.format(mode))

            # search albums
            elif mode == 'searchAlbums':    self.searchItems(['albums','catalog_album'],30010)
            elif mode in ['search1Albums','search2Albums','search3Albums']:
                exec('self.searchItems([\'albums\',\'catalog_album\'],None,self.getSetting("{}"))'.format(mode))

            # search songs
            elif mode == 'searchSongs':     self.searchItems(['tracks','catalog_track'],30011)
            elif mode in ['search1Songs','search2Songs','search3Songs']:
                exec('self.searchItems([\'tracks\',\'catalog_track\'],None,self.getSetting("{}"))'.format(mode))

            # search artists
            elif mode == 'searchArtist':    self.searchItems(['artists','catalog_artist'],30014)
            elif mode in ['search1Artists','search2Artists','search3Artists']:
                exec('self.searchItems([\'artists\',\'catalog_artist\'],None,self.getSetting("{}"))'.format(mode))

            # search stations
            elif mode == 'searchStations':  self.searchItems(['stations','catalog_station'],30016)
            elif mode in ['search1Stations','search2Stations','search3Stations']:
                exec('self.searchItems([\'stations\',\'catalog_station\'],None,self.getSetting("{}"))'.format(mode))

            elif mode == 'getArtistDetails':
                asin = self.G['addonArgs'].get('asin', [None])
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

            elif mode == 'getPlaylistsByIdV2':
                asin = self.G['addonArgs'].get('asin', [None])
                #self.getPlaylistsByIdV2(asin[0])
                items = self._c.amzCall('APIgetPlaylistsByIdV2','getplaylistsbyid',None,asin[0],None)
                self.setAddonContent('getplaylistsbyid',items,'songs')

            # recommendations
            elif mode == 'getRecomPlayLists':   self.getRecommendations('mp3-prime-browse-carousels_playlistStrategy')
            elif mode == 'getRecomAlbums':      self.getRecommendations('mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy')
            elif mode == 'getRecomStations':    self.getRecommendations('mp3-prime-browse-carousels_mp3ArtistStationStrategy')

            elif mode == 'getNewRecom':         self.getNewRecommendations()
            elif mode == 'getNewRecomDetails':
                asin = self.G['addonArgs'].get('target', [None])
                self.getNewRecomDetails(asin[0])

            # get own music, differentiate betwenn purchased and own lib
            # param: searchReturnType , caller, sortCriteriaList.member.1.sortColumn
            elif mode in ['getPurAlbums','getAllAlbums']:
                self.getPurchased(['ALBUMS','getAllDataByMetaType','sortAlbumName'],'albums')
            elif mode in ['getPurSongs','getAllSongs']:
                self.getPurchased(['TRACKS','getServerSongs','sortTitle'],'songs')

            # get amazon stations
            elif mode in ['getStations','getAllArtistsStations','getGenres','getGenres2']:
                items = self._c.amzCall('APIgetStationSections','getStations','/stations')
                self.setAddonContent(mode.replace('get','').lower(),items,'albums')

            elif mode in ['getGenrePlaylist','createQueue']:
                asin = self.G['addonArgs'].get('asin', None)
                exec('self.{}(asin[0])'.format(mode))

            # get song lists
            elif mode == 'lookup':
                asin = self.G['addonArgs'].get('asin', None)
                self.lookup(asin)

            # play the song
            elif mode == 'getTrack':
                asin = self.G['addonArgs'].get('asin', [None])[0]
                objectId = self.G['addonArgs'].get('objectId', [None])[0]
                from resources.lib.play import AMplay
                AMplay().getTrack(asin,objectId)
 
        except: # something went wrong, try to logon again
            self.resetCredentials()
            self.credentials = AMlogon().amazonLogon()

    # get music information
    def lookup( self, asin ):
        """
        Lookup function to collect further detials for the given ID
        :param str asin: Playlist-, Albums-, Song-, Artist-ID
        """
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        data = self._c.amzCall( 'APIlookup', 'itemLookup', None, asin, mediatype )
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
            data = self._c.amzCall( 'APIcirrus', 'itemLookup2ndRound', '/my/albums', [asin], None )['selectTrackMetadataResponse']['selectTrackMetadataResult']
            sel = 'trackInfoList'
        self.setAddonContent( sel, data[sel], 'songs' )

    def getPlayLists( self, mediatype ):
        """
        Collect Playlist information
        :param str mediatype:   dynamic API parameter
        """
        items = self._c.amzCall( 'APIgetTopMusicEntities', 'playlist', None, None, mediatype )
        # data structure is similar to lookup
        self.setAddonContent( 'playlists', items, 'albums' )

    def getGenrePlaylist( self, asin ):
        """
        Collect Genre information
        :param str asin:    Station-ID
        """
        items = self._c.amzCall( 'APIcreateQueue', 'getGenrePlaylist', None, asin )
        self.setAddonContent( 'genreplaylist', items, 'albums' )

    def getRecommendations( self, mediatype ):
        """
        Collect recommendations for Playlists, Album, Stations
        :param str mediatype:   historical API entry point
        """
        resp = self._c.amzCall( 'APIgetBrowseRecommendations', 'recommendations', None, None, mediatype )
        sel = ''
        if   resp['recommendations'][0]['recommendationType'] == 'PLAYLIST':
            sel = 'recplaylists'
        elif resp['recommendations'][0]['recommendationType'] == 'ALBUM':
            sel = 'recalbums'
        elif resp['recommendations'][0]['recommendationType'] == 'STATION':
            sel = 'recstations'
        self.setAddonContent( sel, resp['recommendations'][0], 'albums' )

    def getNewRecommendations( self ):
        """
        Collect new recommendations due to API change
        """
        menuEntries = []
        resp = self._c.amzCall( 'APIgetHome', 'new_recommendations' )
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
        self.createList( menuEntries )

    def getNewRecomDetails( self, asin ):
        """
        Further recommendation details
        :param str asin:    unique ID
        """
        items = None
        resp = self._c.amzCall( 'APIgetHome', 'new_recommendations' )
        for item in resp['blocks']:
            if (('ButtonGrid' in item['__type']) or ('Barker' in item['__type'])): # ignore button fields
                continue
            if asin in item['title']: # find the category
                items = item['blocks']
                break
        if items == None: # in case of empty list
            return
        self.setAddonContent( 'newrecom', items, 'albums' )

    def getPurchased( self, mode, ctype ):
        """
        Collect purchased Albums and Songs
        :param array mode:  dynamic API parameter
        :param str ctype:   content type (songs / albums)
        """
        resp = self._c.amzCall('APIcirrus','getPurchased',None,None,mode)
        items = resp['searchLibraryResponse']['searchLibraryResult']
        if ctype == 'songs':
            mode = 'purchasedsongs'
        elif ctype == 'albums':
            mode = 'purchasedalbums'
        self.setAddonContent(mode,items,ctype)

    def searchItems( self, mode=None, txt=None, query=None ):
        """
        Search function for Playlists, Albums, Songs, Stations and Artists
        :param array mode:  search mode
        :param str txt:     dialog description
        :param str query:   search string
        """
        if query == None:
            if self.G['addonArgs'].get('token', False):
                query = self.G['addonArgs'].get('query', [''])[0]
            else:
                query = self.getUserInput( self.getTranslation( txt ), '' )
                if not query:
                    return

        resp = self._c.amzCall( 'APIsearch', 'searchItems', '/search', query, mode )
        items = resp['results'][0]
        if   mode[0] == 'albums':
            if not txt == None:
                self.setSearch( self.sAlbums, query )
            self.setAddonContent( 'searchitems', items, 'albums', 'albums', query )

        elif mode[0] == 'tracks':
            if not txt == None:
                self.setSearch( self.sSongs, query )
            self.setAddonContent( 'searchitems', items, 'songs', 'tracks', query )

        elif mode[0] == 'playlists':
            if not txt == None:
                self.setSearch( self.sPlayLists, query )
            self.setAddonContent( 'searchplaylists', items, 'albums', None, query )

        elif mode[0] == 'artists':
            if not txt == None:
                self.setSearch( self.sArtists, query )
            self.setAddonContent( 'searchartists', items, 'albums', None, query ) #songs

        elif mode[0] == 'stations':
            if not txt == None:
                self.setSearch( self.sStations, query )
            self.setAddonContent( 'searchstations', items, 'albums', None, query )

    def getArtistDetails( self, asin ):
        """
        Collect Artist details
        :param str asin:    Unique ID
        """
        resp = self._c.amzCall( 'APIartistDetailsMetadata', 'getArtistDetails', None, asin, None )
        items = resp
        self.setAddonContent( 'artistdetails', items, 'albums', None, asin )

    def createQueue( self, asin ):
        """
        Create playlist queue for given unique ID
        :param str asin:    Unique ID
        """
        resp = self._c.amzCall( 'APIcreateQueue', 'createQueue', None, asin, None )
        token = resp['queue']['pageToken']
        tracklist = resp['trackMetadataList']
        i = 1
        while token: # 5 songs per loop
            resp = self._c.amzCall( 'APIQueueGetNextTracks', 'getNextTracks', None, asin, token )
            token = resp['nextPageToken']
            for item in resp['trackMetadataList']:
                tracklist.append(item)
            if i == 10:
                break
            i += 1
        self.setAddonContent( 'stationList', tracklist, 'songs' )

    # kodi visualization
    def getMeta( self, resp, filter ):
        """
        Collect further meta data for given response list
        :param array resp:  response list
        :param str filter:  function filter
        """
        meta = []
        for item in resp:
            if len(filter) == 1:
                meta.append(item[filter['array1']])
            else:
                meta.append(item[filter['array1']][filter['array2']])
        seen = set()
        uniq = [x for x in meta if x not in seen and not seen.add(x)] # make it unique
        return self._c.amzCall( 'APIlookup', 'itemLookup', None, uniq, ['fullAlbumDetails'] ) #['albumList']

    def getMetaTracks( self, asin ):
        """
        Collect Songs for the given Album-, Playlist-ID
        :param str asin:    unique Album/Playlist-ID
        """
        return self._c.amzCall( 'APIV3getTracks', 'getMetaTracks', None, asin, None )

    def setAddonContent( self, mode, param, ctype, stype=None, query=None ):
        """
        Generic function for data collection and mapping to ensure proper Kodi visualization
        :param str mode:    addon request mode
        :param array param: data response array
        :param str ctype:   content type - Albums, Songs
        :param str stype:   search type - Albums, Tracks, Artists
        :param str query:   sarch query string
        """
        sortArray = []
        itemlist = []
        meta = []
        mod = None
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        if   mode == 'albumList' or mode == 'playlistList':
            meta = self.getMetaTracks( param[0]['asin'] )['resultList']
            if len(param[0]['tracks']) > 0:     # Bugfix, in case of empty track list, try to use the lookup content
                for item in param[0]['tracks']:
                    inf, met = self._i.setData( item, {'mode':'getTrack'} )
                    for i in meta:
                        if item['asin'] == i['metadata']['asin']:
                            inf, met = self._i.setData( i['metadata'],{'info':inf,'meta':met,'update':True} )
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
            else:
                for item in meta:               # Bugfix, try to use the loopup metadata as content
                    inf, met = self._i.setData(item['metadata'],{'mode':'getTrack'})
                    url, li  = self._i.setItem(inf,met)
                    if not self.showUnplayableSongs and not met['isPlayable']:
                        continue
                    itemlist.append((url, li, False))

        elif mode == 'artistList':              # no content at the moment
            self.log('artistList')
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
                itemlist.append(
                    self._i.setListItem(i,{'mode':'lookup','isList':True})
                )
            page, listitem = self._i.addPaginator(param['nextTokenMap']['playlist'],param['playlistList'])
            if page:
                itemlist.append( listitem )

        elif mode == 'followedplaylists':       # followed playlists
            for item in param['playlists']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['title'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'lookup','isList':True})
                )

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
                itemlist.append(
                    self._i.setListItem(i,{'mode':'lookup','isList':True})
                )
            page, listitem = self._i.addPaginator(param['nextResultsToken'],param['playlists'])
            if page:
                itemlist.append( listitem )

        elif mode == 'recalbums':               # recommended albums
            for item in param['albums']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['albumName'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'lookup','isAlbum':True, 'isAlbumFolder':True, 'isList':True})
                )
            page, listitem = self._i.addPaginator(param['nextResultsToken'],param['albums'])
            if page:
                itemlist.append( listitem )

        elif mode == 'recstations':             # recommended stations
            for item in param['stations']:
                sortArray.append(item)
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'createQueue'})
                )
            page, listitem = self._i.addPaginator(param['nextResultsToken'],param['stations'])
            if page:
                itemlist.append( listitem )

        elif mode == 'recentlyplayed':          # recently played songs
            for item in param['recentTrackList']:
                inf, met = self._i.setData(item,{'mode':'getTrack'})
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            page, listitem = self._i.addPaginator(param['nextToken'],param['recentTrackList'])
            if page:
                itemlist.append( listitem )

        elif mode == 'newrecom':                # new recommendations
            for item in param:
                i = item['hint']['__type']
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
            page, listitem = self._i.addPaginator(param['nextResultsToken'],param['trackInfoList'])
            if page:
                itemlist.append( listitem )

        elif mode == 'stations':                # (all) stations
            items = param['categories'].get('allStations')['stationMapIds']
            for item in items:
                sortArray.append(param['stations'].get(item))
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'createQueue'})
                )

        elif mode == 'allartistsstations':      # (all artists) stations
            items = param['stations']
            for item in items:
                i = param['stations'].get(item)
                if not i['seedType'] == 'ARTIST':
                    continue
                sortArray.append(i)
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'createQueue'})
                )

        elif mode == 'genres':                  # genre 1st level
            for sec in param['sections']:
                if sec['sectionId'] == 'genres':
                    for item in sec['categoryMapIds']:
                        sortArray.append(param['categories'].get(item))
                else:
                    continue
            sortArray.sort(key=lambda x: x['title'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'getGenres2','isStation':True})
                )

        elif mode == 'genres2':                 # genres 2nd level
            asin = self.G['addonArgs'].get('asin', None)[0]
            items = param['categories'].get(asin)['stationMapIds']
            for item in items:
                sortArray.append(param['stations'].get(item))
            sortArray.sort(key=lambda x: x['stationTitle'])
            for i in sortArray:
                itemlist.append(
                    self._i.setListItem(i,{'mode':'createQueue'})
                )

        elif mode == 'purchasedalbums':         # purchased and owned albums
            for item in param['searchReturnItemList']:
                meta.append(item['metadata']['asin'])
            meta = self._c.amzCall('APIlookup','itemLookup',None,meta,['fullAlbumDetails'])['albumList']

            for i in param['searchReturnItemList']:
                sortArray.append(i['metadata'])
            sortArray.sort(key=lambda x: x['sortAlbumName'])

            for item in sortArray:
                inf, met = self._i.setData(item,{'mode':'lookup', 'isAlbumFolder':True, 'isAlbum':True})
                for i in meta:
                    if item['albumAsin'] == i['asin']:
                        inf, met = self._i.setData( i,{'info':inf, 'meta':met, 'isAlbum':True, 'update':True, 'isAlbumFolder':True, 'isList':True} )
                    else:
                        continue
                url, li  = self._i.setItem(inf,met)
                itemlist.append((url, li, True))
            page, listitem = self._i.addPaginator(param['nextResultsToken'],param['searchReturnItemList'])
            if page:
                itemlist.append( listitem )

        elif mode == 'purchasedsongs':          # purchased and owned songs
            meta = self.getMeta(param['searchReturnItemList'],{'array1':'metadata','array2':'albumAsin'})['albumList']
            for item in param['searchReturnItemList']:
                inf, met = self._i.setData(item['metadata'],{'mode':'getTrack'})
                url, li  = self._i.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            page, listitem = self._i.addPaginator(param['nextResultsToken'],param['searchReturnItemList'])
            if page:
                itemlist.append( listitem )

        elif mode == 'searchitems':             # search items (songs / albums)
            for item in param['hits']:
                if stype == 'albums':
                    mod  = {'mode':'lookup', 'isAlbumFolder':True, 'isList':True}
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
                if not param['nextPage'] == None and len(param['hits']) <= self.G['maxResults']: # next page
                    itemlist.append( self._i.setPaginator( param['nextPage'], query ) )
            except:
                pass

        elif mode == 'searchplaylists':         # search playlists
            for item in param['hits']:
                itemlist.append(
                    self._i.setListItem(item['document'],{'mode':'lookup','isList':True})
                )
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.G['maxResults']: # next page
                    itemlist.append( self._i.setPaginator( param['nextPage'], query ) )
            except:
                pass

        elif mode == 'searchartists':           # search artists
            for item in param['hits']:
                itemlist.append(
                    self._i.setListItem(item['document'],{'mode':'getArtistDetails','isList':True})
                )
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.G['maxResults']: # next page
                    itemlist.append( self._i.setPaginator( param['nextPage'], query ) )
            except:
                pass

        elif mode == 'searchstations':          # search stations
            for item in param['hits']:
                itemlist.append(
                    self._i.setListItem( item['document'], {'mode':'createQueue', 'query':query} )
                )
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.G['maxResults']: # next page
                    itemlist.append( self._i.setPaginator( param['nextPage'], query ) )
            except:
                pass

        elif mode == 'artistdetails':           # artitist details (albums)
            for item in param['albumList']:
                itemlist.append(
                    self._i.setListItem( item, {'mode':'lookup', 'isAlbumFolder':True, 'isList':True } )
                )
            try:
                if len(param['albumList']) == self.G['maxResults']:
                    itemlist.append( self._i.setPaginator( param['nextTokenMap']['album'], None, query ) )
            except:
                pass

        self.finalizeContent( self.G['addonHandle'], itemlist, ctype )

if __name__ == '__main__':
    AmazonMedia().reqDispatch()
