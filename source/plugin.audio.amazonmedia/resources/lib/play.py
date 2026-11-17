#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib.parse import quote as urlquote, urlencode
import base64, json, os, re
import xbmc, xbmcgui, xbmcplugin, xbmcvfs

from resources.lib.api import AMapi
from resources.lib.tools import AMtools
from resources.lib.amzcall import AMcall

class AMplay( AMtools ):
    """
    Item playback class, call Amazon API to get streaming meta data and create a Kodi list item for blayback
    """
    def getTrack( self, asin, objectId ):
        """
        Main entry point for playback. 'asin' is the common parameter for remote items. \n
        In some cases is no 'asin' available, then 'objectId' is used
        :param str asin:        unique song ID
        :param str objectId:    2nd unique song ID
        """
        self.credentials = self.load()
        self._c = AMcall()
        if objectId:
            # A song of the personal library: what the customer owns is streamed as a plain
            # file, which plays on every platform. Anything else is refused here and goes on.
            song = self.tryGetStreamCoid( objectId )
            if song:
                self.finalizeItem( song )
                return True
        if self._c.licenseOutOfReach():
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            xbmcgui.Dialog().notification(xbmc.getLocalizedString(257), self.getTranslation(30083), xbmcgui.NOTIFICATION_ERROR, 6000)
            return False
        manifest, status = self.tryGetStreamDash( asin or objectId, 'ASIN' if asin else 'COID' )
        if not manifest:
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            reason = {'MAX_CONCURRENCY_REACHED': 30075, 'CONTENT_NOT_ELIGIBLE': 30078}.get(status, 30074)
            xbmcgui.Dialog().notification(xbmc.getLocalizedString(257), '{} {}'.format(self.getTranslation(30073), self.getTranslation(reason)),
                                          xbmcgui.NOTIFICATION_ERROR, 10000)
            return False
        if not self.widevineReady():
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            return False
        self.writeSongFile( manifest )
        song = 'http://{}/mpd/{}'.format( self.getSetting('proxy'), 'song.mpd' )
        self.finalizeItem( song, True, True )

    def widevineReady( self ):
        """
        Have InputStream Helper see to it that InputStream Adaptive and the Widevine library are
        there and up to date; it offers to install what is missing. A fresh Kodi on a desktop
        has no Widevine library, and the song then just does not start.
        :return: False when the user declined or the installation failed
        """
        try:
            import inputstreamhelper
        except ImportError:
            return True
        return bool( inputstreamhelper.Helper('mpd', drm='com.widevine.alpha').check_inputstream() )

    def tryGetStreamCoid( self, objectId ):
        """
        Get the streaming URL of a song the customer owns, or None
        :param str objectId:    unique song ID of the personal library
        """
        try:
            resp = self._c.amzCall( 'APIstreamCoid', 'getTrackCoid', None, objectId )
            content = ( json.loads(resp.text).get('contentResponseList') or [{}] )[0]
        except (ValueError, AttributeError):
            return None
        urls = content.get('urlList') or []
        if content.get('statusCode', 'SUCCESS') != 'SUCCESS' or not urls:
            self.log('No streaming URL for {}: {}'.format(objectId, content.get('statusCode')))
            return None
        return urls[0]

    def tryGetStreamDash( self, identifier, identifierType ):
        """
        Get the DASH manifest of the song and the status Amazon answered with
        :param str identifier:      unique song ID
        :param str identifierType:  type of the given ID, 'ASIN' or 'COID'
        """
        resp = self._c.amzCall( 'APIstreamDash', 'getTrackDash', None, identifier, identifierType )
        content = ( json.loads(resp.text).get('contentResponseList') or [{}] )[0]
        status = content.get('contentResponseStatusCode')
        if status != 'SUCCESS':
            self.log('No manifest for {}: {} {}'.format(
                identifier, status, content.get('contentResponseStatusMessage')))
            return None, status
        # Amazon hands the manifest over with its line breaks and quotes escaped.
        manifest = (content.get('manifest') or '').replace('\\n', '\n').replace('\\"', '"')
        self.log('Manifest for {}: {}'.format(identifier, self.manifestSummary(manifest)))
        if not self._c.verifiedMediaPath():
            manifest = self.onlyUnverified(manifest)
            self.log('Kept for a player without Verified Media Path: {}'.format(self.manifestSummary(manifest)))
        return manifest, status

    SETS = re.compile(r'<AdaptationSet\b.*?</AdaptationSet>', re.S)
    REPRESENTATIONS = re.compile(r'<Representation\b[^>]*?/>|<Representation\b.*?</Representation>', re.S)
    TRACK_TYPE = re.compile(r'schemeIdUri="amz-music:trackType"[^>]*?value="([^"]+)"|value="([^"]+)"[^>]*?schemeIdUri="amz-music:trackType"')

    @classmethod
    def trackType( cls, xml ):
        found = cls.TRACK_TYPE.search(xml)
        return (found.group(1) or found.group(2)) if found else None

    @classmethod
    def manifestSummary( cls, manifest ):
        """What a manifest offers: its qualities with their type, codec and bandwidth; nothing of the account"""
        offered = []
        for block in cls.SETS.findall(manifest):
            of_set = cls.trackType(cls.REPRESENTATIONS.sub('', block))
            set_codec = (re.search(r'<AdaptationSet\b[^>]*?codecs="([^"]+)"', block) or [None, None])[1]
            for rep in cls.REPRESENTATIONS.findall(block):
                codec = (re.search(r'codecs="([^"]+)"', rep) or [None, set_codec])[1]
                bandwidth = (re.search(r'bandwidth="(\d+)"', rep) or [None, '?'])[1]
                offered.append('{}{} {} {}'.format(cls.trackType(rep) or of_set, '' if cls.trackType(rep) else '(set)', codec, bandwidth))
        return '{} sets, {}'.format(len(cls.SETS.findall(manifest)), offered)

    @classmethod
    def onlyUnverified( cls, manifest ):
        """
        Leave only the quality Amazon licenses to a player without a Verified Media Path, the one
        marked as track type "LD". The web player chooses among the qualities the same way. \n
        The manifest is cut as text: written anew, its namespace prefixes would change, and
        InputStream Adaptive finds the protection data by them.
        :return: the manifest unchanged when it names no such quality
        """
        kept = [0]
        def cut( block ):
            block = block.group(0)
            of_set = cls.trackType(cls.REPRESENTATIONS.sub('', block))
            reps = cls.REPRESENTATIONS.findall(block)
            keep = [rep for rep in reps if (cls.trackType(rep) or of_set) == 'LD']
            kept[0] += len(keep)
            if not keep:
                return ''
            for rep in reps:
                if rep not in keep:
                    block = block.replace(rep, '', 1)
            return block
        cut_down = cls.SETS.sub(cut, manifest)
        return cut_down if kept[0] else manifest

    def finalizeItem( self, song, ia=False, lic=False ):
        """
        Create Kodi list item and resolve stream endpoint
        :param str song:        path to the manifest song file
        :param bool ia:         inputstream adaptive necessary?
        :param bool lic:        license for playback necessary?
        """
        inf  = {}
        data = {
            'tracknumber',
            'discnumber',
            'duration',
            'year',
            'genre',
            'album',
            'artist',
            'rating'
        }
        for item in data:
            if not self.G['addonArgs'].get(item, [None])[0] == None:
                if ('artist' in item or 'genre' in item):
                    inf[item] = [ self.G['addonArgs'].get(item, [None])[0] ]
                else:
                    inf[item] = self.G['addonArgs'].get(item, [None])[0]

        li = xbmcgui.ListItem(path=song, label=self.G['addonArgs'].get('title', [None])[0])        
        # Tagged as music, Kodi hands the item to PAPlayer, which cannot decode the DRM protected stream.
        info_tag = self.setItemTags(li, 'video')
        info_tag.set_info(inf)
        if ia:
            li.setMimeType('application/xml+dash')
            li.setProperty('inputstream', 'inputstream.adaptive')
            if self.getKodiVersion() < 21:
                # Kodi 21 detects the manifest type itself and warns about these two properties.
                li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            li.setProperty('inputstream.adaptive.manifest_headers', 'user-agent={}'.format(self.userAgent))
            if lic:
                self.setLicense( li )

        li.setProperty('isFolder', 'false')
        li.setProperty('IsPlayable', 'true')
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.G['addonHandle'], True, listitem=li)

    def setLicense( self, li ):
        """
        Hand the license request to inputstream adaptive, further communication will be managed by it
        :param ListItem li: the item to play
        """
        url, licHeader = self.getLicenseServer()
        # Amazon wants the challenge base64 encoded in a JSON request, and answers with the
        # license base64 encoded in the field 'license' of a JSON response.
        if self.getKodiVersion() >= 22:
            licBody = AMcall().prepReqData('getLicenseForPlaybackV2', None, '{CHA-B64}')
            li.setProperty('inputstream.adaptive.drm', json.dumps({'com.widevine.alpha': {'license': {
                'server_url':       url,
                'req_headers':      licHeader,
                'req_data':         base64.b64encode(licBody.encode('utf-8')).decode('ascii'),
                'unwrapper':        'json,base64',
                'unwrapper_params': {'path_data': 'license'}
            }}}))
        else:
            licBody = AMcall().prepReqData('getLicenseForPlaybackV2', None, 'b{SSM}')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            # licURL expect (req | header | body | response), the access token contains a '|'
            li.setProperty('inputstream.adaptive.license_key', '{}|{}|{}|JBlicense'.format(
                url, licHeader, licBody.replace('|', '\\u007c')))

    def getLicenseServer( self ):
        """
        URL and HTTP headers of the license request
        """
        amzUrl = AMapi.getAPI('APILicenseForPlaybackV2')
        url = '{}/{}/api/{}'.format(
            self.musicURL.format( self.credentials.USERTLD ),
            self.credentials.REGION,
            amzUrl['path'])
        head = self.prepReqHeader( amzUrl['target'] )

        cookiedict = {}
        for cookie in self.credentials.COOKIE:
            cookiedict[cookie.name] = cookie.value

        cj_str = ';'.join(['%s=%s' % (k, v) for k, v in cookiedict.items()])

        head['Cookie'] = cj_str
        # Through the proxy, which passes the request on and reads why a license was refused.
        proxy = self.getSetting('proxy')
        if proxy:
            url = 'http://{}/license?{}'.format( proxy, urlencode({'url': url}) )
        return url, '&'.join(['%s=%s' % (k, urlquote(v, safe='')) for k, v in head.items()])

    @staticmethod
    def getKodiVersion():
        """
        Major version of the running Kodi
        """
        return int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])

    def writeSongFile( self, manifest ):
        """
        Keep the manifest of the song where the proxy hands it to InputStream Adaptive
        :param str manifest:    DASH manifest of the song
        """
        temp_file = xbmcvfs.File( os.path.join(self.G['addonUDatFo'], 'song.mpd'), 'w' )
        temp_file.write( manifest )
        temp_file.close()
