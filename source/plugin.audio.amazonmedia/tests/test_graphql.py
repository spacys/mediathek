"""The GraphQL interface of the web player: what is asked, and how the answers become lists.

The answers follow what the web player 1.0.11818.0 got in November 2026, cut down to
the fields the add-on reads.
"""

import json
import unittest
from http.cookiejar import Cookie
from urllib.parse import parse_qs, urlparse

from .support import AddonTest, Kodi, Response, clicked, invoke, signed_in, text, xbmc
from resources.lib import gql
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.main import AmazonMedia
from resources.lib.tools import AMtools

ARTIST = {'role': 'PRIMARY', 'node': {'id': 'B001T0YOF2', 'name': 'Coldplay'}}
COVER = [{'url': 'https://m.media-amazon.com/images/I/cover.jpg', 'imageType': 'PRIMARY', 'width': 1400}]


def song(asin, title, purchased=None, number=1):
    return {'id': asin, 'title': title, 'shortTitle': title, 'duration': 223, 'trackNumber': number,
            'images': COVER, 'contributingArtists': {'edges': [ARTIST]},
            'album': {'id': 'B0FMYTYHQR', 'shortTitle': 'ALL MY LOVE'},
            'purchaseContext': {'isPurchased': bool(purchased), 'id': purchased}}


def connection(*nodes, token=None):
    return {'edges': [{'node': node} for node in nodes],
            'pageInfo': {'hasNextPage': bool(token), 'token': token, 'endCursor': None}}


ALBUM = {'id': 'B0FMYTYHQR', 'title': 'ALL MY LOVE', 'shortTitle': 'ALL MY LOVE', 'images': COVER,
         'contributingArtists': {'edges': [ARTIST]}, 'releaseDate': '2025-08-22T00:00:00.000Z',
         'trackCount': 2, 'duration': 664}
PLAYLIST = {'id': 'B00ZS0A5GQ', 'title': 'Pop-Balladen', 'images': COVER, 'trackCount': 67, 'duration': 15177,
            'curator': {'name': 'Amazon Music'}}
CURSOR = 'tcs-V1_o9M9IU3gY1b8+i4/KiAg=='
# The query itself, before the tests replace it
QUERY = gql.AMgql.query


class Interface(AddonTest):
    """One query as the web player sends it."""

    def ask(self, *answers):
        invoke('mode=getAllSongs')
        self.patch(gql.AMgql, 'query', QUERY)
        stored = signed_in(AMaccess())
        stored.COOKIE.set_cookie(Cookie(0, 'session-id', '262-1234567-7654321', None, False, '.amazon.de', True, True,
                                        '/', True, True, None, False, None, None, {}))
        self.addCleanup(stored.COOKIE.clear)
        self.patch(AMtools, 'load', lambda tools: stored)
        posted = self.patch(gql.requests, 'post', side_effect=list(answers))
        return gql.AMgql(), posted

    def test_the_query_goes_by_its_name_variables_and_hash_without_its_text(self):
        g, posted = self.ask(Response({'data': {'album': ALBUM}}))
        self.assertEqual(g.album('B0FMYTYHQR'), ALBUM)
        sent = posted.call_args.kwargs
        self.assertEqual(sent['url'], 'https://gql.music.amazon.de/')
        self.assertEqual(json.loads(sent['data']), {
            'operationName': 'AlbumDetailPage',
            'variables': {'id': 'B0FMYTYHQR', 'isAuthenticated': True, 'includeMerch': False, 'includeAlbumAbout': False},
            'extensions': {'persistedQuery': {'version': 1, 'sha256Hash': gql.AMgql.HASHES['AlbumDetailPage']}}})
        self.assertEqual(sent['timeout'], (10, 30))

    def test_it_signs_in_by_the_cookies_and_the_csrf_tokens_as_the_web_player_does(self):
        g, posted = self.ask(Response({'data': {'album': ALBUM}}))
        g.album('B0FMYTYHQR')
        head = posted.call_args.kwargs['headers']
        self.assertEqual((head['x-api-key'], head['x-amzn-device-id'], head['x-amzn-device-type'], head['x-amzn-session-id']),
                         ('amzn1.application.4ff5579ca2e3407aba989a1f5dbdaf69', 'device-id', 'device-type', '262-1234567-7654321'))
        self.assertEqual((head['csrf-token'], head['csrf-rnd'], head['csrf-ts']), ('csrf', '2', '1'))
        self.assertEqual((head['music-territory'], head['X-AMZN-CLIENT-SUBSCRIPTION-TIER'], head['Accept-Language']), ('DE', 'PRIME', 'de-DE'))
        self.assertNotIn('Authorization', head)
        self.assertIn('session-id', [c.name for c in posted.call_args.kwargs['cookies']])

    def test_a_query_amazon_no_longer_knows_is_an_error(self):
        g, posted = self.ask(Response({'errors': [{'message': 'PersistedQueryNotFound'}], 'data': None}))
        with self.assertRaisesRegex(gql.GqlError, 'PersistedQueryNotFound'):
            g.album('B0FMYTYHQR')

    def test_an_answer_with_errors_and_a_status_of_294_still_gives_its_data(self):
        g, posted = self.ask(Response({'data': {'album': ALBUM}, 'errors': [{'message': 'PlaylistId x was not found.'}]}, 294))
        self.assertEqual(g.album('B0FMYTYHQR'), ALBUM)

    def test_an_answer_that_is_no_json_is_an_error(self):
        g, posted = self.ask(Response('<html>Service Unavailable</html>', 503))
        with self.assertRaises(gql.GqlError):
            g.album('B0FMYTYHQR')

    def test_refused_csrf_tokens_are_renewed_once(self):
        g, posted = self.ask(Response({'message': 'Forbidden'}, 403), Response({'data': {'album': ALBUM}}))
        renewed = self.patch(AMcall, 'renewTokens', return_value=True)
        self.assertEqual(g.album('B0FMYTYHQR'), ALBUM)
        self.assertEqual((renewed.call_count, posted.call_count), (1, 2))

    def test_a_page_after_the_first_names_the_cursor_of_the_previous_one(self):
        g, posted = self.ask(Response({'data': {'user': {'purchased': connection(song('B0C5S721BJ', 'Lighthouse'), token='next')}}}))
        songs, cursor = g.libraryPage('purchased', CURSOR)
        self.assertEqual(json.loads(posted.call_args.kwargs['data'])['variables'],
                         {'firstLimit': 50, 'isAuthenticated': True, 'afterCursor': CURSOR})
        self.assertEqual((len(songs), cursor), (1, 'next'))


class Items(unittest.TestCase):
    """The answers as the item data the lists are built from."""

    def test_a_bought_song_carries_its_library_id_and_plays_without_drm(self):
        item = gql.track(song('B0C5S721BJ', 'Lighthouse', 'e4b679f9-7fd2-411a-a225-607f0fd27c6a', 5))
        self.assertEqual(item, {'asin': 'B0C5S721BJ', 'title': 'Lighthouse', 'duration': 223, 'artistName': 'Coldplay',
                                'albumName': 'ALL MY LOVE', 'image': COVER[0]['url'], 'isPrime': True, 'purchased': True,
                                'trackNum': 5, 'objectId': 'e4b679f9-7fd2-411a-a225-607f0fd27c6a'})

    def test_a_song_of_the_catalogue_has_no_library_id(self):
        item = gql.track(song('B0FMYV292H', 'ALL MY LOVE'))
        self.assertNotIn('objectId', item)
        self.assertFalse(item['purchased'])

    def test_an_album_a_playlist_and_an_artist(self):
        self.assertEqual(gql.album(ALBUM)['albumReleaseDate'][:4], '2025')
        self.assertEqual(gql.playlist(PLAYLIST), {'asin': 'B00ZS0A5GQ', 'title': 'Pop-Balladen', 'image': COVER[0]['url'],
                                                   'trackCount': 67, 'duration': 15177, 'isPrime': True, 'artistName': 'Amazon Music'})
        background = {'url': 'https://m.media-amazon.com/images/I/back.jpg', 'imageType': 'BACKGROUND'}
        self.assertEqual(gql.artist({'id': 'B001SYQJP2', 'name': 'Natalia Lafourcade', 'images': [background]}),
                         {'asin': 'B001SYQJP2', 'title': 'Natalia Lafourcade', 'image': background['url'],
                          'bannerImage': background['url'], 'isPrime': True})

    def test_an_empty_entry_of_a_list_is_left_out(self):
        self.assertEqual(gql.nodes({'edges': [{'node': None}, None, {'node': {'id': 'B0'}}]}), [{'id': 'B0'}])


class Lists(AddonTest):
    """Each list asks its query; what Amazon answers is listed as before."""

    def answer(self, query, answers):
        invoke(query)
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.gql.side_effect = lambda name, variables: answers[name](variables) if callable(answers[name]) else answers[name]
        old = self.patch(AMcall, 'amzCall', side_effect=AssertionError('the older interface is not asked'))
        AmazonMedia().reqDispatch()
        return [(li.label, folder) for url, li, folder in Kodi.items], old

    def asked(self, name):
        return [call.args[1] for call in self.gql.call_args_list if call.args[0] == name]

    def test_a_search_for_songs(self):
        found = {'specificationSearch': {'result': [connection(song('B07VX8C9LN', 'Viva La Vida'))]}}
        labels, old = self.answer('mode=searchSongs&query=Coldplay', {'SpecSearchSeeMorePage': found})
        self.assertEqual(labels, [('Viva La Vida', False)])
        self.assertEqual(self.asked('SpecSearchSeeMorePage')[0], {
            'searchText': 'Coldplay', 'specType': 'track', 'firstLimit': 30, 'isAuthenticated': True,
            'audiobooksEnabled': True, 'merchEnabled': False, 'categoryInEntityUnionEnabled': False})
        self.assertEqual(AMtools().searchHistory('Songs'), ['Coldplay'])

    def test_a_search_pages_on_without_entering_the_history_again(self):
        found = {'specificationSearch': {'result': [connection(song('B07VX8C9LN', 'Viva La Vida'), token=CURSOR)]}}
        self.answer('mode=searchSongs&query=Coldplay', {'SpecSearchSeeMorePage': found})
        next_page = Kodi.items[-1][0]
        self.assertEqual(parse_qs(urlparse(next_page).query)['query'], ['Coldplay'])
        del Kodi.items[:]
        self.answer(clicked(next_page), {'SpecSearchSeeMorePage': {'specificationSearch': {'result': [connection(song('B0FMYV292H', 'Yellow'))]}}})
        self.assertEqual(self.asked('SpecSearchSeeMorePage')[-1]['afterCursor'], CURSOR)
        self.assertEqual(AMtools().searchHistory('Songs'), ['Coldplay'])

    def test_a_search_for_artists_opens_an_artist(self):
        found = {'specificationSearch': {'result': [connection({'id': 'B001T0YOF2', 'name': 'Coldplay', 'images': COVER})]}}
        self.answer('mode=searchArtist&query=Coldplay', {'SpecSearchSeeMorePage': found})
        url = Kodi.items[0][0]
        self.assertEqual(parse_qs(urlparse(url).query)['mode'], ['getArtistDetails'])
        self.assertEqual(self.asked('SpecSearchSeeMorePage')[0]['specType'], 'artist')

    def test_the_albums_of_an_artist_page_on_with_their_cursor(self):
        page = {'artist': {'releases': connection(ALBUM, token=CURSOR)}}
        labels, old = self.answer('mode=getArtistDetails&asin=B001T0YOF2', {'ChronologicalAlbumsPage': page})
        self.assertIn('ALL MY LOVE', labels[0][0])
        next_page = Kodi.items[-1][0]
        del Kodi.items[:]
        self.answer(clicked(next_page), {'ChronologicalAlbumsPage': {'artist': {'releases': connection(ALBUM)}}})
        self.assertEqual(self.asked('ChronologicalAlbumsPage')[-1],
                         {'id': 'B001T0YOF2', 'firstLimit': 20, 'isAuthenticated': True, 'afterCursor': CURSOR})

    def test_an_artist_without_albums_of_its_own_has_its_songs_listed(self):
        answers = {'ChronologicalAlbumsPage': {'artist': {'releases': connection()}},
                   'ArtistSummary': {'artist': {'tracks': connection(song('B07VX8C9LN', 'Viva La Vida'))}}}
        labels, old = self.answer('mode=getArtistDetails&asin=B001T0YOF2', answers)
        self.assertEqual(labels, [('Viva La Vida', False)])
        self.assertEqual(self.asked('ArtistSummary')[0]['topAlbumsId'], 'uri:///artist/B001T0YOF2/top-albums')

    def test_an_album_lists_its_songs_under_its_title(self):
        album = dict(ALBUM, tracksConnection=connection(song('B0FMYV292H', 'ALL MY LOVE'), song('B0FMYV292J', 'ALIEN HITS', number=2)))
        labels, old = self.answer('mode=lookup&asin=B0FMYTYHQR', {'AlbumDetailPage': {'album': album}})
        self.assertEqual(labels, [('ALL MY LOVE', False), ('ALIEN HITS', False)])
        self.assertEqual(Kodi.items[0][1].info.get('album'), 'ALL MY LOVE')

    def test_what_is_no_album_is_looked_up_as_a_playlist(self):
        playlist = dict(PLAYLIST, tracks=connection(song('B085W5XDB3', 'Control'), None))
        labels, old = self.answer('mode=lookup&asin=B00ZS0A5GQ', {'AlbumDetailPage': {'album': None},
                                                                  'playlistDetail': {'playlist': playlist}})
        self.assertEqual(labels, [('Control', False)])

    def test_a_bought_song_of_the_library_plays_by_its_library_id(self):
        page = {'user': {'purchased': connection(song('B0C5S721BJ', 'Lighthouse', 'e4b679f9-7fd2-411a-a225-607f0fd27c6a'))}}
        labels, old = self.answer('mode=getPurSongs', {'LibraryPurchasedPageQuery': page})
        self.assertEqual(labels, [('[COLOR gold]Lighthouse[/COLOR]', False)])
        self.assertEqual(parse_qs(urlparse(Kodi.items[0][0]).query)['objectId'], ['e4b679f9-7fd2-411a-a225-607f0fd27c6a'])

    def test_the_artists_of_the_library_open_as_artists(self):
        page = {'user': {'likedArtists': connection({'id': 'B001SYQJP2', 'name': 'Natalia Lafourcade', 'images': []})}}
        self.answer('mode=getLibraryArtists', {'LibraryArtistsPage': page})
        self.assertEqual(parse_qs(urlparse(Kodi.items[0][0]).query)['mode'], ['getArtistDetails'])

    def test_own_playlists_open_their_songs(self):
        library = {'user': {'playlists': connection(dict(PLAYLIST, id='403e2aaa-1f30-49bd-bcb6-eef95da497ba', title='TEST-PlayList')),
                            'followedPlaylists': connection(PLAYLIST)}}
        self.answer('mode=getOwnedPlaylists', {'LibraryHomePage': library})
        self.assertEqual(parse_qs(urlparse(Kodi.items[0][0]).query)['mode'], ['getPlaylistsByIdV2'])

    def test_followed_playlists_page_on_beyond_those_of_the_library_page(self):
        page = {'user': {'followedPlaylists': connection(dict(PLAYLIST, title='Gute Laune'), PLAYLIST, token=CURSOR)}}
        labels, old = self.answer('mode=getFollowedPlayLists', {'FollowedPlaylistsPagePage': page})
        self.assertEqual([label.split('  (')[0] for label, folder in labels[:2]], ['Gute Laune', 'Pop-Balladen'])
        self.assertEqual(self.asked('FollowedPlaylistsPagePage')[0], {'firstLimit': 100})
        next_page = Kodi.items[-1][0]
        del Kodi.items[:]
        self.answer(clicked(next_page), {'FollowedPlaylistsPagePage': {'user': {'followedPlaylists': connection(PLAYLIST)}}})
        self.assertEqual(self.asked('FollowedPlaylistsPagePage')[-1], {'firstLimit': 100, 'afterCursor': CURSOR})

    def charted(self, query, nodes, token=None):
        content = connection(*nodes, token=token)
        return self.answer(query, {'RecommenderSeeMorePage': {'recommender': {'edges': [{'node': {'recommendedContent': content}}]}}})

    def test_the_charts_and_new_releases_ask_for_their_lists(self):
        for query, rid in (('getPopularPlayLists', 'uri:///popular/top-playlists'), ('getNewPlayLists', 'uri:///new/playlists'),
                           ('getPopularAlbums', 'uri:///popular/top-albums'), ('getNewAlbums', 'uri:///new/albums')):
            with self.subTest(query=query):
                self.gql.reset_mock()
                self.charted('mode=' + query, [])
                self.assertEqual(self.asked('RecommenderSeeMorePage')[0]['id'], rid)

    def test_charted_albums_and_playlists_open_and_page_on(self):
        labels, old = self.charted('mode=getPopularAlbums', [ALBUM], token=CURSOR)
        self.assertEqual(parse_qs(urlparse(Kodi.items[0][0]).query)['mode'], ['lookup'])
        next_page = Kodi.items[-1][0]
        del Kodi.items[:]
        self.charted(clicked(next_page), [ALBUM])
        self.assertEqual(self.asked('RecommenderSeeMorePage')[-1]['afterCursor'], CURSOR)
        del Kodi.items[:]
        labels, old = self.charted('mode=getNewPlayLists', [PLAYLIST])
        self.assertEqual(len(labels), 1)

    def test_the_recommendations_are_the_playlists_or_albums_of_the_shelves_of_the_start_page(self):
        station = {'__typename': 'Station', 'id': 'S1', 'title': 'A Station'}
        shelves = [{'recommendedContent': connection(dict(ALBUM, __typename='Album'), station, dict(PLAYLIST, __typename='Playlist'))},
                   {'recommendedContent': connection(dict(PLAYLIST, __typename='Playlist'), dict(ALBUM, id='B0OTHER', __typename='Album'))}]
        home = {'browse': {'recommendationConnection': connection(*shelves)}}
        labels, old = self.answer('mode=getRecomPlayLists', {'MusicHomePage': home})
        self.assertEqual(len(labels), 1)
        self.assertEqual(self.asked('MusicHomePage')[0]['type'], 'music-home')
        del Kodi.items[:]
        labels, old = self.answer('mode=getRecomAlbums', {'MusicHomePage': home})
        self.assertEqual(len(labels), 2)


class Browsing(AddonTest):
    """Genres and radio stations."""
    answer, asked, charted = Lists.answer, Lists.asked, Lists.charted

    HOME = {'genres': [
        {'id': '1|G|GROUPING_GENRE', 'recommendedContent': connection(
            {'id': 'kF5AsCSx', 'name': 'Pop & Deutscher Pop', 'url': 'https://music.amazon.de/genres/kF5AsCSx?ref=x'})},
        {'id': '1|G|GROUPING_LISTEN_YOUR_WAY', 'recommendedContent': connection(
            {'id': '1|C|CATEGORY_CHARTS', 'name': 'Charts', 'url': 'https://music.amazon.de/popular'},
            {'id': 'kF5AsCSx', 'name': 'Pop again', 'url': 'https://music.amazon.de/genres/kF5AsCSx'},
            {'id': 'mwXZ32AJ', 'name': 'Playlists on-demand', 'url': 'https://music.amazon.de/genres/mwXZ32AJ'})}]}

    def test_the_genres_are_those_of_the_start_page_that_open_a_genre(self):
        labels, old = self.answer('mode=getGenres', {'MusicHomePage': self.HOME})
        self.assertEqual([label for label, folder in labels], ['Pop & Deutscher Pop', 'Playlists on-demand'])
        url = Kodi.items[0][0]
        self.assertEqual(parse_qs(urlparse(url).query)['mode'], ['getGenre'])
        self.assertEqual(Kodi.items[0][1].art['icon'].rsplit('/', 1)[-1], 'genres.jpg')

    def test_a_genre_lists_its_shelves_and_a_shelf_its_playlists_albums_and_genres(self):
        shelf = {'id': 'uri:///category/kF5AsCSx/6f8a', 'name': 'Best of Deutschpop',
                 'recommendedContent': connection(dict(PLAYLIST, __typename='Playlist'))}
        empty = {'id': 'uri:///category/kF5AsCSx/0000', 'name': 'Empty', 'recommendedContent': connection()}
        page = {'recommendationCollection': {'recommendationConnection': connection(shelf, empty, token=CURSOR)}}
        labels, old = self.answer('mode=getGenre&asin=kF5AsCSx', {'genreCollections': page})
        self.assertEqual(labels[0], ('Best of Deutschpop', True))
        self.assertEqual(self.asked('genreCollections')[0]['targets'], ['kF5AsCSx'])
        self.assertEqual(len(labels), 2)     # the empty shelf is left out, the next page is offered
        shelf_url = Kodi.items[0][0]
        self.assertEqual(parse_qs(urlparse(shelf_url).query)['asin'], ['uri:///category/kF5AsCSx/6f8a'])
        del Kodi.items[:]
        content = [dict(PLAYLIST, __typename='Playlist'), dict(ALBUM, __typename='Album'),
                   {'__typename': 'Category', 'id': 'sub1', 'name': 'Deutschpop'}]
        self.charted(clicked(shelf_url), content)
        self.assertEqual(self.asked('RecommenderSeeMorePage')[0]['id'], 'uri:///category/kF5AsCSx/6f8a')
        self.assertEqual([parse_qs(urlparse(url).query)['mode'] for url, li, folder in Kodi.items],
                         [['lookup'], ['lookup'], ['getGenre']])

    STATIONS = {'user': {'topStations': connection({'id': 'A1L791OPWXY55I', 'name': 'Nena'})},
                'topStations': connection({'id': 'AUTF210RZQL6', 'name': 'Feeling Happy'}, {'id': 'A1L791OPWXY55I', 'name': 'Nena'})}

    def test_the_stations_are_those_made_for_the_customer_then_the_others(self):
        labels, old = self.answer('mode=getStations', {'getStations': self.STATIONS})
        self.assertEqual([label for label, folder in labels], ['Nena', 'Feeling Happy'])
        self.assertEqual(parse_qs(urlparse(Kodi.items[0][0]).query)['mode'], ['getStation'])
        self.assertEqual(Kodi.items[0][1].art['icon'].rsplit('/', 1)[-1], 'stations.jpg')

    def test_a_station_lists_the_songs_of_a_new_queue_and_offers_more(self):
        queue = {'createQueue': {'queue': {'current': connection({'id': 'B0BRYK1WQC', 'duration': 200}),
                                           'next': connection({'id': 'B08GYHGZTY', 'duration': 180}, token='t')}}}
        old = self.patch(AMcall, 'amzCall', side_effect=lambda api, mode, referer, asins, features: {'trackList': [
            {'asin': a, 'title': 'Song ' + a[-3:], 'isMusicSubscription': 'true'} for a in asins]})
        invoke('mode=getStation&asin=A1L791OPWXY55I')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.gql.side_effect = lambda name, variables: queue
        AmazonMedia().reqDispatch()
        asked = self.asked('CreateRemoteQueue')[0]
        self.assertEqual((asked['id'], asked['nextLimit']), ('mrn:1.0:catalog:station:key:A1L791OPWXY55I', 10))
        self.assertEqual([li.label for url, li, folder in Kodi.items[:2]], ['Song WQC', 'Song ZTY'])
        self.assertEqual([folder for url, li, folder in Kodi.items], [False, False, True])
        self.assertEqual(parse_qs(urlparse(Kodi.items[2][0]).query)['asin'], ['A1L791OPWXY55I'])


class Hashes(unittest.TestCase):
    def test_every_hash_is_a_sha256(self):
        for name, value in gql.AMgql.HASHES.items():
            with self.subTest(query=name):
                self.assertRegex(value, r'^[0-9a-f]{64}$')


class Failing(AddonTest):
    """The older interfaces are gone: a failed query is told, and nothing else is asked."""

    def test_a_failed_query_is_logged_and_the_user_told(self):
        invoke('mode=getPurSongs')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        old = self.patch(AMcall, 'amzCall', side_effect=AssertionError('the older interface is not asked'))
        AmazonMedia().reqDispatch()
        old.assert_not_called()
        self.assertTrue(any(level == xbmc.LOGERROR and 'not asked in this test' in message for level, message in Kodi.log))
        self.assertEqual(Kodi.notifications[-1]['message'], text(30077))
        self.assertEqual(Kodi.items, [])

    def test_bought_albums_come_from_the_library(self):
        invoke('mode=getPurAlbums')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        old = self.patch(AMcall, 'amzCall', return_value={'resultList': [], 'nextToken': None, 'albumList': []})
        AmazonMedia().reqDispatch()
        self.gql.assert_not_called()


if __name__ == '__main__':
    unittest.main()
