"""The menus against the dispatcher and against the language files.

A menu entry whose mode nobody handles ends in Kodi as an empty, failed
listing. Features have been removed from the add-on; their entries must go
with them.
"""

import os
import re
import unittest

from .support import LANGUAGE_FOLDER, LANGUAGES, AddonTest, Kodi, invoke, signed_in, text
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.main import AmazonMedia
from resources.lib.menu import AMmenu
from resources.lib.tools import AMtools


def menu_entries():
    for name in sorted(vars(AMmenu)):
        if name.startswith('menu'):
            for entry in getattr(AMmenu, name)():
                yield name, entry['fct']


def shown(language):
    """What Kodi shows for each string id in the given language."""
    path = os.path.join(LANGUAGE_FOLDER, 'resource.language.%s' % language, 'strings.po')
    with open(path, encoding='utf-8') as handle:
        return {int(number): msgstr or msgid
                for number, msgid, msgstr in re.findall(r'msgctxt "#(\d+)"\nmsgid "(.*)"\nmsgstr "(.*)"', handle.read())}


class Menus(AddonTest):
    def test_every_entry_lists_something_or_asks_amazon(self):
        # A search history is only offered once there is one.
        for kind in ('PlayLists', 'Albums', 'Songs', 'Artists'):
            AMtools().addSearch(kind, 'jazz')
        for menu, mode in menu_entries():
            with self.subTest(menu=menu, mode=mode):
                Kodi.typed = 'jazz'
                del Kodi.items[:]
                invoke('mode=' + mode)
                self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
                asked = self.patch(AMcall, 'amzCall', side_effect=RuntimeError('not answered in this test'))
                AmazonMedia().reqDispatch()
                self.assertTrue(asked.called or self.gql.called or Kodi.items, 'nothing handles this entry')

    def test_a_menu_entry_sets_its_image_only_where_its_shape_fits(self):
        # The images are icons or wide pictures; poster, banner and landscape are other shapes.
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        for kind in ('PlayLists', 'Albums', 'Songs', 'Artists'):
            AMtools().addSearch(kind, 'jazz')
        for query in [''] + ['mode=' + name for name in sorted(vars(AMmenu)) if name.startswith('menu') and name != 'menuHome']:
            del Kodi.items[:]
            invoke(query)
            AmazonMedia().reqDispatch()
            for url, li, folder in Kodi.items:
                with self.subTest(query=query, entry=li.label):
                    self.assertEqual(sorted(li.art), ['fanart', 'icon', 'thumb'])

    def test_a_menu_declares_no_content_type(self):
        # Declared as albums, skins show a folder symbol in the list instead of the entry's icon.
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        for query in [''] + ['mode=' + name for name in sorted(vars(AMmenu)) if name.startswith('menu') and name != 'menuHome']:
            with self.subTest(query=query):
                Kodi.content = None
                invoke(query)
                AmazonMedia().reqDispatch()
                self.assertEqual(Kodi.content, '')

    def test_the_home_menu_repeats_no_entry_of_the_menus_below_it(self):
        below = {text(entry['txt']) for name in vars(AMmenu) if name.startswith('menu') and name != 'menuHome'
                 for entry in getattr(AMmenu, name)()}
        self.assertEqual({text(entry['txt']) for entry in AMmenu.menuHome()} & below, set())

    def test_the_menus_below_it_list_what_they_share_in_the_same_order(self):
        menus = [[text(entry['txt']) for entry in getattr(AMmenu, name)()]
                 for name in sorted(vars(AMmenu)) if name.startswith('menu') and name != 'menuHome']
        for first in menus:
            for second in menus:
                with self.subTest(first=first, second=second):
                    self.assertEqual([label for label in first if label in second],
                                     [label for label in second if label in first])

    def test_the_search_dialog_says_what_is_searched_for(self):
        # The menu entry is just "Search"; the dialog has no path above it to tell what for.
        for mode, heading in (('searchPlayLists', 30013), ('searchAlbums', 30010),
                              ('searchSongs', 30011), ('searchArtist', 30014)):
            with self.subTest(mode=mode):
                del Kodi.headings[:]
                invoke('mode=' + mode)
                self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
                AmazonMedia().reqDispatch()
                self.assertEqual(Kodi.headings, [text(heading)])
                self.assertNotEqual(text(heading), text(30042))


class Labels(unittest.TestCase):
    def test_no_entry_repeats_the_name_of_its_menu(self):
        # The path top left names the menu already. A word that begins like the menu
        # name also catches "Playlist" below "Playlists" and "Album" below "Albums".
        menus = {entry['fct']: entry['txt'] for entry in AMmenu.menuHome() if entry['fct'].startswith('menu')}
        for language in LANGUAGES:
            texts = shown(language)
            for menu, name in menus.items():
                stem = texts[name].lower()[:5]
                for entry in getattr(AMmenu, menu)():
                    with self.subTest(language=language, menu=texts[name], entry=texts[entry['txt']]):
                        words = re.findall(r'\w+', texts[entry['txt']].lower())
                        self.assertFalse([word for word in words if word.startswith(stem)])

    def test_the_search_entry_says_that_a_dialog_follows(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertTrue(shown(language)[30042].endswith(' ...'))


if __name__ == '__main__':
    unittest.main()
