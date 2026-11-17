#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import traceback
from urllib.parse import urlencode
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.item import AMitem
from resources.lib.menu import AMmenu
from resources.lib.tools import AMtools
from resources.lib.logon import AMlogon
from resources.lib.amzcall import AMcall
from resources.lib import gql

class AmazonMedia( AMtools ):
    LOOKUP_FEATURES = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
    # search history, by the mode that searches again
    SEARCH_MODES = {'PlayLists': 'searchPlayLists', 'Albums': 'searchAlbums', 'Songs': 'searchSongs', 'Artists': 'searchArtist'}

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
            xbmc.executebuiltin('Notification("Information", {}, 5000, )'.format(self.getTranslation(30071)))
            return
        elif mode == 'resetCredentials':
            self.resetCredentials()
            xbmc.executebuiltin('Notification("Information", {}, 5000, )'.format(self.getTranslation(30076)))
            return

        try:
            self.credentials = self.load()
        except IOError: # no credentials available, start logon
            self.credentials = AMlogon().amazonLogon()
            if not self.credentials:
                return

        self._c = AMcall()
        self._i = AMitem()

        self.hideUnplayableSongs = self.getSetting('hideUnplayableSongs')

        # build kodi menus
        if mode is None:                self.createList( AMmenu.menuHome() )
        elif mode == 'menuPlaylists':   self.createList( AMmenu.menuPlaylists() )
        elif mode == 'menuAlbums':      self.createList( AMmenu.menuAlbums() )
        elif mode == 'menuSongs':       self.createList( AMmenu.menuSongs() )
        elif mode == 'menuArtists':     self.createList( AMmenu.menuArtists() )

        try:
            if mode == 'searchPlayLists':   self.searchItems('PlayLists',30013)
            elif mode == 'searchAlbums':    self.searchItems('Albums',30010)
            elif mode == 'searchSongs':     self.searchItems('Songs',30011)
            elif mode == 'searchArtist':    self.searchItems('Artists',30014)

            # search history
            elif mode in ['searchHistory' + kind for kind in self.SEARCH_MODES]:
                self.showSearchHistory( mode[len('searchHistory'):] )
            elif mode == 'deleteSearch':
                self.deleteSearch( self.G['addonArgs']['kind'][0], self.G['addonArgs']['query'][0] )
                xbmc.executebuiltin('Container.Refresh')

            elif mode == 'getArtistDetails':
                asin = self.G['addonArgs'].get('asin', [None])
                self.viaGraphQL( lambda g: self.gqlArtist(g, asin[0]) )

            elif mode == 'getRecentlyAddedSongs':
                items = self._c.amzCall('APIV3getTracks','recentlyaddedsongs',None,None,None)
                self.setAddonContent('recentlyaddedsongs',items,'songs')
                if not items.get('resultList'):
                    xbmcgui.Dialog().notification(xbmc.getLocalizedString(19033), self.getTranslation(30079), xbmcgui.NOTIFICATION_INFO, 5000)

            elif mode == 'getPopularPlayLists': self.viaGraphQL( lambda g: self.gqlRecommender(g, 'uri:///popular/top-playlists', 'playlist') )
            elif mode == 'getNewPlayLists':     self.viaGraphQL( lambda g: self.gqlRecommender(g, 'uri:///new/playlists', 'playlist') )
            elif mode == 'getPopularAlbums':    self.viaGraphQL( lambda g: self.gqlRecommender(g, 'uri:///popular/top-albums', 'album') )
            elif mode == 'getNewAlbums':        self.viaGraphQL( lambda g: self.gqlRecommender(g, 'uri:///new/albums', 'album') )

            elif mode == 'getGenres':
                self.viaGraphQL( self.gqlGenres )
            elif mode == 'getGenre':
                self.viaGraphQL( lambda g: self.gqlGenre(g, self.G['addonArgs'].get('asin', [None])[0]) )
            elif mode == 'getGenreShelf':
                self.viaGraphQL( lambda g: self.gqlGenreShelf(g, self.G['addonArgs'].get('asin', [None])[0]) )
            elif mode == 'getStations':
                self.viaGraphQL( self.gqlStations )
            elif mode == 'getStation':
                self.viaGraphQL( lambda g: self.gqlStation(g, self.G['addonArgs'].get('asin', [None])[0]) )

            elif mode == 'getLibraryArtists':
                self.viaGraphQL( lambda g: self.gqlLibrary(g, 'artists') )

            elif mode == 'getFollowedPlayLists':
                self.viaGraphQL( lambda g: self.gqlPlaylists(g, followed=True) )

            elif mode == 'getOwnedPlaylists':
                self.viaGraphQL( lambda g: self.gqlPlaylists(g, followed=False) )

            elif mode == 'getPlaylistsByIdV2':
                asin = self.G['addonArgs'].get('asin', [None])
                self.viaGraphQL( lambda g: (self.gqlPlaylistTracks(found(g.playlist(asin[0]))), 'songs') )

            # recommendations
            elif mode == 'getRecomPlayLists':   self.viaGraphQL( lambda g: self.gqlRecommended(g, 'Playlist') )
            elif mode == 'getRecomAlbums':      self.viaGraphQL( lambda g: self.gqlRecommended(g, 'Album') )

            # get own music, differentiate betwenn purchased and own lib
            elif mode in ['getPurAlbums','getAllAlbums']:
                self.getPurchased('albums')
            elif mode in ['getPurSongs','getAllSongs']:
                self.getPurchased('songs')

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
 
        except Exception:
            # The credentials stay: a failed request is no indication that they went stale.
            self.log(traceback.format_exc(), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(xbmc.getLocalizedString(257), self.getTranslation(30077), xbmcgui.NOTIFICATION_ERROR, 5000)
            xbmcplugin.endOfDirectory(self.G['addonHandle'], False)

    # get music information
    def lookup( self, asin ):
        """
        Lookup function to collect the songs of an album or a playlist
        :param str asin: Playlist- or Albums-ID
        """
        self.viaGraphQL( lambda g: self.gqlLookup(g, asin[0]) )

    def getPurchased( self, ctype ):
        """
        Collect purchased Albums and Songs
        :param str ctype:   content type (songs / albums)
        """
        # Albums bought have no list of their own in the GraphQL interface.
        kind = {'getAllSongs': 'songs', 'getPurSongs': 'purchased', 'getAllAlbums': 'albums'}.get(self.getMode())
        if kind:
            self.viaGraphQL( lambda g: self.gqlLibrary(g, kind) )
        else:
            self.setAddonContent( 'purchasedalbums', self._c.amzCall('APIV3getAlbums', 'getLibraryAlbums'), ctype )

    def searchItems( self, kind, txt ):
        """
        Search function for Playlists, Albums, Songs and Artists
        :param str kind:    PlayLists, Albums, Songs or Artists; the search history is kept by it
        :param str txt:     dialog description
        """
        # An entry of the search history carries its search string.
        query = self.G['addonArgs'].get('query', [None])[0]
        if query is None:
            query = self.getUserInput( self.getTranslation( txt ), '' )
            if not query:
                return
        self.viaGraphQL( lambda g: self.gqlSearch(g, kind, query) )
        if not self.pageToken():
            self.addSearch( kind, query )

    def showSearchHistory( self, kind ):
        """
        The terms searched for before, to search again or to remove
        :param str kind:    PlayLists, Albums, Songs or Artists
        """
        art = dict( self._i.setImage(self.imageUrl('search.png')), fanart=self.imageUrl('search.png') )
        itemlist = []
        for query in self.searchHistory(kind):
            li = xbmcgui.ListItem(label=query)
            li.setArt( art )
            delete = '{}?{}'.format( self.G['addonBaseUrl'], urlencode({'mode': 'deleteSearch', 'kind': kind, 'query': query}) )
            li.addContextMenuItems([( self.getTranslation(30044), 'RunPlugin({})'.format(delete) )])
            url = '{}?{}'.format( self.G['addonBaseUrl'], urlencode({'mode': self.SEARCH_MODES[kind], 'query': query}) )
            itemlist.append(( url + self.crumbsTo(query), li, True ))
        self.finalizeContent( self.G['addonHandle'], itemlist, '' )

    def appendSong( self, itemlist, inf, met ):
        """
        Add a song to the listing, unless it cannot be played and such songs are hidden
        """
        url, li = self._i.setItem(inf,met)
        if met['isPlayable'] or not self.hideUnplayableSongs:
            itemlist.append((url, li, False))

    def appendCatalogueSongs( self, itemlist, songs ):
        """
        Add songs to the listing, completed with what the catalogue knows of them
        :param array songs: song data, each with its asin
        """
        # A song of the personal library that is not in the catalogue, an upload for instance, has no asin.
        asins = [s['asin'] for s in songs if s.get('asin')]
        known = {i['asin']: i for i in self._c.amzCall('APIlookup','itemLookup',None,asins,self.LOOKUP_FEATURES).get('trackList') or []} if asins else {}
        for song in songs:
            inf, met = self._i.setData(song,{'mode':'getTrack'})
            self.appendSong( itemlist, *self._i.update(inf, met, known.get(song.get('asin'))) )

    def appendSorted( self, itemlist, entries, key, param ):
        """
        Add folders to the listing, sorted by the given field
        """
        for entry in sorted(entries, key=lambda x: x[key]):
            itemlist.append( self._i.setListItem(entry, param) )

    # The GraphQL interface of the web player. Each function returns the entries of the list
    # and its content type.

    ALBUM_FOLDER = {'mode': 'lookup', 'isAlbumFolder': True, 'isList': True}

    def viaGraphQL( self, build ):
        """
        Build a list from the GraphQL interface and hand it to Kodi
        :param function build:  takes an AMgql and returns the entries and the content type
        """
        itemlist, ctype = build( gql.AMgql() )
        self.finalizeContent( self.G['addonHandle'], itemlist, ctype )

    def pageToken( self ):
        return self.G['addonArgs'].get('token', [None])[0]

    def songEntries( self, tracks, album=None ):
        itemlist = []
        for node in tracks:
            inf, met = self._i.setData( gql.track(node, album), {'mode': 'getTrack'} )
            if album:
                inf['album'] = album.get('title')
            self.appendSong( itemlist, inf, met )
        return itemlist

    def folderEntries( self, items, param ):
        return [self._i.setListItem( item, dict(param) ) for item in items]

    def nextPage( self, itemlist, cursor, asin=None ):
        if cursor:
            itemlist.append( self._i.setPaginator(cursor, None, asin) )
        return itemlist

    def gqlSearch( self, g, kind, query ):
        found, cursor = g.searchMore( kind, query, self.pageToken() )
        if kind == 'Songs':
            entries, ctype = self.songEntries(found), 'songs'
        elif kind == 'Albums':
            entries, ctype = self.folderEntries( [gql.album(n) for n in found], self.ALBUM_FOLDER ), 'albums'
        elif kind == 'PlayLists':
            entries, ctype = self.folderEntries( [gql.playlist(n) for n in found], {'mode': 'lookup', 'isList': True} ), 'albums'
        else:
            entries, ctype = self.folderEntries( [gql.artist(n) for n in found], {'mode': 'getArtistDetails', 'isList': True} ), 'albums'
        if cursor:
            entries.append( self._i.setPaginator(cursor, query) )
        return entries, ctype

    def gqlRecommender( self, g, rid, kind ):
        """
        A list of charts or new releases
        :param str kind: playlist or album
        """
        found, cursor = g.recommender( rid, self.pageToken() )
        if kind == 'album':
            entries = self.folderEntries( [gql.album(n) for n in found], self.ALBUM_FOLDER )
        else:
            entries = self.folderEntries( [gql.playlist(n) for n in found], {'mode': 'lookup', 'isList': True} )
        return self.nextPage( entries, cursor ), 'albums'

    def listing( self, title, asin, image ):
        """The data of a folder that is neither an album, a playlist nor an artist"""
        return {'asin': asin, 'title': title, 'image': self.imageUrl(image), 'isPrime': True}

    def genreFolders( self, nodes ):
        return self.folderEntries( [self.listing(n.get('name'), n['id'], 'genres.jpg') for n in nodes],
                                   {'mode': 'getGenre', 'isList': True} )

    def gqlGenres( self, g ):
        return self.genreFolders( g.genres() ), 'albums'

    def gqlGenre( self, g, gid ):
        """The shelves of a genre, as folders"""
        shelves, cursor = g.genreShelves( gid, self.pageToken() )
        entries = self.folderEntries( [self.listing(n.get('name'), n['id'], 'genres.jpg') for n in shelves],
                                      {'mode': 'getGenreShelf', 'isList': True} )
        return self.nextPage( entries, cursor, gid ), 'albums'

    def gqlGenreShelf( self, g, sid ):
        """What a shelf of a genre holds: playlists, albums and further genres"""
        found, cursor = g.recommender( sid, self.pageToken() )
        entries = []
        for node in found:
            kind = node.get('__typename')
            if kind == 'Album':
                entries += self.folderEntries( [gql.album(node)], self.ALBUM_FOLDER )
            elif kind == 'Playlist':
                entries += self.folderEntries( [gql.playlist(node)], {'mode': 'lookup', 'isList': True} )
            elif kind == 'Category':
                entries += self.genreFolders( [node] )
        return self.nextPage( entries, cursor, sid ), 'albums'

    def gqlStations( self, g ):
        stations = [self.listing(n.get('name'), n['id'], 'stations.jpg') for n in g.stations()]
        return self.folderEntries( stations, {'mode': 'getStation', 'isList': True} ), 'albums'

    def gqlStation( self, g, sid ):
        """The songs a radio station plays next; the next page is a new queue"""
        itemlist = []
        songs = [{'asin': n['id'], 'duration': n.get('duration'), 'isPrime': True} for n in g.stationSongs(sid)]
        self.appendCatalogueSongs( itemlist, songs )
        itemlist.append( self._i.setPaginator('more', None, sid) )
        return itemlist, 'songs'

    def gqlRecommended( self, g, typename ):
        """
        The playlists or albums on the shelves of the start page
        :param str typename: Playlist or Album
        """
        seen, found = set(), []
        for shelf in g.homeRecommendations():
            for node in shelf:
                if node.get('__typename') == typename and node['id'] not in seen:
                    seen.add(node['id'])
                    found.append(node)
        if typename == 'Album':
            return self.folderEntries( [gql.album(n) for n in found], self.ALBUM_FOLDER ), 'albums'
        return self.folderEntries( [gql.playlist(n) for n in found], {'mode': 'lookup', 'isList': True} ), 'albums'

    def gqlArtist( self, g, asin ):
        albums, cursor = g.artistAlbums( asin, self.pageToken() )
        if albums or self.pageToken():
            entries = self.folderEntries( [gql.album(n) for n in albums], self.ALBUM_FOLDER )
            return self.nextPage( entries, cursor, asin ), 'albums'
        # Without an album of its own an artist still has songs, on the albums of others.
        return self.songEntries( g.artistTracks(asin) ), 'songs'

    def gqlLookup( self, g, asin ):
        album = g.album( asin )
        if album:
            return self.songEntries( gql.nodes(album.get('tracksConnection')), album ), 'songs'
        return self.gqlPlaylistTracks( found(g.playlist(asin)) ), 'songs'

    def gqlPlaylistTracks( self, playlist ):
        if (playlist.get('tracks') or {}).get('pageInfo', {}).get('hasNextPage'):
            self.log('The playlist has more than {} songs; the rest is not listed'.format(gql.AMgql.PLAYLIST_TRACKS))
        return self.songEntries( gql.nodes(playlist.get('tracks')) )

    def gqlPlaylists( self, g, followed ):
        if followed:
            found, cursor = g.followedPlaylists( self.pageToken() )
            entries = self.folderEntries( [gql.playlist(n) for n in found], {'mode': 'lookup', 'isList': True} )
            return self.nextPage( entries, cursor ), 'albums'
        own, follows = g.libraryPlaylists()
        return self.folderEntries( [gql.playlist(n) for n in own], {'mode': 'getPlaylistsByIdV2', 'isList': True} ), 'albums'

    def gqlLibrary( self, g, kind ):
        """
        :param str kind: songs, purchased, albums or artists
        """
        items, cursor = g.libraryPage( kind, self.pageToken() )
        if kind in ('songs', 'purchased'):
            return self.nextPage( self.songEntries(items), cursor ), 'songs'
        if kind == 'albums':
            return self.nextPage( self.folderEntries([gql.album(n) for n in items], self.ALBUM_FOLDER), cursor ), 'albums'
        entries = self.folderEntries( [gql.artist(n) for n in items], {'mode': 'getArtistDetails', 'isList': True} )
        return self.nextPage( entries, cursor ), 'artists'

    # What Amazon answered, by the kind of list the add-on asked for, and the function that
    # turns the answer into the entries of a Kodi list.
    LISTS = {
        'recentlyaddedsongs':    'listLibrarySongs',
        'purchasedalbums':       'listLibraryAlbums',
    }

    def setAddonContent( self, mode, param, ctype, stype=None, query=None ):
        """
        Generic function for data collection and mapping to ensure proper Kodi visualization
        :param str mode:    addon request mode
        :param array param: data response array
        :param str ctype:   content type - Albums, Songs
        :param str stype:   search type - Albums, Tracks, Artists
        :param str query:   sarch query string
        """
        itemlist = getattr( self, self.LISTS[mode] )( mode, param, stype, query )
        self.finalizeContent( self.G['addonHandle'], itemlist, ctype )

    def listLibrarySongs( self, mode, param, stype, query ):
        """Songs of the personal library"""
        itemlist = []
        # The library does not say whether a title is streamed, the catalogue does.
        self.appendCatalogueSongs( itemlist, [item['metadata'] for item in param['resultList']] )
        itemlist.append( self._i.addPaginator(param.get('nextToken'),param['resultList']) )
        return itemlist

    def listLibraryAlbums( self, mode, param, stype, query ):
        """The albums that were bought"""
        itemlist = []
        albums = [item['metadata'] for item in param['resultList']]
        known = {i['asin']: i for i in self._c.amzCall('APIlookup','itemLookup',None,[a['albumAsin'] for a in albums],['fullAlbumDetails'])['albumList']}
        for item in sorted(albums, key=lambda x: x['sortAlbumName']):
            item['purchased'] = True
            inf, met = self._i.setData(item,{'mode':'lookup', 'isAlbumFolder':True, 'isAlbum':True})
            inf, met = self._i.update( inf, met, known.get(item['albumAsin']), isAlbum=True, isAlbumFolder=True, isList=True )
            url, li  = self._i.setItem(inf,met)
            if not met['isPlayable']:
                continue
            itemlist.append((url, li, True))
        itemlist.append( self._i.addPaginator(param.get('nextToken'),param['resultList']) )
        return itemlist

def found( item ):
    """The item, or GqlError when the catalogue has none of that id"""
    if not item:
        raise gql.GqlError('Nothing of that id')
    return item

def run():
    AmazonMedia().reqDispatch()
