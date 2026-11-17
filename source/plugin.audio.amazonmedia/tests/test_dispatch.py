"""How a plugin call ends when something goes wrong, and how it tells the user."""

import json
import os
import re
import unittest
from http.cookiejar import Cookie

from .support import AddonTest, HANDLE, Kodi, Response, invoke, signed_in, text, xbmc
from resources.lib import logon
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.logon import AMlogon
from resources.lib.main import AmazonMedia
from resources.lib.tools import AMtools


class FailedRequest(AddonTest):
    def setUp(self):
        super().setUp()
        self.stored = [os.path.join(Kodi.profile, name) for name in ('cookie', 'data.obj')]
        for path in self.stored:
            open(path, 'w').close()
        invoke('mode=getPopularPlayLists')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.gql.side_effect = ValueError('Amazon answered 500')
        self.logon = self.patch(AMlogon, 'amazonLogon')
        AmazonMedia().reqDispatch()

    def test_the_stored_sign_in_survives(self):
        self.assertEqual([os.path.exists(path) for path in self.stored], [True, True])

    def test_the_user_is_not_asked_to_sign_in_again(self):
        self.logon.assert_not_called()

    def test_the_failure_is_shown_as_an_error(self):
        self.assertEqual(Kodi.notifications, [{'heading': 'Error', 'message': text(30077), 'icon': 'error'}])

    def test_the_listing_is_ended_as_failed(self):
        self.assertEqual(Kodi.directories, [(HANDLE, False)])

    def test_the_cause_ends_up_in_the_log(self):
        errors = [message for level, message in Kodi.log if level == xbmc.LOGERROR]
        self.assertTrue(any('Amazon answered 500' in message for message in errors))


def cookie(name, value, domain):
    return Cookie(0, name, value, None, False, domain, True, True, '/', True, True, None, False, None, None, {})


class StoredSignIn(AddonTest):
    FILES = ('cookie', 'data.json', 'data.obj')

    def kept(self):
        return [name for name in self.FILES if os.path.exists(os.path.join(Kodi.profile, name))]

    def test_a_stored_sign_in_is_read_back_and_removed_with_the_credentials(self):
        invoke('')
        tools = AMtools()
        stored = signed_in(AMaccess())
        stored.USERPASSWORD = 'secret'
        tools.save(stored)
        tools.saveCookie(stored.COOKIE)
        stored.CUSTOMERID = stored.ACCESSTOKEN = None
        loaded = tools.load()
        self.assertEqual((loaded.CUSTOMERID, loaded.ACCESSTOKEN, loaded.REGION), ('customer-id', 'Bearer access-token', 'EU'))
        tools.resetCredentials()
        self.assertEqual(self.kept(), [])

    def test_the_sign_in_is_kept_as_plain_data_without_the_password(self):
        invoke('')
        stored = signed_in(AMaccess())
        stored.USERPASSWORD = 'secret'
        AMtools().save(stored)
        with open(os.path.join(Kodi.profile, 'data.json'), encoding='utf-8') as file:
            kept = json.load(file)
        self.assertEqual(kept['CUSTOMERID'], 'customer-id')
        self.assertNotIn('secret', json.dumps(kept))
        self.assertNotIn('COOKIE', kept)

    def test_without_a_stored_sign_in_the_user_has_to_sign_in(self):
        invoke('')
        with self.assertRaises(IOError):
            AMtools().load()

    def old_sign_in(self, config):
        """The files of 2.2.3: cookies, and a pickled object that must not be read."""
        invoke('')
        tools = AMtools()
        jar = signed_in(AMaccess()).COOKIE
        jar.set_cookie(cookie('at-acbde', 'value', '.amazon.de'))
        tools.saveCookie(jar)
        jar.clear()
        with open(os.path.join(Kodi.profile, 'data.obj'), 'wb') as file:
            # A pickle that runs code when read: reading it at all fails the test.
            file.write(b"cos\nsystem\n(S'exit 1'\ntR.")
        posted = self.patch(logon.requests, 'post', return_value=Response(config))
        return tools, posted

    def test_a_sign_in_of_an_earlier_version_is_taken_over_by_its_cookies_alone(self):
        tools, posted = self.old_sign_in({
            'accessToken': 'fresh', 'csrf': {'token': 'c', 'ts': '1', 'rnd': '2'}, 'deviceId': 'device-id',
            'customerId': 'customer-id', 'marketplaceId': 'marketplace-id', 'deviceType': 'device-type',
            'musicTerritory': 'DE', 'displayLanguage': 'de_DE', 'siteRegion': 'EU', 'tier': 'PRIME'})
        loaded = tools.load()
        self.assertEqual(posted.call_args.kwargs['url'].split('/config.json')[0], 'https://music.amazon.de')
        self.assertEqual((loaded.CUSTOMERID, loaded.ACCESSTOKEN, loaded.USERTLD, loaded.REGION),
                         ('customer-id', 'Bearer fresh', 'de', 'ZAZ'))
        self.assertEqual(self.kept(), ['cookie', 'data.json'])

    def test_cookies_that_are_no_longer_signed_in_ask_for_a_new_sign_in(self):
        tools, posted = self.old_sign_in({'customerId': '', 'csrf': {'token': 'c', 'ts': '1', 'rnd': '2'}})
        with self.assertRaises(IOError):
            tools.load()


class Information(AddonTest):
    def titles(self):
        return [re.match(r'Notification\("([^"]*)"', command).group(1) for command in Kodi.builtins]

    def test_the_title_of_an_information_carries_no_colon(self):
        for mode in ('resetCredentials', 'resetAddon'):
            with self.subTest(mode=mode):
                del Kodi.builtins[:]
                invoke('mode=' + mode)
                AmazonMedia().reqDispatch()
                self.assertEqual(self.titles(), ['Information'])


if __name__ == '__main__':
    unittest.main()
