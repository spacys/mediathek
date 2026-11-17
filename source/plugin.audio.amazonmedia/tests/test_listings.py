"""What ends up in a listing, and how it is marked."""

import json
import unittest
from urllib.parse import parse_qs, urlparse

from .support import AddonTest, Kodi, Response, clicked, invoke, signed_in, text
from resources.lib import amzcall
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.item import AMitem
from resources.lib.main import AmazonMedia
from resources.lib.tools import AMtools

# How Amazon describes its catalogue today: nothing is marked as Prime any more.
CATALOGUE_TRACK = {'asin': 'B001SG09MY', 'title': 'Big in Japan', 'primeStatus': 'NOT_PRIME',
                   'isMusicSubscription': 'true'}
PURCHASED_TRACK = {'asin': 'B0PURCHASE', 'title': 'A Purchased Song', 'purchased': 'true'}
UNAVAILABLE_TRACK = {'asin': 'B0UNAVAILA', 'title': 'An Unavailable Song', 'primeStatus': 'NOT_PRIME',
                     'isMusicSubscription': 'false'}

GOLD, PLAIN, RED = '[COLOR gold]%s[/COLOR]', '%s', '[COLOR red]%s[/COLOR]'


class Playability(AddonTest):
    def marked(self, track, tier):
        item = AMitem()
        signed_in(item.credentials, tier)
        _, meta = item.setData(dict(track), {'mode': 'getTrack'})
        return meta['isPlayable'], meta['color']

    def test_the_catalogue_is_playable_whatever_the_tier(self):
        for tier in ('PRIME', 'UNLIMITED'):
            with self.subTest(tier=tier):
                self.assertEqual(self.marked(CATALOGUE_TRACK, tier), (True, PLAIN))

    def test_a_purchase_is_playable_and_gold(self):
        self.assertEqual(self.marked(PURCHASED_TRACK, 'PRIME'), (True, GOLD))

    def test_a_title_outside_the_catalogue_is_unplayable_and_red(self):
        self.assertEqual(self.marked(UNAVAILABLE_TRACK, 'PRIME'), (False, RED))

    def test_an_old_setting_that_turned_the_colours_off_is_ignored(self):
        Kodi.settings['showcolentr'] = 'false'
        self.assertEqual(self.marked(PURCHASED_TRACK, 'PRIME'), (True, GOLD))

    def searched_songs(self):
        invoke('mode=getRecentlyAddedSongs')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess(), 'PRIME'))
        songs = [dict(CATALOGUE_TRACK), dict(UNAVAILABLE_TRACK)]
        self.patch(AMcall, 'amzCall', side_effect=lambda api, *args: {'resultList': [{'metadata': dict(s)} for s in songs],
                                                                      'nextToken': None} if api == 'APIV3getTracks' else {'trackList': songs})
        AmazonMedia().reqDispatch()
        return [li.label for url, li, folder in Kodi.items]

    def test_a_prime_account_finds_the_catalogue_in_the_songs_of_a_chart(self):
        self.assertIn('Big in Japan', self.searched_songs())

    def test_unplayable_songs_are_hidden_by_default(self):
        self.assertEqual(self.searched_songs(), ['Big in Japan'])

    def test_unplayable_songs_are_listed_when_the_setting_is_off(self):
        Kodi.settings['hideUnplayableSongs'] = 'false'
        self.assertEqual(self.searched_songs(), ['Big in Japan', RED % 'An Unavailable Song'])


class RecentlyAdded(AddonTest):
    def told(self, tracks):
        invoke('mode=getRecentlyAddedSongs')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.patch(AMcall, 'amzCall', side_effect=lambda api, *args:
                   {'resultList': tracks} if api == 'APIV3getTracks' else {'trackList': []})
        AmazonMedia().reqDispatch()
        return Kodi.notifications

    def test_an_empty_list_says_nothing_was_added_in_the_last_90_days(self):
        self.assertEqual(self.told([]), [{'heading': 'Information', 'message': text(30079), 'icon': 'info'}])

    def test_a_list_with_songs_says_nothing(self):
        self.assertEqual(self.told([{'metadata': dict(PURCHASED_TRACK)}]), [])


class LibrarySongs(AddonTest):
    # The library answers with whether a title was bought, not with whether it is streamed.
    LIBRARY = {'resultList': [{'metadata': {'asin': CATALOGUE_TRACK['asin'], 'title': 'Big in Japan', 'purchased': 'false'}}]}

    def listed(self, query):
        invoke(query)
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        asked = self.patch(AMcall, 'amzCall', side_effect=lambda api, mode, *args:
                           self.LIBRARY if api == 'APIV3getTracks' else {'trackList': [dict(CATALOGUE_TRACK)]})
        AmazonMedia().reqDispatch()
        lookups = [c.args[3] for c in asked.call_args_list if c.args[0] == 'APIlookup']
        return [li.label for url, li, folder in Kodi.items], lookups

    def test_a_song_added_from_the_catalogue_is_listed_as_playable(self):
        self.assertEqual(self.listed('mode=getRecentlyAddedSongs'), (['Big in Japan'], [[CATALOGUE_TRACK['asin']]]))


if __name__ == '__main__':
    unittest.main()
