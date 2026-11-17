"""The search history: the terms searched for before, to search again or to remove."""

import os
import unittest
from urllib.parse import parse_qs, urlparse

from .support import ROOT, AddonTest, Kodi, clicked, invoke, signed_in, text
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.main import AmazonMedia
from resources.lib.tools import AMtools

NOTHING_FOUND = {'specificationSearch': {'result': []}}


class History(AddonTest):
    def setUp(self):
        super().setUp()
        self.tools = AMtools()

    def test_the_latest_search_comes_first_and_only_once_whatever_its_case(self):
        for query in ('jazz', 'Rock', 'JAZZ'):
            self.tools.addSearch('Songs', query)
        self.assertEqual(self.tools.searchHistory('Songs'), ['JAZZ', 'Rock'])

    def test_the_history_keeps_the_latest_25_searches(self):
        for number in range(30):
            self.tools.addSearch('Songs', 'term %d' % number)
        history = self.tools.searchHistory('Songs')
        self.assertEqual((len(history), history[0], history[-1]), (25, 'term 29', 'term 5'))

    def test_every_kind_of_search_has_a_history_of_its_own(self):
        self.tools.addSearch('Songs', 'jazz')
        self.tools.addSearch('Albums', 'rock')
        self.assertEqual((self.tools.searchHistory('Songs'), self.tools.searchHistory('Albums')), (['jazz'], ['rock']))

    def test_a_removed_search_is_gone_whatever_its_case(self):
        for query in ('jazz', 'rock'):
            self.tools.addSearch('Songs', query)
        self.tools.deleteSearch('Songs', 'JAZZ')
        self.assertEqual(self.tools.searchHistory('Songs'), ['rock'])


class OldSearches(AddonTest):
    # Up to version 2.1 the last three searches of each kind were kept in hidden settings.
    def setUp(self):
        super().setUp()
        Kodi.settings.update(search1Songs='jazz', search2Songs='true', search1Albums='pop')
        self.tools = AMtools()

    def test_the_last_searches_are_taken_over_in_their_order(self):
        self.assertEqual((self.tools.searchHistory('Songs'), self.tools.searchHistory('Albums'),
                          self.tools.searchHistory('Artists')), (['jazz', 'true'], ['pop'], []))

    def test_they_are_taken_over_once(self):
        self.tools.searchHistory('Songs')
        Kodi.settings['search1Songs'] = 'rock'
        self.assertEqual(self.tools.searchHistory('Songs'), ['jazz', 'true'])

    def test_they_do_not_return_after_the_add_on_is_reset(self):
        self.tools.resetAddon()
        self.assertEqual(self.tools.searchHistory('Songs'), [])


class Searching(AddonTest):
    def setUp(self):
        super().setUp()
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.gql.side_effect = lambda name, variables: NOTHING_FOUND

    def run_plugin(self, query):
        del Kodi.items[:]
        invoke(query)
        AmazonMedia().reqDispatch()
        return [(li, parse_qs(urlparse(url).query)) for url, li, folder in Kodi.items]

    def history(self, kind):
        invoke('')
        return AMtools().searchHistory(kind)

    def test_an_entered_search_is_added_to_its_history(self):
        Kodi.typed = 'jazz'
        self.run_plugin('mode=searchSongs')
        self.assertEqual((self.history('Songs'), self.history('Albums')), (['jazz'], []))

    def test_the_menu_offers_the_history_only_once_there_is_one(self):
        entry = text(30043)
        self.assertNotIn(entry, [li.label for li, query in self.run_plugin('mode=menuSongs')])
        self.run_plugin('mode=searchSongs&query=jazz')
        self.assertIn(entry, [li.label for li, query in self.run_plugin('mode=menuSongs')])

    def test_an_entry_of_the_history_searches_again(self):
        self.run_plugin('mode=searchAlbums&query=jazz')
        [(li, query)] = self.run_plugin('mode=searchHistoryAlbums')
        self.assertEqual((li.label, query['mode'], query['query']), ('jazz', ['searchAlbums'], ['jazz']))
        self.gql.reset_mock()
        self.run_plugin(clicked('plugin://plugin.audio.amazonmedia/?' + urlparse(Kodi.items[0][0]).query))
        self.assertEqual(self.gql.call_args.args[1]['searchText'], 'jazz')

    def test_an_entry_of_the_history_can_be_removed_from_its_context_menu(self):
        self.run_plugin('mode=searchArtist&query=jazz')
        [(li, query)] = self.run_plugin('mode=searchHistoryArtists')
        [(label, command)] = li.context_menu
        self.assertEqual(label, text(30044))
        self.run_plugin(clicked(command[len('RunPlugin('):-1]))
        self.assertEqual((self.history('Artists'), Kodi.builtins[-1]), ([], 'Container.Refresh'))

    def test_search_and_history_show_the_search_icon(self):
        self.run_plugin('mode=searchSongs&query=jazz')
        menu = {li.label: li.art for li, query in self.run_plugin('mode=menuSongs')}
        [(entry, query)] = self.run_plugin('mode=searchHistorySongs')
        self.assertEqual(Kodi.content, '')
        art = [(name, os.path.basename(images['icon']), os.path.basename(images['fanart']))
               for name, images in ((text(30042), menu[text(30042)]), (text(30043), menu[text(30043)]), ('jazz', entry.art))]
        self.assertEqual(art, [(text(30042), 'search.png', 'search.png'),
                               (text(30043), 'search.png', 'search.png'),
                               ('jazz', 'search.png', 'search.png')])
        for name, icon, fanart in art:
            with self.subTest(image=icon):
                self.assertTrue(os.path.exists(os.path.join(ROOT, 'resources', 'images', icon)))
                self.assertTrue(os.path.exists(os.path.join(ROOT, 'resources', 'images', fanart)))

    def test_resetting_the_add_on_forgets_the_history(self):
        self.run_plugin('mode=searchPlayLists&query=jazz')
        self.run_plugin('mode=resetAddon')
        self.assertEqual(self.history('PlayLists'), [])


if __name__ == '__main__':
    unittest.main()
