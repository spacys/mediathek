"""The path to the current folder, which the skin shows top left after the add-on name."""

import json
import os
import unittest
from urllib.parse import parse_qs, urlencode, urlparse

from .support import AddonTest, Kodi, clicked, invoke, signed_in
from .test_graphql import PLAYLIST as GQL_PLAYLIST, connection, song
from resources.lib.access import AMaccess
from resources.lib.item import AMitem
from resources.lib.main import AmazonMedia
from resources.lib.tools import AMtools


class Breadcrumb(AddonTest):
    def setUp(self):
        super().setUp()
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        # What the GraphQL interface answers: nothing is found, an artist has no more albums, a playlist is empty.
        self.found = connection()
        self.charted = connection()
        self.gql.side_effect = lambda name, variables: {
            'SpecSearchSeeMorePage':    {'specificationSearch': {'result': [self.found]}},
            'RecommenderSeeMorePage':   {'recommender': {'edges': [{'node': {'recommendedContent': self.charted}}]}},
            'AlbumDetailPage':          {'album': None},
            'playlistDetail':           {'playlist': dict(GQL_PLAYLIST, tracks=connection())},
            'ChronologicalAlbumsPage':  {'artist': {'releases': connection()}}
        }[name]

    def open(self, query):
        del Kodi.items[:]
        invoke(query)
        AmazonMedia().reqDispatch()
        return Kodi.category

    def follow(self, mode):
        """Open the listed folder of the given mode, as a click on it does."""
        for url, li, folder in list(Kodi.items):
            if parse_qs(urlparse(url).query).get('mode') == [mode]:
                return self.open(clicked(url))
        self.fail('nothing listed opens ' + mode)

    def test_the_main_menu_adds_nothing(self):
        self.assertEqual(self.open(''), '')

    def test_the_path_leads_down_to_a_playlist(self):
        self.open('')
        self.assertEqual(self.follow('menuPlaylists'), 'Playlists')
        self.charted = connection(dict(GQL_PLAYLIST, title='Cool Jazz'))
        self.assertEqual(self.follow('getPopularPlayLists'), 'Playlists / Popular')
        self.assertEqual(self.follow('lookup'), 'Playlists / Popular / Cool Jazz')

    def test_a_title_with_url_characters_comes_through(self):
        self.open('')
        self.follow('menuPlaylists')
        self.charted = connection(dict(GQL_PLAYLIST, title='Rock & Roll / 50%'))
        self.follow('getPopularPlayLists')
        self.assertEqual(self.follow('lookup'), 'Playlists / Popular / Rock & Roll / 50%')

    def searched_before(self, kind, query):
        with open(os.path.join(Kodi.profile, 'searches.json'), 'w') as handle:
            json.dump({kind: [query]}, handle)

    def test_a_search_from_the_history_shows_what_was_searched_for(self):
        self.searched_before('PlayLists', 'jazz')
        self.open('')
        self.follow('menuPlaylists')
        self.assertEqual(self.follow('searchHistoryPlayLists'), 'Playlists / Search history')
        self.assertEqual(self.follow('searchPlayLists'), 'Playlists / Search history / jazz')

    def test_the_next_page_stays_in_the_folder(self):
        invoke(urlencode({'mode': 'getArtistDetails', 'asin': 'B001RJ93XS',
                          'crumbs': json.dumps(['Artists', 'Search', 'Alphaville'])}))
        next_page = AMitem().setPaginator('next-page-token', None, 'B001RJ93XS')[0]
        self.assertEqual(self.open(clicked(next_page)), 'Artists / Search / Alphaville')

    def test_a_song_carries_no_path(self):
        self.searched_before('Songs', 'jazz')
        self.open('')
        self.follow('menuSongs')
        self.follow('searchHistorySongs')
        self.found = connection(song('B0CATALOG1', 'Take Five'))
        self.follow('searchSongs')
        songs = [url for url, li, folder in Kodi.items if not folder]
        self.assertEqual(len(songs), 1)
        self.assertNotIn('crumbs', parse_qs(urlparse(songs[0]).query))


if __name__ == '__main__':
    unittest.main()
