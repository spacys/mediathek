"""addon.xml against what the Kodi repositories accept."""

import os
import unittest
import xml.etree.ElementTree as ElementTree

from .support import ROOT


class News(unittest.TestCase):
    def setUp(self):
        news = ElementTree.parse(os.path.join(ROOT, 'addon.xml')).getroot().find('.//news')
        if news is None:
            self.skipTest('addon.xml carries no news')
        self.news = news.text.strip()

    def test_the_news_fit_into_what_the_repositories_accept(self):
        # The addon.xml schema of the Kodi repositories caps the news at 1500 characters.
        self.assertLessEqual(len(self.news), 1500)

    def test_the_news_are_about_the_latest_version_of_the_changelog(self):
        # The news sum the latest changelog entry up; they must not be left at an older version.
        with open(os.path.join(ROOT, 'changelog.txt'), encoding='utf-8') as handle:
            latest = handle.readline().strip()
        self.assertEqual(self.news.splitlines()[0], latest)



class Settings(unittest.TestCase):
    def test_every_visible_setting_explains_itself(self):
        settings = ElementTree.parse(os.path.join(ROOT, 'resources', 'settings.xml')).getroot()
        for setting in settings.iter('setting'):
            if setting.findtext('visible') != 'false':
                with self.subTest(setting=setting.get('id')):
                    self.assertTrue(setting.get('help'))

    def test_the_settings_belong_to_this_add_on(self):
        addon_id = ElementTree.parse(os.path.join(ROOT, 'addon.xml')).getroot().get('id')
        settings = ElementTree.parse(os.path.join(ROOT, 'resources', 'settings.xml')).getroot()
        self.assertEqual(settings.find('section').get('id'), addon_id)
        for action in settings.iter('data'):
            with self.subTest(action=action.text):
                self.assertIn('plugin://%s/' % addon_id, action.text)

if __name__ == '__main__':
    unittest.main()
