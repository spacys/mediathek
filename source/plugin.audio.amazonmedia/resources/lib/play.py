#!/usr/bin/env python
# -*- coding: utf-8 -*-

from resources.lib.tools import AMtools
from resources.lib.api import AMapi
from resources.lib.amzcall import AMcall
from resources.lib.singleton import Singleton
from urllib.parse import quote as urlquote
import json, re, os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs

class AMplay(Singleton):
    def __init__(self):
        self._t = AMtools()
        self._a = AMapi()
        self._c = AMcall()

    def getTrack(self,asin,objectId):
        song    = self.tryGetStream(asin,objectId)
        stream  = {'ia':False, 'lic':False}
        if song == None:
            manifest = self.tryGetStreamHLS(asin,objectId)
            if manifest:
                song = self.writeSongFile(manifest,'m3u8')
        if song == None:
            manifest = self.tryGetStreamDash(asin,objectId)
            if manifest:
                song = self.writeSongFile(manifest,'mpd')
                song = 'http://{}/mpd/{}'.format(self._t.getSetting('proxy'),'song.mpd')
                stream['ia']  = True
                stream['lic'] = True
        if song == None:
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self._t.getTranslation(30073),' ',self._t.getTranslation(30074)))
            return False
        self.finalizeItem(song,stream['ia'],stream['lic'])

    def tryGetStream(self,asin,objectId):
        if objectId == None:
            resp = self._c.amzCall('APIstream','getTrack',None,asin,'ASIN')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['statusCode'] == 'MAX_CONCURRENCY_REACHED':
                xbmc.PlayList(0).clear()
                xbmc.Player().stop()
                xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self._t.getTranslation(30073),' ',self._t.getTranslation(30075)))
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        else:
            resp = self._c.amzCall('APIstream','getTrack',None,objectId,'COID')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['contentResponse']['statusCode'] == 'CONTENT_NOT_ELIGIBLE' or obj['contentResponse']['statusCode'] == 'BAD_REQUEST':
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        return song

    def tryGetStreamHLS(self,asin,objectId):
        resp = self._c.amzCall('APIstreamHLS','getTrackHLS',None,asin,'ASIN')
        return re.compile('manifest":"(.+?)"',re.DOTALL).findall(resp.text)

    def tryGetStreamDash(self,asin,objectId):
        resp = self._c.amzCall('APIstreamDash','getTrackDash',None,asin,'ASIN')
        return json.loads(resp.text)['contentResponseList'][0]['manifest']

    def finalizeItem(self,song,ia=False,lic=False):
        inf = {
            'tracknumber':  int(self._t.addonArgs.get('tracknumber', [0])[0] ),
            'discnumber':   int(self._t.addonArgs.get('discnumber',  [0])[0] ),
            'duration':     int(self._t.addonArgs.get('duration',    [0])[0] ),
            'year':         int(self._t.addonArgs.get('year',     [1900])[0] ),
            'genre':            self._t.addonArgs.get('genre',      [''])[0],
            'album':            self._t.addonArgs.get('album',      [''])[0],
            'artist':      [    self._t.addonArgs.get('artist',     [''])[0] ],
            'rating':       float(self._t.addonArgs.get('rating',    [0])[0] )
        }

        li = xbmcgui.ListItem(path=song, label=self._t.addonArgs.get('title', [None])[0])
        if ia:
            li.setMimeType('application/xml+dash')
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.stream_headers', 'user-agent={}'.format(self._t.getSetting('userAgent')))
            li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            if lic:
                li.setProperty('inputstream.adaptive.license_key', self.getLicenseKey() )
            li.setInfo('video', inf)
        inf['artist'] = str(inf['artist'][0])
        li.setProperty('isFolder', 'false')
        li.setProperty('IsPlayable', 'true')
        li.setArt({'thumb':self._t.addonArgs.get('art', [None])[0]})
        li.setInfo('audio', {'codec': 'aac'})
        li.addStreamInfo('audio', {'codec': 'aac'})
        li.setContentLookup(False)
        li.setInfo('music', inf)
        xbmcplugin.setResolvedUrl(self._t.addonHandle, True, listitem=li)

    def getLicenseKey(self):
        amzUrl = self._a.getAPI('APILicenseForPlaybackV2')
        url = '{}/{}/api/{}'.format(self._t.url, self._t.region, amzUrl['path'])
        head = self._t.prepReqHeader(amzUrl['target'])

        cookiedict = {}
        for cookie in self._t.cj:
            cookiedict[cookie.name] = cookie.value

        cj_str = ';'.join(['%s=%s' % (k, v) for k, v in cookiedict.items()])

        head['Cookie'] = cj_str
        licHeader = '&'.join(['%s=%s' % (k, urlquote(v, safe='')) for k, v in head.items()])
        licBody = self._c.prepReqData('getLicenseForPlaybackV2')
        # licURL expect (req | header | body | response)
        return '{}|{}|{}|JBlicense'.format(url,licHeader,licBody)

    def writeSongFile(self,manifest,ftype='m3u8'):
        song = '{}{}song.{}'.format(self._t.addonUDatFo, os.sep, ftype)
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