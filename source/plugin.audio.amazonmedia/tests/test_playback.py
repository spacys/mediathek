"""What the user is told when Amazon hands out no stream, and what the player gets."""

import base64
import json
import unittest

from .support import AddonTest, Kodi, Response, clicked, invoke, signed_in, text, xbmcplugin
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.item import AMitem
from resources.lib.play import AMplay
from resources.lib.tools import AMtools


class Refused(AddonTest):
    def play(self, status):
        invoke('mode=getTrack&asin=B0PURCHASE')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.patch(AMcall, 'amzCall', return_value=Response({'contentResponseList': [{
            'contentResponseStatusCode': status, 'contentResponseStatusMessage': '', 'manifest': ''}]}))
        return AMplay().getTrack('B0PURCHASE', None)

    def told(self, reason):
        return [{'heading': 'Error', 'message': text(30073) + ' ' + text(reason), 'icon': 'error'}]

    def test_a_title_amazon_does_not_stream_says_so(self):
        # Purchases that are not part of the streaming catalogue are refused this way.
        self.assertFalse(self.play('CONTENT_NOT_ELIGIBLE'))
        self.assertEqual(Kodi.notifications, self.told(30078))

    def test_the_concurrency_limit_is_reported_once(self):
        self.play('MAX_CONCURRENCY_REACHED')
        self.assertEqual(Kodi.notifications, self.told(30075))

    def test_any_other_refusal_says_that_no_stream_was_found(self):
        self.play('BAD_REQUEST')
        self.assertEqual(Kodi.notifications, self.told(30074))


class License(AddonTest):
    def played(self, build_version):
        Kodi.build_version = build_version
        invoke('mode=getTrack&asin=B0ASONG001')
        signed_in(AMaccess()).ACCESSTOKEN = 'Bearer access|token'
        resolved = self.patch(xbmcplugin, 'setResolvedUrl')
        AMplay().finalizeItem('http://127.0.0.1:1/mpd/song.mpd', True, True)
        return resolved.call_args.kwargs['listitem'].properties

    def test_kodi_22_gets_the_license_request_the_way_it_is_no_longer_deprecated(self):
        properties = self.played('22.0-RC1 (21.90.901) Git:20260928-6ba5e10e65')
        self.assertEqual([p for p in ('inputstream.adaptive.license_type', 'inputstream.adaptive.license_key') if p in properties], [])
        license = json.loads(properties['inputstream.adaptive.drm'])['com.widevine.alpha']['license']
        body = json.loads(base64.b64decode(license['req_data']))
        self.assertTrue(license['server_url'].endswith('/EU/api/dmls/'), license['server_url'])
        self.assertEqual((body['licenseChallenge'], body['Authorization']), ('{CHA-B64}', 'Bearer access|token'))
        self.assertEqual((license['unwrapper'], license['unwrapper_params']), ('json,base64', {'path_data': 'license'}))

    def test_an_older_kodi_gets_the_license_key(self):
        properties = self.played('21.2 (21.2.0) Git:20250208-4b2a3c1d0e')
        self.assertNotIn('inputstream.adaptive.drm', properties)
        self.assertEqual(properties['inputstream.adaptive.license_type'], 'com.widevine.alpha')
        url, headers, body, response = properties['inputstream.adaptive.license_key'].split('|')
        self.assertEqual((json.loads(body)['licenseChallenge'], json.loads(body)['Authorization'], response),
                         ('b{SSM}', 'Bearer access|token', 'JBlicense'))


class NowPlaying(AddonTest):
    def played(self):
        item = AMitem()
        signed_in(item.credentials)
        song = {'asin': 'B0ASONG001', 'title': 'A Song', 'artistName': 'An Artist', 'primaryGenre': 'Pop',
                'isMusicSubscription': 'true'}
        url, li = item.setItem(*item.setData(song, {'mode': 'getTrack'}))
        invoke(clicked(url))
        resolved = self.patch(xbmcplugin, 'setResolvedUrl')
        AMplay().finalizeItem('song.mpd')
        return resolved.call_args.kwargs['listitem']

    def test_a_song_is_played_by_the_video_player(self):
        # Only VideoPlayer decodes the DRM protected stream; music information would pick PAPlayer.
        self.assertEqual(self.played().tag_type, 'video')

    def test_the_artist_and_genre_of_a_listed_song_reach_the_player_as_they_are(self):
        info = self.played().info
        self.assertEqual((info['artist'], info['genre']), (['An Artist'], ['Pop']))


if __name__ == '__main__':
    unittest.main()
