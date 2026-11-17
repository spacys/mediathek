#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The GraphQL interface of the Amazon Music web player (gql.music.amazon.<tld>).

The web player sends no query text, only the name of a query, its variables and the
SHA-256 hash of the query it was built with. The hashes below were recorded from the web
player 1.0.11818.0 in November 2026; the one of playlistDetail stayed the same through an
update of the web player. A hash is the SHA-256 of the printed query document, so the server only knows the queries
its own web player was built with; should Amazon change one, its hash is no longer known
(PersistedQueryNotFound) and the list shows the error.

What a query answers is turned here into the item data the rest of the add-on knows
(see AMitem.setData), so the lists are built the same way whichever interface answered.
"""

import json
import uuid
import requests
import xbmc

from resources.lib.amzcall import AMcall


class GqlError(Exception):
    """A GraphQL query did not answer what the add-on can use"""


class AMgql( AMcall ):
    URL = 'https://gql.music.amazon.{}/'
    # The application id of the web player, the same for every customer
    API_KEY = 'amzn1.application.4ff5579ca2e3407aba989a1f5dbdaf69'
    HASHES = {
        'ArtistSummary':                '9abfdbd3cc8ef7e8c7466009b2b824fa97cfbd0819fbbecc355045a1711966c7',
        'ChronologicalAlbumsPage':      '21accd6e4c2fa6ad0a0323ee60eba50afa8a22ff8f581e9e4602e87508e3214a',
        'AlbumDetailPage':              '45c44e542819fda01fef81c79814f2eb98d548fbfed68631ac38bd55afda36de',
        'playlistDetail':               'ed7a9eb147b6e58f9e1f97ceff215ed64fc19524b8133cf0e29f621d7901d7a5',
        'LibraryHomePage':              '8fbb66318689a88a64e1e0b7699cbcdb5cc63c0836b114557a3f3bf6dcbe17e8',
        'LikedSongsPage':               '7817afff6a4e91b678d6ac2b821255acc230f8745d05493999edd01436b42f32',
        'LikedAlbumsPage':              'ac0f3868a56af3b23191e0f173701c3bf0ffa71df79001cfbc9d00dcd144cc97',
        'LibraryArtistsPage':           '23525956998ec205f891c5949bd118f9833dd33500c9f82f2566b7b38a89b012',
        'MusicHomePage':                '49a8711ccff9b2e050c25196b1295427fde068cfeb538eeb23abf287df0e6bf3',
        'RecommenderSeeMorePage':       'a4cf0f3baa18092966315d29045ff365c2fc4e9b15252c664a386a47ce9a0a2a',
        'SpecSearchSeeMorePage':        '470a4cfc5b48502890dc4a7dfbc5f1e0201f1fe8aa06424b91c9311e2c24ee9d',
        'FollowedPlaylistsPagePage':    'c0ad67804cbb6947455430dc45605d70596519006097f6942b1b821554f01134',
        'genreCollections':             'bf65faad8f31f422a13a837a8efb5ad409b074e32c1436d85bc028248d63e7f0',
        'getStations':                  '1beef0ea6eccb6e297dbfd37232eee7dc567478701c6c201a0f336a29aaebad8',
        'CreateRemoteQueue':            'ce53397897c6a286f02a4da8a869fb8d0033e930c058796a6b2a16543e555512',
        'LibraryPurchasedPageQuery':    '5d7705c2ee5fc52f598f745f00b2698b77fd50d7e65b7ccc3584ff04cfd96b56'
    }
    # What the search answers to "show all", by kind
    SEARCH_TYPES = {'Songs': 'track', 'Albums': 'album', 'PlayLists': 'playlist', 'Artists': 'artist'}
    MORE_PAGE = 30
    SEE_MORE_PAGE = 20
    FOLLOWED_PAGE = 100
    HOME_SHELF_ITEMS = 15
    GENRE_SHELVES, GENRE_SHELF_ITEMS = 20, 10
    STATIONS = 20
    # The web player asks for no more than ten songs after the first of a station
    STATION_SONGS = 10
    # Page sizes as the web player asks for them
    SONGS_PAGE, ALBUMS_PAGE, ARTISTS_PAGE, RELEASES_PAGE = 50, 30, 30, 20
    PLAYLIST_TRACKS = 500
    PLAYLISTS = 50
    TOP_TRACKS = 25
    # The station the library page of the web player asks about along with it
    MY_SOUNDTRACK = 'A1ESXGJW9GSMCX'

    def query( self, name, variables ):
        """
        Ask one query of the web player
        :param str name:        name of the query, a key of HASHES
        :param dict variables:  its variables
        :return: the data of the answer
        :raises GqlError: Amazon answered with an error or without data
        """
        if not self.signedIn:
            self.credentials = self.load()
            self.signedIn = True
        body = json.dumps({
            'operationName':    name,
            'variables':        variables,
            'extensions':       {'persistedQuery': {'version': 1, 'sha256Hash': self.HASHES[name]}}
        })
        url = self.URL.format( self.credentials.USERTLD )
        resp = requests.post( url=url, headers=self.gqlHeaders(), data=body,
                              cookies=self.credentials.COOKIE, timeout=self.TIMEOUT )
        if resp.status_code in (401, 403) and self.renewTokens():
            resp = requests.post( url=url, headers=self.gqlHeaders(), data=body,
                                  cookies=self.credentials.COOKIE, timeout=self.TIMEOUT )
        if self.G['logging']:
            self.log('GraphQL {}: {} {}'.format(name, resp.status_code, resp.reason))
            self.log(resp.text)
        try:
            answer = json.loads(resp.text)
        except ValueError:
            raise GqlError('{} answered {} without JSON'.format(name, resp.status_code))
        errors = [str(e.get('message', e))[:200] for e in answer.get('errors') or []]
        # Amazon answers 294 when part of a page is missing (a playlist of a shelf that is gone) and still sends the rest.
        if resp.status_code >= 400 or not answer.get('data'):
            raise GqlError('{} answered {}: {}'.format(name, resp.status_code, '; '.join(errors) or resp.text[:200]))
        if errors:
            # Part of the answer may be missing; what is there is used.
            self.log('GraphQL {} answered with errors: {}'.format(name, '; '.join(errors)), xbmc.LOGWARNING)
        return answer['data']

    def gqlHeaders( self ):
        """
        The headers the web player sends to its GraphQL interface. It signs in by the cookies.
        """
        language = (self.credentials.LOCALE or 'de_DE').replace('_', '-')
        site = self.musicURL.format( self.credentials.USERTLD )
        return {
            'Content-Type':                     'application/json',
            'Accept':                           'application/graphql-response+json, application/json',
            'x-api-key':                        self.API_KEY,
            'x-amzn-device-id':                 self.credentials.DEVICEID,
            'x-amzn-device-type':               self.credentials.DEVICETYPE,
            'x-amzn-session-id':                self.sessionId(),
            'music-territory':                  self.credentials.MUSICTERRITORY,
            'X-AMZN-CLIENT-SUBSCRIPTION-TIER':  self.credentials.ACCESSTYPE or 'PRIME',
            'x-amzn-feature-flags':             'api-cache',
            'csrf-token':                       self.credentials.CSRF_TOKEN,
            'csrf-rnd':                         self.credentials.CSRF_RND,
            'csrf-ts':                          self.credentials.CSRF_TS,
            'Content-Language':                 language,
            'Accept-Language':                  language,
            'Origin':                           site,
            'Referer':                          site + '/',
            'User-Agent':                       self.userAgent
        }

    def sessionId( self ):
        """
        The session the web player names: the one of its session-id cookie
        """
        for cookie in self.credentials.COOKIE:
            if cookie.name == 'session-id':
                return cookie.value
        return ''

    # The queries, each with the variables the web player sends

    def artistAlbums( self, asin, cursor=None ):
        """The albums of an artist, newest first, and the cursor of the next page"""
        variables = {'id': asin, 'firstLimit': self.RELEASES_PAGE, 'isAuthenticated': True}
        if cursor:
            variables['afterCursor'] = cursor
        releases = self.query('ChronologicalAlbumsPage', variables)['artist']['releases']
        return nodes(releases), nextCursor(releases)

    def artistTracks( self, asin ):
        """The most popular songs of an artist"""
        variables = {
            'id': asin, 'limit': self.TOP_TRACKS, 'isAuthenticated': True, 'includeMerch': False,
            'includeVideos': False, 'audiobooksEnabled': True, 'merchEnabled': False,
            'categoryInEntityUnionEnabled': False
        }
        for key, part in (('latestSongsId', 'latest-songs'), ('appearsOnId', 'collaborated-songs'),
                          ('highlightsId', 'highlights'), ('relatedPlaylistsId', 'related-playlists'),
                          ('relatedPodcastsId', 'related-podcasts'), ('topAlbumsId', 'top-albums'),
                          ('relatedArtistsId', 'related-artists'), ('relatedStationsId', 'related-stations'),
                          ('allAccessSongsId', 'all-access-songs')):
            variables[key] = 'uri:///artist/{}/{}'.format(asin, part)
        return nodes(self.query('ArtistSummary', variables)['artist']['tracks'])

    def album( self, asin ):
        """An album with its songs, None if the catalogue has no album of that id"""
        return self.query('AlbumDetailPage', {
            'id': asin, 'isAuthenticated': True, 'includeMerch': False, 'includeAlbumAbout': False
        }).get('album')

    def playlist( self, asin ):
        """A playlist with its songs, None if there is none of that id"""
        return self.query('playlistDetail', {
            'id': asin, 'firstLimit': self.PLAYLIST_TRACKS, 'isAuthenticated': True, 'includeCollaborators': False
        }).get('playlist')

    def searchMore( self, kind, text, cursor=None ):
        """The results of a search, and the cursor of the next page"""
        variables = {
            'searchText': text, 'specType': self.SEARCH_TYPES[kind], 'firstLimit': self.MORE_PAGE,
            'isAuthenticated': True, 'audiobooksEnabled': True, 'merchEnabled': False,
            'categoryInEntityUnionEnabled': False
        }
        if cursor:
            variables['afterCursor'] = cursor
        results = (self.query('SpecSearchSeeMorePage', variables).get('specificationSearch') or {}).get('result') or []
        return (nodes(results[0]), nextCursor(results[0])) if results else ([], None)

    def recommender( self, rid, cursor=None ):
        """
        The entries of a list of recommendations, charts or new releases, and the cursor of the next page
        :param str rid: id of the list, for instance uri:///popular/top-albums
        """
        variables = {
            'id': rid, 'firstLimit': self.SEE_MORE_PAGE, 'isAuthenticated': True, 'audiobooksEnabled': True,
            'merchEnabled': False, 'categoryInEntityUnionEnabled': False
        }
        if cursor:
            variables['afterCursor'] = cursor
        edges = ((self.query('RecommenderSeeMorePage', variables).get('recommender') or {}).get('edges') or [])
        content = ((edges[0] or {}).get('node') or {}).get('recommendedContent') if edges else None
        return nodes(content), nextCursor(content)

    def homePage( self ):
        """The music start page of the web player: the shelves of recommendations and the genres"""
        return self.query('MusicHomePage', {
            'firstLimit': 5, 'recommenderItemLimit': self.HOME_SHELF_ITEMS, 'type': 'music-home',
            'topRecommenderId': 'musicTopOneRecommender', 'isAuthenticated': True, 'audiobooksEnabled': True,
            'merchEnabled': False, 'categoryInEntityUnionEnabled': False, 'paginating': False
        })

    def homeRecommendations( self ):
        """The entries of the shelves of the music start page"""
        shelves = nodes((self.homePage().get('browse') or {}).get('recommendationConnection'))
        return [nodes(shelf.get('recommendedContent')) for shelf in shelves]

    def genres( self ):
        """The genres, moods and activities the start page lists"""
        found, seen = [], set()
        for group in self.homePage().get('genres') or []:
            for node in nodes((group or {}).get('recommendedContent')):
                # The groups hold links to the charts, the playlists and the radio too.
                if '/genres/' in (node.get('url') or '') and node['id'] not in seen:
                    seen.add(node['id'])
                    found.append(node)
        return found

    def genreShelves( self, gid, cursor=None ):
        """The shelves of a genre, each with its name, and the cursor of the next page"""
        variables = {
            'type': 'category', 'firstLimit': self.GENRE_SHELVES, 'itemLimit': self.GENRE_SHELF_ITEMS, 'targets': [gid],
            'isAuthenticated': True, 'audiobooksEnabled': False, 'merchEnabled': False, 'categoryInEntityUnionEnabled': False
        }
        if cursor:
            variables['afterCursor'] = cursor
        connection = (self.query('genreCollections', variables).get('recommendationCollection') or {}).get('recommendationConnection')
        return [shelf for shelf in nodes(connection) if nodes(shelf.get('recommendedContent'))], nextCursor(connection)

    def stations( self ):
        """The radio stations: those made for the customer, then those of everybody"""
        data = self.query('getStations', {'limit': self.STATIONS})
        found, seen = [], set()
        for connection in ((data.get('user') or {}).get('topStations'), data.get('topStations')):
            for node in nodes(connection):
                if node['id'] not in seen:
                    seen.add(node['id'])
                    found.append(node)
        return found

    def stationSongs( self, sid ):
        """
        The first songs of a queue of a radio station. Every call starts a new queue, with songs of its own.
        :param str sid: id of the station
        """
        data = self.query('CreateRemoteQueue', {
            'id': 'mrn:1.0:catalog:station:key:' + sid, 'containerIds': [], 'nextLimit': self.STATION_SONGS,
            'queueId': str(uuid.uuid4()), 'drmType': 'WIDEVINE', 'format': 'ENCRYPTED_OPUS_FLAC',
            'audioCapability': ['HI_RES', 'HI_FI', 'STD_RES']
        })
        queue = (data.get('createQueue') or {}).get('queue') or {}
        return nodes(queue.get('current')) + nodes(queue.get('next'))

    def followedPlaylists( self, cursor=None ):
        """The playlists the customer follows and the cursor of the next page"""
        variables = {'firstLimit': self.FOLLOWED_PAGE}
        if cursor:
            variables['afterCursor'] = cursor
        connection = (self.query('FollowedPlaylistsPagePage', variables).get('user') or {}).get('followedPlaylists')
        return nodes(connection), nextCursor(connection)

    def libraryPlaylists( self ):
        """The playlists of the customer and those followed"""
        user = self.query('LibraryHomePage', {
            'isAuthenticated': True, 'limit': self.PLAYLISTS, 'mySoundtrackStationAsin': self.MY_SOUNDTRACK
        })['user']
        return nodes(user.get('playlists')), nodes(user.get('followedPlaylists'))

    def libraryPage( self, kind, cursor=None ):
        """
        A page of the library and the cursor of the next one
        :param str kind: songs, purchased, albums or artists
        """
        name, field, size, extra = {
            'songs':        ('LikedSongsPage', 'tracks', self.SONGS_PAGE, {'sortBy': 'name'}),
            'purchased':    ('LibraryPurchasedPageQuery', 'purchased', self.SONGS_PAGE, {}),
            'albums':       ('LikedAlbumsPage', 'likedAlbums', self.ALBUMS_PAGE, {}),
            'artists':      ('LibraryArtistsPage', 'likedArtists', self.ARTISTS_PAGE, {})
        }[kind]
        variables = dict({'firstLimit': size, 'isAuthenticated': True}, **extra)
        if cursor:
            variables['afterCursor'] = cursor
        connection = self.query(name, variables)['user'][field]
        return nodes(connection), nextCursor(connection)


def nodes( connection ):
    """The entries of a connection, without the empty ones Amazon hands over for songs it no longer has"""
    return [edge['node'] for edge in (connection or {}).get('edges') or [] if edge and edge.get('node')]


def nextCursor( connection ):
    """The cursor of the next page, None on the last one"""
    page = (connection or {}).get('pageInfo') or {}
    return page.get('token') or page.get('endCursor') if page.get('hasNextPage') else None


def image( item, prefer=('PRIMARY', None) ):
    """The address of the image of the preferred type, else of the first"""
    images = [i for i in item.get('images') or [] if i and i.get('url')]
    for kind in prefer:
        for i in images:
            if i.get('imageType') == kind:
                return i['url']
    return images[0]['url'] if images else None


def artists( item ):
    """The names of the primary artists, else of all who took part"""
    edges = [e for e in ((item.get('contributingArtists') or {}).get('edges') or []) if e and e.get('node')]
    primary = [e['node']['name'] for e in edges if e.get('role') == 'PRIMARY'] or [e['node']['name'] for e in edges]
    if primary:
        return ', '.join(primary)
    return (item.get('album') or {}).get('artistNames')


def track( node, album=None ):
    """
    A song as the item data of the add-on
    :param dict album: the album the song is listed in, for its title, cover and year
    """
    purchase = node.get('purchaseContext') or {}
    item = {
        'asin':         node['id'],
        'title':        node.get('title') or node.get('shortTitle'),
        'duration':     node.get('duration'),
        'artistName':   artists(node) or (artists(album) if album else None),
        'albumName':    (node.get('album') or {}).get('shortTitle') or (album or {}).get('title'),
        'image':        image(node) or (image(album) if album else None),
        # Amazon streams its catalogue to a Prime account as to a subscription.
        'isPrime':      True,
        'purchased':    bool(purchase.get('isPurchased'))
    }
    if node.get('trackNumber') is not None:
        item['trackNum'] = node['trackNumber']
    if purchase.get('isPurchased') and purchase.get('id'):
        # The id of the song in the library: what was bought is streamed without DRM.
        item['objectId'] = purchase['id']
    if album and album.get('releaseDate'):
        item['albumReleaseDate'] = album['releaseDate']
    return dropNone(item)


def album( node ):
    """An album as the item data of the add-on"""
    item = {
        'asin':         node['id'],
        'title':        node.get('title') or node.get('shortTitle'),
        'artistName':   artists(node),
        'image':        image(node),
        'trackCount':   node.get('trackCount'),
        'duration':     node.get('duration'),
        'albumReleaseDate': node.get('releaseDate'),
        'isPrime':      True
    }
    return dropNone(item)


def playlist( node ):
    """A playlist as the item data of the add-on"""
    item = {
        'asin':         node['id'],
        'title':        node.get('title'),
        'image':        image(node),
        'trackCount':   node.get('trackCount'),
        'duration':     node.get('duration'),
        'isPrime':      True
    }
    curator = (node.get('curator') or {}).get('name')
    if curator:
        item['artistName'] = curator
    return dropNone(item)


def artist( node ):
    """An artist as the item data of the add-on"""
    item = {
        'asin':         node['id'],
        'title':        node.get('name'),
        'image':        image(node, ('PRIMARY', 'BACKGROUND', None)),
        'bannerImage':  image(node, ('BACKGROUND',)) if any(i.get('imageType') == 'BACKGROUND' for i in node.get('images') or [] if i) else None,
        'isPrime':      True
    }
    return dropNone(item)


def dropNone( item ):
    return {k: v for k, v in item.items() if v is not None}
