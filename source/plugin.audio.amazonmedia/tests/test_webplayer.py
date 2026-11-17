"""Where the add-on follows the web player of Amazon Music.

The requests were read from the web player 1.0.11818.0 (music.amazon.de,
November 2026): how it loads its configuration, builds the API path and the
headers, asks for a manifest and what it does once Amazon refuses a license
because the client has no Widevine Verified Media Path (VMP).
"""

import json
import os
import re
import sys
import threading
import time
import unittest
import urllib.request
from unittest import mock
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlparse

from .support import AddonTest, Kodi, Response, invoke, signed_in, text, xbmcplugin
from resources.lib import amzcall, logon, proxy
from resources.lib.access import AMaccess
from resources.lib.amzcall import AMcall
from resources.lib.logon import AMlogon
from resources.lib.play import AMplay
from resources.lib.proxy import ProxyTCPD
from resources.lib.tools import AMtools

LICENSE_URL = 'https://music.amazon.de/ZAZ/api/dmls/'

CONFIG = {'accessToken': 'token', 'csrf': {'token': 'c', 'ts': '1', 'rnd': '2'}, 'deviceId': 'device-id',
          'customerId': 'customer-id', 'marketplaceId': 'marketplace-id', 'deviceType': 'device-type',
          'musicTerritory': 'DE', 'displayLanguage': 'de_DE', 'siteRegion': 'EU', 'tier': 'PRIME',
          'version': '1.0.11818.0'}


class Configuration(AddonTest):
    def configured(self, config):
        signing_in = AMlogon()
        signing_in._appConfig(config)
        return signing_in.credentials

    def test_the_api_path_takes_its_region_from_the_music_territory(self):
        # The site region of amazon.de is EU, the web player asks https://music.amazon.de/ZAZ/api/.
        self.assertEqual(self.configured(CONFIG).REGION, 'ZAZ')
        self.assertEqual((AMtools.apiRegion('US'), AMtools.apiRegion('JP'), AMtools.apiRegion('GB')),
                         ('NA', 'FE', 'ZAZ'))

    def test_a_territory_the_web_player_does_not_list_keeps_its_site_region(self):
        self.assertEqual(self.configured(dict(CONFIG, musicTerritory='XX')).REGION, 'EU')

    def test_the_configuration_is_asked_for_as_the_web_player_does(self):
        posted = self.patch(logon.requests, 'post', return_value=Response(CONFIG))
        signing_in = AMlogon()
        signed_in(signing_in.credentials)
        signing_in.fetchAppConfig()
        self.assertEqual(posted.call_args.kwargs['url'],
                         'https://music.amazon.de/config.json?clientApplication=skyfire&skipToken=false')

    def test_the_access_token_is_renewed_the_way_of_the_web_player_when_the_configuration_has_none(self):
        invoke('mode=getAllSongs')
        call = AMcall()
        signed_in(call.credentials)
        self.patch(AMtools, 'save')
        self.patch(logon.requests, 'post', return_value=Response({'csrf': CONFIG['csrf']}))
        asked = self.patch(logon.requests, 'get', return_value=Response({'accessToken': 'fresh', 'expiresIn': 3600}))
        self.assertTrue(call.renewTokens())
        self.assertEqual(asked.call_args.kwargs['url'], 'https://music.amazon.de/pandaToken')
        self.assertEqual(asked.call_args.kwargs['params'], {'deviceType': 'device-type'})
        self.assertEqual(call.credentials.ACCESSTOKEN, 'Bearer fresh')


class Requests(AddonTest):
    def call(self):
        invoke('mode=getTrack&asin=B0ASONG001')
        call = AMcall()
        signed_in(call.credentials)
        call.credentials.APPVERSION = '1.0.11818.0'
        return call

    def test_the_access_token_is_sent_along_with_the_csrf_tokens(self):
        head = self.call().prepReqHeader('target')
        self.assertEqual((head['Authorization'], head['csrf-token'], head['X-Amz-Target'], head['Content-Encoding']),
                         ('Bearer access-token', 'csrf', 'target', 'amz-1.0'))

    def test_the_player_names_itself_as_the_web_player_does(self):
        self.assertRegex(self.call().musicAgent(),
                         r'^Vinyl/2\.0 GreenHornet_Web/1\.0\.1468 \([0-9a-f]{4}-[0-9a-f]{4}-Gree-[0-9a-f]{4}-[0-9a-f]{5}\)$')

    def test_a_manifest_is_asked_for_with_what_the_web_player_sends(self):
        body = json.loads(self.call().prepReqData('getTrackDash', 'B0ASONG001', 'ASIN'))
        self.assertEqual(body, {
            'appInfo': {'musicAgent': body['appInfo']['musicAgent']},
            'customerId': 'customer-id',
            # Neither an entitlement nor the customer once more: the web player leaves both out.
            'customerInfo': {'marketplaceId': 'marketplace-id', 'territoryId': 'DE'},
            'contentIdList': [{'identifier': 'B0ASONG001', 'identifierType': 'ASIN'}],
            'deviceToken': {'deviceTypeId': 'device-type', 'deviceId': 'device-id'},
            'musicDashVersionList': ['V2'],
            'bitrateTypeList': ['HIGH']})

    UNVERIFIED = {'musicDashVersionList': ['SIREN_KATANA'], 'contentProtectionList': ['TRACK_PSSH'],
                  'tryAsinSubstitution': False}

    def asked(self, call):
        body = json.loads(call.prepReqData('getTrackDash', 'B0', 'ASIN'))
        return {key: body.get(key) for key in ('musicDashVersionList', 'contentProtectionList',
                                               'tryAsinSubstitution', 'bitrateTypeList') if key in body}

    def test_without_a_verified_media_path_the_manifest_of_the_web_player_is_asked_for(self):
        # Kodi 21.3 on Linux: Amazon refused the license for the best and for the lowest quality
        # of a V2 manifest alike (VMP_VALIDATION_FAILED). Chrome on Linux asks for this one and plays.
        for platform in ('System.Platform.Linux', 'System.Platform.Windows', 'System.Platform.OSX'):
            with self.subTest(platform=platform):
                call = self.call()
                Kodi.conditions = {platform}
                self.assertEqual(self.asked(call), self.UNVERIFIED)

    def test_after_a_refusal_for_vmp_it_is_asked_for_on_android_too(self):
        call = self.call()
        with open(os.path.join(Kodi.profile, 'vmp-unverified'), 'w') as handle:
            handle.write('VMP_VALIDATION_FAILED\n' + call.userAgent)
        self.assertEqual(self.asked(call), self.UNVERIFIED)

    def device(self, call, mode='getTrackDash'):
        return json.loads(call.prepReqData(mode, 'B0', 'ASIN'))['deviceToken']

    def test_no_device_calls_itself_unverified_before_amazon_refused_a_license(self):
        # Chrome on Linux has no Verified Media Path, sends no status and is handed a license.
        for platform in ('System.Platform.Android', 'System.Platform.Linux', 'System.Platform.Windows'):
            with self.subTest(platform=platform):
                call = self.call()
                Kodi.conditions = {platform}
                self.assertNotIn('vmpValidationStatus', self.device(call))
                self.assertNotIn('vmpValidationStatus', self.device(call, 'getLicenseForPlaybackV2'))

    def test_once_a_license_was_refused_for_vmp_the_device_is_unverified_for_manifest_and_license(self):
        call = self.call()
        with open(os.path.join(Kodi.profile, 'vmp-unverified'), 'w') as handle:
            handle.write('VMP_VALIDATION_FAILED\n' + call.userAgent)
        self.assertEqual(self.device(call)['vmpValidationStatus'], 'UNVERIFIED')
        self.assertEqual(self.device(call, 'getLicenseForPlaybackV2')['vmpValidationStatus'], 'UNVERIFIED')

    def test_a_refused_access_token_does_not_lock_out_a_sign_in_whose_cookies_are_good(self):
        call = self.call()
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.patch(AMcall, 'renewTokens', return_value=False)
        answers = [Response({}, 401), Response({'ok': True})]
        posted = self.patch(amzcall.requests, 'post', side_effect=lambda **kwargs: answers.pop(0))
        self.assertEqual(call.amzCall('APIstreamDash', 'getTrackDash', None, 'B0', 'ASIN').json(), {'ok': True})
        first, second = (sent.kwargs['headers'] for sent in posted.call_args_list)
        self.assertNotIn('Authorization', second)
        self.assertEqual(second['csrf-token'], 'csrf')

    def test_a_refusal_given_to_another_browser_name_is_not_held_against_this_one(self):
        # Kodi 21 on Linux: refused as Chrome for Windows, then named as what it is.
        call = self.call()
        with open(os.path.join(Kodi.profile, 'vmp-unverified'), 'w') as handle:
            handle.write('VMP_VALIDATION_FAILED\nMozilla/5.0 (Windows NT 10.0; Win64; x64)')
        self.assertNotIn('vmpValidationStatus', self.device(call))
        with open(os.path.join(Kodi.profile, 'vmp-unverified'), 'w') as handle:
            handle.write('VMP_VALIDATION_FAILED')
        self.assertNotIn('vmpValidationStatus', self.device(call))

    def test_kodi_on_a_linux_desktop_names_itself_as_chrome_for_linux(self):
        # Amazon expects a Verified Media Path of Chrome for Windows and none of Chrome for Linux.
        names = {}
        for platform in (('System.Platform.Linux',), ('System.Platform.Linux', 'System.Platform.Android'),
                         ('System.Platform.Windows',)):
            Kodi.conditions = set(platform)
            names[platform[-1]] = self.call().prepReqHeader('target')['User-Agent']
        self.assertIn('(X11; Linux x86_64)', names['System.Platform.Linux'])
        self.assertIn('(Windows NT 10.0; Win64; x64)', names['System.Platform.Android'])
        self.assertIn('(Windows NT 10.0; Win64; x64)', names['System.Platform.Windows'])

    def test_a_browser_name_set_by_the_user_is_kept(self):
        Kodi.conditions = {'System.Platform.Linux'}
        Kodi.settings['userAgent'] = 'My Browser'
        self.assertEqual(self.call().prepReqHeader('target')['User-Agent'], 'My Browser')

    def test_signing_out_forgets_the_refusal(self):
        call = self.call()
        with open(os.path.join(Kodi.profile, 'vmp-unverified'), 'w') as handle:
            handle.write('VMP_VALIDATION_FAILED\n' + call.userAgent)
        call.resetCredentials()
        self.assertFalse(call.vmpFailed())


SET = '<AdaptationSet mimeType="audio/mp4" codecs="{codec}">{type}<ContentProtection schemeIdUri="urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"><cenc:pssh>{codec}</cenc:pssh></ContentProtection>{reps}</AdaptationSet>'
TYPE = '<SupplementalProperty schemeIdUri="amz-music:trackType" value="{}"/>'
MPD = '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" xmlns:cenc="urn:mpeg:cenc:2013"><Period>{}</Period></MPD>'


class UnverifiedQuality(AddonTest):
    """Of the qualities of a manifest, a player without Verified Media Path is licensed the one marked LD."""

    def test_a_quality_marked_on_its_set_is_kept_with_its_protection_data(self):
        low = SET.format(codec='opus', type=TYPE.format('LD'), reps='<Representation id="1" bandwidth="53091"/>')
        high = SET.format(codec='flac', type=TYPE.format('HD'), reps='<Representation id="2" bandwidth="1137568"/>')
        self.assertEqual(AMplay.onlyUnverified(MPD.format(high + low + high)), MPD.format(low))

    def test_a_quality_marked_on_the_representation_is_kept_alone(self):
        reps = ''.join('<Representation id="{0}" bandwidth="{1}">{2}<SegmentList/></Representation>'.format(i, b, TYPE.format(t))
                       for i, (b, t) in enumerate([(325100, 'SD'), (53091, 'LD'), (197096, 'SD')]))
        only = '<Representation id="1" bandwidth="53091">{}<SegmentList/></Representation>'.format(TYPE.format('LD'))
        self.assertEqual(AMplay.onlyUnverified(MPD.format(SET.format(codec='opus', type='', reps=reps))),
                         MPD.format(SET.format(codec='opus', type='', reps=only)))

    def test_a_manifest_that_marks_no_such_quality_is_left_as_it_is(self):
        for manifest in (MPD.format(SET.format(codec='mp4a.40.5', type='', reps='<Representation id="0" bandwidth="49181"/>')),
                         MPD.format(SET.format(codec='flac', type=TYPE.format('HD'), reps='<Representation id="0"/>'))):
            self.assertEqual(AMplay.onlyUnverified(manifest), manifest)

    def play(self, platform):
        invoke('mode=getTrack&asin=B0ASONG001')
        Kodi.conditions = {platform}
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        low = SET.format(codec='opus', type=TYPE.format('LD'), reps='<Representation id="1" bandwidth="53091"/>')
        high = SET.format(codec='flac', type=TYPE.format('HD'), reps='<Representation id="2" bandwidth="1137568"/>')
        escaped = MPD.format(high + low).replace('"', '\\"').replace('><Period>', '>\\n<Period>')
        self.patch(AMcall, 'amzCall', return_value=Response({'contentResponseList': [{
            'contentResponseStatusCode': 'SUCCESS', 'manifest': escaped}]}))
        written = self.patch(AMplay, 'writeSongFile')
        self.patch(xbmcplugin, 'setResolvedUrl')
        AMplay().getTrack('B0ASONG001', None)
        return written.call_args.args[0], low, high

    def test_the_player_is_handed_the_licensed_quality_only_where_kodi_has_no_verified_media_path(self):
        manifest, low, high = self.play('System.Platform.Linux')
        self.assertIn(low, manifest)
        self.assertNotIn('flac', manifest)
        manifest, low, high = self.play('System.Platform.Android')
        self.assertIn(high, manifest)


class OutOfReach(AddonTest):
    """Kodi on Windows: Amazon refused the license for the one quality an unverified player may ask for."""

    def play(self, platform, refused, age=0, owned=False):
        invoke('mode=getTrack&asin=B0ASONG001')
        Kodi.conditions = {platform}
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        if refused:
            flag = os.path.join(Kodi.profile, 'vmp-unverified')
            with open(flag, 'w') as handle:
                handle.write('VMP_VALIDATION_FAILED\n' + AMplay().userAgent)
            os.utime(flag, (time.time() - age, time.time() - age))
        answers = {'APIstreamCoid': {'contentResponseList': [{'statusCode': 'SUCCESS', 'urlList': ['https://cdn.example/song.mp3']}]},
                   'APIstreamDash': {'contentResponseList': [{'contentResponseStatusCode': 'SUCCESS', 'manifest': '<MPD/>'}]}}
        asked = self.patch(AMcall, 'amzCall', side_effect=lambda *args: Response(answers[args[0]]))
        self.patch(AMplay, 'writeSongFile')
        resolved = self.patch(xbmcplugin, 'setResolvedUrl')
        AMplay().getTrack('B0ASONG001', 'object-id' if owned else None)
        return [call.args[0] for call in asked.call_args_list], resolved.called, [n['message'] for n in Kodi.notifications]

    def test_a_catalogue_song_is_not_started_for_its_unprotected_start_alone(self):
        self.assertEqual(self.play('System.Platform.Windows', True), ([], False, [text(30083)]))

    def test_a_song_the_customer_owns_still_plays(self):
        self.assertEqual(self.play('System.Platform.Windows', True, owned=True), (['APIstreamCoid'], True, []))

    def test_a_day_later_amazon_is_asked_again(self):
        self.assertEqual(self.play('System.Platform.Windows', True, age=25 * 60 * 60), (['APIstreamDash'], True, []))

    def test_without_a_refusal_and_on_android_the_song_is_asked_for(self):
        self.assertEqual(self.play('System.Platform.Windows', False), (['APIstreamDash'], True, []))
        self.assertEqual(self.play('System.Platform.Android', True), (['APIstreamDash'], True, []))


class TimeLimit(AddonTest):
    """No request waits for Amazon without an end."""

    def test_a_request_of_the_music_api_has_a_time_limit(self):
        invoke('mode=getRecentlyAddedSongs')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        posted = self.patch(amzcall.requests, 'post', return_value=Response({'ok': True}))
        AMcall().amzCall('APIV3getTracks', 'recentlyaddedsongs')
        self.assertEqual(posted.call_args.kwargs['timeout'], (10, 30))

    def test_the_configuration_and_the_access_token_have_a_time_limit(self):
        posted = self.patch(logon.requests, 'post', return_value=Response(CONFIG))
        asked = self.patch(logon.requests, 'get', return_value=Response({'accessToken': 'fresh'}))
        signing_in = AMlogon()
        signed_in(signing_in.credentials)
        signing_in.fetchAppConfig()
        signing_in.fetchAccessToken()
        self.assertEqual((posted.call_args.kwargs['timeout'], asked.call_args.kwargs['timeout']), ((10, 30), (10, 30)))

    def test_the_pages_of_the_sign_in_have_a_time_limit(self):
        from resources.lib import browser
        pages = browser.StatefulBrowser(timeout=(10, 30))
        page = '<form name="signIn" method="post" action="/ap/signin"><input name="email"></form>'
        got = self.patch(pages.session, 'get', return_value=mock.Mock(text=page, url='https://www.amazon.de/ap/signin'))
        sent = self.patch(pages.session, 'post', return_value=mock.Mock(text='', url='https://www.amazon.de/next'))
        pages.open('https://www.amazon.de/ap/signin')
        pages.select_form('form[name="signIn"]')
        pages.submit_selected()
        self.assertEqual((got.call_args.kwargs['timeout'], sent.call_args.kwargs['timeout']), ((10, 30), (10, 30)))


class OwnedSongs(AddonTest):
    """A song the customer owns is streamed as a plain file (getStreamingURLs), as the web player plays it."""

    def play(self, answers):
        invoke('mode=getTrack&asin=B0PURCHASE&objectId=object-id')
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        asked = self.patch(AMcall, 'amzCall', side_effect=lambda *args: Response(answers[args[0]]))
        resolved = self.patch(xbmcplugin, 'setResolvedUrl')
        self.patch(AMplay, 'writeSongFile')
        AMplay().getTrack('B0PURCHASE', 'object-id')
        return [call.args[0] for call in asked.call_args_list], resolved.call_args.kwargs['listitem']

    def test_the_file_is_handed_to_the_player_without_inputstream_adaptive_or_a_license(self):
        asked, item = self.play({'APIstreamCoid': {'contentResponseList': [{
            'statusCode': 'SUCCESS', 'urlList': ['https://cdn.example/song.mp3'], 'cdnTypeList': ['cf']}]}})
        self.assertEqual(asked, ['APIstreamCoid'])
        self.assertEqual(item.path, 'https://cdn.example/song.mp3')
        self.assertEqual([p for p in item.properties if p.startswith('inputstream')], [])

    def test_a_song_amazon_hands_out_no_file_for_is_asked_for_as_a_catalogue_song(self):
        asked, item = self.play({
            'APIstreamCoid': {'contentResponseList': [{'statusCode': 'CONTENT_NOT_ELIGIBLE', 'urlList': []}]},
            'APIstreamDash': {'contentResponseList': [{'contentResponseStatusCode': 'SUCCESS', 'manifest': '<MPD/>'}]}})
        self.assertEqual(asked, ['APIstreamCoid', 'APIstreamDash'])
        self.assertEqual(item.properties['inputstream'], 'inputstream.adaptive')

    def test_the_file_is_asked_for_with_what_the_web_player_sends(self):
        invoke('mode=getTrack&objectId=object-id')
        call = AMcall()
        signed_in(call.credentials)
        body = json.loads(call.prepReqData('getTrackCoid', 'object-id'))
        self.assertRegex(body['clientMetadata'].pop('clientRequestId'), r'^[0-9a-z]{19}$')
        self.assertTrue(body['appMetadata'].pop('userAgent'))
        self.assertEqual(body, {
            'contentIdList': [{'identifier': 'object-id', 'identifierType': 'COID'}],
            'bitRate': 'HIGH',
            'deviceToken': {'deviceTypeId': 'device-type', 'deviceId': 'device-id'},
            'appMetadata': {'https': True, 'appId': 'GreenHornet_Web', 'appVersion': '1.0.1468'},
            'clientMetadata': {'clientId': 'WebCP'},
            'customerId': 'customer-id'})


class Widevine(AddonTest):
    """InputStream Helper sees to the Widevine library before a protected song plays."""

    def play(self, ready, build='21.3'):
        invoke('mode=getTrack&asin=B0ASONG001')
        Kodi.build_version = build
        self.patch(AMtools, 'load', lambda tools: signed_in(AMaccess()))
        self.patch(AMcall, 'amzCall', return_value=Response({'contentResponseList': [{
            'contentResponseStatusCode': 'SUCCESS', 'manifest': '<MPD/>'}]}))
        self.patch(AMplay, 'writeSongFile')
        resolved = self.patch(xbmcplugin, 'setResolvedUrl')
        helper = mock.Mock()
        helper.Helper.return_value.check_inputstream.return_value = ready
        with mock.patch.dict(sys.modules, {'inputstreamhelper': helper}):
            AMplay().getTrack('B0ASONG001', None)
        return helper, resolved

    def test_the_helper_is_asked_for_dash_with_widevine_and_the_song_plays(self):
        helper, resolved = self.play(True)
        helper.Helper.assert_called_once_with('mpd', drm='com.widevine.alpha')
        self.assertEqual(resolved.call_args.kwargs['listitem'].properties['inputstream'], 'inputstream.adaptive')

    def test_without_a_widevine_library_nothing_is_handed_to_the_player(self):
        # Kodi 21 from Flatpak: no library yet, the song did not start and nothing said why.
        helper, resolved = self.play(False)
        resolved.assert_not_called()

    def test_kodi_21_is_spared_the_two_properties_it_warns_about(self):
        _, resolved = self.play(True, '21.3')
        self.assertFalse({'inputstream.adaptive.manifest_type', 'inputstream.adaptive.manifest_update_parameter'}
                         & set(resolved.call_args.kwargs['listitem'].properties))
        _, resolved = self.play(True, '20.5')
        self.assertEqual(resolved.call_args.kwargs['listitem'].properties['inputstream.adaptive.manifest_type'], 'mpd')


class LicenseUrl(AddonTest):
    def test_the_license_request_goes_through_the_proxy_to_amazon(self):
        invoke('mode=getTrack&asin=B0ASONG001')
        signed_in(AMaccess()).REGION = 'ZAZ'
        Kodi.settings['proxy'] = '127.0.0.1:4711'
        url, headers = AMplay().getLicenseServer()
        parsed = urlparse(url)
        self.assertEqual((parsed.netloc, parsed.path), ('127.0.0.1:4711', '/license'))
        self.assertEqual(dict(parse_qsl(parsed.query)), {'url': LICENSE_URL})
        self.assertNotIn('|', url)
        self.assertIn('Authorization=Bearer%20access-token', headers)


class LicenseProxy(AddonTest):
    def setUp(self):
        super().setUp()
        proxy.ProxyHTTPD.lastTold = 0
        self.proxy = ProxyTCPD()
        threading.Thread(target=self.proxy.serve_forever, daemon=True).start()

    def tearDown(self):
        self.proxy.shutdown()
        self.proxy.server_close()
        super().tearDown()

    def ask(self, target=LICENSE_URL, answer=None):
        """What inputstream.adaptive gets, and what the proxy asked Amazon for."""
        answer = answer or Response({'license': 'TElDRU5TRQ=='})
        answer.content = answer.text.encode('utf-8')
        answer.headers = {'Content-Type': 'application/json'}
        asked = self.patch(proxy.requests, 'post', return_value=answer)
        request = urllib.request.Request(
            'http://127.0.0.1:{}/license?{}'.format(self.proxy.port, urllib.parse.urlencode({'url': target})),
            data=b'{"licenseChallenge":"Q0hBTExFTkdF"}',
            headers={'X-Amz-Target': 'target', 'csrf-token': 'csrf', 'Host': 'music.amazon.de'})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.read(), asked
        except HTTPError as error:
            return error.code, error.read(), asked

    def test_the_request_reaches_amazon_unchanged_and_the_license_comes_back(self):
        status, body, asked = self.ask()
        self.assertEqual((status, json.loads(body)), (200, {'license': 'TElDRU5TRQ=='}))
        self.assertEqual(asked.call_args.args[0], LICENSE_URL)
        self.assertEqual(asked.call_args.kwargs['data'], b'{"licenseChallenge":"Q0hBTExFTkdF"}')
        sent = {key.lower(): value for key, value in asked.call_args.kwargs['headers'].items()}
        self.assertEqual((sent['x-amz-target'], sent['csrf-token']), ('target', 'csrf'))
        # requests names the host of Amazon itself; the one of the hop to the proxy is not passed on.
        self.assertFalse({'host', 'content-length'} & set(sent))

    def test_only_amazon_music_is_passed_on_to(self):
        for target in ('https://example.com/ZAZ/api/dmls/', 'http://music.amazon.de/ZAZ/api/dmls/',
                       'https://music.amazon.de.example.com/ZAZ/api/dmls/'):
            with self.subTest(target=target):
                status, body, asked = self.ask(target)
                self.assertEqual(status, 501)
                asked.assert_not_called()

    def test_a_refusal_for_vmp_is_remembered_and_the_user_is_told_to_start_again(self):
        refused = Response({'__type': 'com.amazon.digitalmusiclocator#DrmLicenseDeniedException',
                            'DrmType': 'WIDEVINE', 'denialReason': 'VMP_VALIDATION_FAILED'}, 400)
        status, body, asked = self.ask(answer=refused)
        # inputstream.adaptive gets the answer of Amazon as it is.
        self.assertEqual((status, json.loads(body)['denialReason']), (400, 'VMP_VALIDATION_FAILED'))
        self.assertTrue(os.path.isfile(os.path.join(Kodi.profile, 'vmp-unverified')))
        self.assertEqual([n['message'] for n in Kodi.notifications], [text(30080)])
        proxy.ProxyHTTPD.lastTold = 0
        # The same refusal again is not reported a second time.
        self.ask(answer=refused)
        self.assertEqual(len(Kodi.notifications), 1)

    def test_any_other_refusal_is_not_taken_for_a_missing_vmp_and_names_its_reason(self):
        status, body, asked = self.ask(answer=Response({'denialReason': 'DEVICE_NOT_ELIGIBLE'}, 400))
        self.assertEqual(status, 400)
        self.assertFalse(os.path.isfile(os.path.join(Kodi.profile, 'vmp-unverified')))
        self.assertEqual([n['message'] for n in Kodi.notifications], [text(30081).format('DEVICE_NOT_ELIGIBLE')])

    def test_an_untrusted_widevine_library_is_named_once_however_many_songs_are_refused(self):
        # Seen with Kodi 20 on Linux and a Widevine library of April 2024.
        refused = Response({'denialReason': 'UNTRUSTED_DEVICE_CERTIFICATE'}, 400)
        for song in range(3):
            self.ask(answer=refused)
        self.assertEqual([(n['message'], n['icon']) for n in Kodi.notifications], [(text(30082), 'error')])
        self.assertFalse(os.path.isfile(os.path.join(Kodi.profile, 'vmp-unverified')))


if __name__ == '__main__':
    unittest.main()
