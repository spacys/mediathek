#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib.parse import quote as urlquote
import json, re, os, base64
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
        self._a = AMapi()
        self._c = AMcall()
        song    = self.tryGetStream( asin, objectId )
        stream  = {'ia':False, 'lic':False}
        if song == None:
            manifest = self.tryGetStreamHLS( asin )
            if manifest:
                song = self.writeSongFile( manifest, 'm3u8' )
        if song == None:
            manifest = self.tryGetStreamDash( asin )
            if manifest:
                song = self.writeSongFile( manifest, 'mpd' )
                song = 'http://{}/mpd/{}'.format( self.getSetting('proxy'), 'song.mpd' )
                stream['ia']  = True
                stream['lic'] = True
        if song == None:
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.getTranslation(30073),' ',self.getTranslation(30074)))
            return False
        self.finalizeItem( song, stream['ia'], stream['lic'] )

    def tryGetStream( self, asin, objectId ):
        """
        Try to get manifest data from the default endpoint
        :param str asin:        unique song ID
        :param str objectId:    2nd unique song ID
        """
        if objectId == None:
            resp = self._c.amzCall( 'APIstream', 'getTrack', None, asin, 'ASIN' )
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['statusCode'] == 'MAX_CONCURRENCY_REACHED':
                xbmc.PlayList(0).clear()
                xbmc.Player().stop()
                xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.getTranslation(30073),' ',self.getTranslation(30075)))
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        else:
            resp = self._c.amzCall( 'APIstream', 'getTrack', None, objectId, 'COID' )
            obj = json.loads(resp.text)
            # self.log(obj)
            try:
                if 'statusCode' in obj and obj['contentResponse']['statusCode'] == 'CONTENT_NOT_ELIGIBLE' or obj['contentResponse']['statusCode'] == 'BAD_REQUEST':
                    return None
            except:
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        return song

    def tryGetStreamHLS( self, asin ):
        """
        Try to get manifest data from the HLS endpoint
        :param str asin:        unique song ID
        """
        resp = self._c.amzCall( 'APIstreamHLS', 'getTrackHLS', None, asin, 'ASIN' )
        return re.compile('manifest":"(.+?)"',re.DOTALL).findall(resp.text)

    def tryGetStreamDash(self,asin):
        """
        Try to get manifest data from the DASH endpoint
        :param str asin:        unique song ID
        """
        resp = self._c.amzCall( 'APIstreamDash', 'getTrackDash', None, asin, 'ASIN' )
        return json.loads(resp.text)['contentResponseList'][0]['manifest']

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
        info_tag = self.setItemTags(li, 'video')
        info_tag.set_info(inf)
        if ia:
            li.setMimeType('application/xml+dash')
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.manifest_headers', 'user-agent={}'.format(self.userAgent))
            li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            if lic:
                li.setProperty('inputstream.adaptive.license_key', self.getLicenseKey() )

        li.setProperty('isFolder', 'false')
        li.setProperty('IsPlayable', 'true')
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.G['addonHandle'], True, listitem=li)

    def getLicenseKey( self ):
        """
        Preparation for license key request, further communication will be managed by inpustream adaptive
        """
        amzUrl = self._a.getAPI('APILicenseForPlaybackV2')
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
        licHeader = '&'.join(['%s=%s' % (k, urlquote(v, safe='')) for k, v in head.items()])
        #self.log(licHeader)
        licBody = self._c.prepReqData('getLicenseForPlaybackV2')
        #self.log(licBody)
        # licURL expect (req | header | body | response)
        return '{}|{}|{}|JBlicense'.format( url, licHeader, licBody )

    def writeSongFile( self, manifest, ftype='m3u8' ):
        """
        Write the song manifest data to a local file, returns the file path
        :param str/xml manifest:    manifest data of the song
        :param str ftype:           file extension
        """
        song = '{}{}song.{}'.format( self.G['addonUDatFo'], os.sep, ftype )
        m3u_string = ''
        temp_file = xbmcvfs.File(song, 'w')
        if ftype == 'm3u8':
            m3u_string = manifest[0]
        if ftype == 'mpd':
            m3u_string = manifest
            song = song.replace("\\","/") # windows fix that inputstream can work properly
        m3u_string = m3u_string.replace("\\n", os.linesep)
        temp_file.write(m3u_string)
        temp_file.close()
        return song