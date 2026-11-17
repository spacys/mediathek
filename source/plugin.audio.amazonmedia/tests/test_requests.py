"""What the add-on asks Amazon for.

Amazon answers several of these requests with an empty result or an error
when a single field is off, so the tests pin the fields that decided it.
"""

import json
import unittest

from .support import AddonTest, Response, invoke, signed_in
from resources.lib import amzcall
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.logon import AMlogon
from resources.lib.tools import AMtools

# What the Cirrus v3 library API accepted when it was probed; anything else is
# refused with HTTP 400.
LIBRARY_SORT_KEYS = {'albumArtistName', 'genre', 'creationDate', 'purchaseDate',
                     'artistName', 'lastUpdatedDate', 'title', 'albumName'}
LIBRARY_ALBUM_FIELDS = {'albumName', 'albumArtistName', 'albumAsin', 'objectId', 'albumCoverImageFull',
                        'sortAlbumName', 'albumReleaseDate', 'primaryGenre', 'albumPrimaryGenre',
                        'status', 'albumArtistAsin'}


class Requests(AddonTest):
    def body(self, mode, asin=None, mediatype=None):
        call = AMcall()
        signed_in(call.credentials)
        return json.loads(call.prepReqData(mode, asin, mediatype))


class SignIn(AddonTest):
    def test_the_sign_in_is_read_once_per_call_and_the_cookies_are_left_alone(self):
        # requests hands the cookies of an answer to a session of its own, not to the jar it is given.
        invoke('mode=getRecentlyAddedSongs')
        loads = []
        self.patch(AMtools, 'load', lambda tools: loads.append(1) or signed_in(AMaccess()))
        saved = self.patch(AMtools, 'saveCookie')
        self.patch(amzcall.requests, 'post', return_value=Response({}))
        call = AMcall()
        call.amzCall('APIV3getTracks', 'recentlyaddedsongs')
        call.amzCall('APIlookup', 'itemLookup', None, ['B0ASONG001'], [])
        self.assertEqual((len(loads), saved.called), (1, False))

    def test_expired_tokens_are_renewed_and_the_request_is_sent_again(self):
        invoke('mode=getRecentlyAddedSongs')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        saved = self.patch(AMtools, 'save')
        self.patch(AMlogon, 'fetchAppConfig', return_value={
            'accessToken': 'new-access-token', 'csrf': {'token': 'new-csrf', 'ts': '3', 'rnd': '4'},
            'deviceId': 'device-id', 'customerId': 'customer-id', 'marketplaceId': 'marketplace-id',
            'deviceType': 'device-type', 'musicTerritory': 'DE', 'displayLanguage': 'de_DE',
            'siteRegion': 'EU', 'tier': 'PRIME'})
        post = self.patch(amzcall.requests, 'post', side_effect=[
            Response({'message': 'CSRF_TOKEN_EXPIRED: [dms-unsigned]:Expired CSRF timestamp'}, 401),
            Response({'tracks': []})])
        self.assertEqual(AMcall().amzCall('APIV3getTracks', 'recentlyaddedsongs'), {'tracks': []})
        self.assertEqual(post.call_args.kwargs['headers']['csrf-token'], 'new-csrf')
        self.assertTrue(saved.called)


class Library(Requests):
    def library_requests(self):
        for mode, query, asin in (('getLibraryAlbums', 'mode=getPurAlbums', None),
                                  ('recentlyaddedsongs', 'mode=getRecentlyAddedSongs', None)):
            invoke(query)
            yield query, self.body(mode, asin)

    def test_every_library_request_sorts_by_a_key_amazon_accepts(self):
        for query, body in self.library_requests():
            with self.subTest(query=query):
                self.assertIn(body['sortOrder']['sort'], LIBRARY_SORT_KEYS)

    def test_albums_only_ask_for_fields_amazon_returns_for_albums(self):
        invoke('mode=getPurAlbums')
        self.assertLessEqual(set(self.body('getLibraryAlbums')['attributeList']), LIBRARY_ALBUM_FIELDS)

    def filters(self, query, mode):
        invoke(query)
        return {f['attributeName']: f['attributeValue'] for f in self.body(mode)['filterList']}

    def test_purchased_albums_keep_to_what_was_bought(self):
        self.assertEqual(self.filters('mode=getPurAlbums', 'getLibraryAlbums').get('purchased'), 'true')

    def test_the_next_page_is_asked_for_with_the_token_of_the_last_one(self):
        invoke('mode=getRecentlyAddedSongs&token=next-page-token=')
        self.assertEqual(self.body('recentlyaddedsongs')['nextToken'], 'next-page-token=')

    def test_the_first_page_carries_no_token(self):
        invoke('mode=getRecentlyAddedSongs')
        self.assertNotIn('nextToken', self.body('recentlyaddedsongs'))


if __name__ == '__main__':
    unittest.main()
