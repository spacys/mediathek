#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# import urllib.parse as urlparse
from urllib.parse import quote as urlquote
from urllib.parse import quote_plus as urlquoteplus
from urllib.parse import urlencode as urlencode

import requests
# import mechanize
# import http.cookiejar as cookielib
# import sys
import re
import os
import json
# import shutil
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
# import xbmcaddon
import xbmcvfs
# from bs4 import BeautifulSoup
import datetime
#import base64

from resources.lib.settings import Settings
from resources.lib.menu import MainMenu
from resources.lib.api import API
from resources.lib.logon import Logon
from resources.lib.amzcall import AMZCall

NODEBUG = False

class AmazonMedia():
    __slots__ = ['addon','addonId','addonName','addonFolder','addonUDatFo','addonBaseUrl','addonHandle','addonArgs','addonMode','siteVerList','siteVersion','logonURL',
        'musicURL','saveUsername','savePassword','userEmail','userPassword','userAgent','deviceId','csrf_token','csrf_ts','csrf_rnd','customerId','marketplaceId','deviceType','musicTerritory','locale','customerLang',
        'region','url','access','accessType','maxResults','audioQualist','audioQuality','cj','logging','showimages','showUnplayableSongs','showcolentr','sPlayLists','sAlbums','sSongs',
<<<<<<< HEAD
        'sStations','sArtists','addonFolRes','addonIcon','defFanart','cookieFile','br','content','AMs','AMm','AMl','AMapi','AMc']
    def __init__(self):
        self.setVariables()
        if self.AMs.logging:
            self.AMs.log( 'Handle: ' + self.AMs.addonHandle.__str__() + '\n'
                    + 'Args  : ' + self.AMs.addonArgs.__str__() + '\n'
                    + 'Mode  : ' + self.AMs.addonMode.__str__())
    # def __del__(self):
    #     ''' Cleanup instances '''
    #     del self.AMs.addon.addonId
    def setVariables(self):
        self.AMs    = Settings()
        self.AMm    = MainMenu(self.AMs)
        self.AMl    = Logon(self.AMs)
        self.AMapi  = API()
        self.AMc    = AMZCall(self.AMs,self.AMl)
=======
        'sStations','sArtists','addonFolRes','addonIcon','defFanart','cookieFile','br','content','captcha',
        'API_getBrowseRecommendations','API_lookup','API_getAddToLibraryRecommendations','API_getSimilarityRecommendations','API_getMusicStoreRecommendations',
        'API_artistDetailCatalog','API_getStationSections','API_artistDetailsMetadata','API_getTopMusicEntities','API_browseHierarchyV2','API_seeMore','API_getHome',
        'API_lookupStationsByStationKeys','API_createQueue','API_QueueGetNextTracks',
        'API_stream','API_streamHLS','API_streamDash','API_LicenseForPlaybackV2','API_search','API_cirrus','API_cirrusV1','API_cirrusV2','API_cirrusV3',
        'API_V3getTracksByAsin','API_V3getTracks','API_V3getTracksById',
        'API_getPlaylistsByIdV2','API_getPubliclyAvailablePlaylistsById','API_sociallySharePlaylist','API_getConfigurationV2','API_getFollowedPlaylistsInLibrary','API_getOwnedPlaylistsInLibrary',
        'API_GetRecentTrackActivity','API_GetRecentActivity',
        'API_GetSoccerMain','API_GetSoccerProgramDetails','API_GetSoccerLiveURLs','API_GetSoccerOnDemandURLs',
        'Q_getServerSongs','Q_getAllDataCountByMetaType','Q_getAllDataByMetaType','Q_getAlbumsCountForMetatype','Q_getAlbumsForMetatype','Q_getSongForPlayerBySearchLibrary',
        'Q_getTracks','Q_getTracksByAlbum','Q_getServerListSongs']
    def __init__(self):
        self.setVariables()
        self.prepFolder()
        self.prepBrowser()
        self.setAPIConstants()
        self.setQueryConstants()
        if self.logging:
            self.log( 'Handle: ' + self.addonHandle.__str__() + '\n'
                    + 'Args  : ' + self.addonArgs.__str__() + '\n'
                    + 'Mode  : ' + self.addonMode.__str__())
    def __del__(self):
        ''' Cleanup instances '''
        del self.addonId
    def setVariables(self):
        self.addon        = xbmcaddon.Addon()
        self.addonId      = self.getInfo('id')
        self.addonName    = self.getInfo('name')
        self.addonFolder  = self.getFolder("special://home/addons/" + self.addonId)
        self.addonUDatFo  = self.getFolder("special://profile/addon_data/" + self.addonId)
        self.addonBaseUrl = sys.argv[0]
        self.addonHandle  = int(sys.argv[1])
        self.addonArgs    = urlparse.parse_qs(sys.argv[2][1:])
        self.addonMode    = self.addonArgs.get('mode', None)
        self.siteVerList  = ["de", "fr", "co.uk", "it", "es"]
        self.siteVersion  = self.getSetting("siteVersion")
        self.logonURL     = 'https://www.amazon.{}/gp/aw/si.html'.format(self.siteVerList[int(self.siteVersion)])
        self.musicURL     = 'https://music.amazon.{}'.format(self.siteVerList[int(self.siteVersion)])
        self.saveUsername = self.toBool(self.getSetting("saveUsername"))
        if not self.saveUsername:
            self.setSetting('savePassword', "false")
            self.setSetting('userEmail', "")
            self.setSetting('userPassword', "")
        self.savePassword = self.toBool(self.getSetting("savePassword"))
        if not self.savePassword:
            self.setSetting('userPassword', "")
        self.userEmail    = self.getSetting("userEmail")
        self.userPassword = base64.urlsafe_b64decode(self.getSetting("userPassword"))
        self.captcha      = ""
        self.userAgent    = self.getSetting("userAgent")
        self.deviceId     = self.getSetting("deviceId")
        self.csrf_token   = self.getSetting("csrf_token")
        self.csrf_ts      = self.getSetting("csrf_ts")
        self.csrf_rnd     = self.getSetting("csrf_rnd")
        self.customerId   = self.getSetting("customerId")
        self.marketplaceId = self.getSetting("marketplaceId")
        self.deviceType   = self.getSetting("deviceType")
        self.musicTerritory = self.getSetting("musicTerritory")
        self.locale       = self.getSetting("locale")
        self.customerLang = self.getSetting("customerLang")
        self.region       = self.getSetting("region")
        self.url          = self.getSetting("url")
        self.access       = self.toBool(self.getSetting("access"))
        self.accessType   = self.getSetting("accessType")
        self.maxResults   = 50
        self.audioQualist = ["HIGH","MEDIUM","LOW"]
        self.audioQuality = self.audioQualist[int(self.getSetting("quality"))]
        self.cj           = cookielib.MozillaCookieJar()
        self.logging      = self.toBool(self.getSetting("logging"))
        self.showimages   = self.toBool(self.getSetting("showimages"))
        self.showUnplayableSongs = self.toBool(self.getSetting("showUnplayableSongs"))
        self.showcolentr  = self.toBool(self.getSetting("showcolentr"))
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7

    def reqDispatch(self):
        # reset addon
        if self.AMs.addonMode is not None and self.AMs.addonMode[0] == 'resetAddon':
            self.AMs.resetAddon()
            xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self.AMs.translation(30071)))
            return
        # logon
        # if not self.AMs.access and not self.AMl.amazonLogon():
        #     xbmc.executebuiltin('Notification("Error:", %s, 5000, )'%(self.AMs.translation(30070)))
        #     return
        if not self.AMs.access:
            if not self.AMl.amazonLogon():
                xbmc.executebuiltin('Notification("Error:", {}, 5000, )'.format(self.AMs.translation(30070)))
                return

        if self.AMs.addonMode is None:
            mode = None
        else:
            mode = self.AMs.addonMode[0]

        if mode is None:
            #self.menuHome()
            self.createList(self.AMm.menuHome())
        elif mode == 'menuPlaylists':
            self.createList(self.AMm.menuPlaylists(),True)
        elif mode == 'menuAlbums':
            self.createList(self.AMm.menuAlbums(),True)
        elif mode == 'menuSongs':
            self.createList(self.AMm.menuSongs(),True)
        elif mode == 'menuStations':
            self.createList(self.AMm.menuStations(),True)
        elif mode == 'menuArtists':
            self.createList(self.AMm.menuArtists(),True)
        elif mode == 'menuSoccer':
            self.createList(self.AMm.menuSoccer())
            #self.menuSoccer()

        elif mode == 'searchPlayLists':
            self.searchItems(['playlists','catalog_playlist'],30013)
        elif mode in ['search1PlayLists','search2PlayLists','search3PlayLists']:
            exec('self.searchItems([\'playlists\',\'catalog_playlist\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchAlbums':
            self.searchItems(['albums','catalog_album'],30010)
        elif mode in ['search1Albums','search2Albums','search3Albums']:
            exec('self.searchItems([\'albums\',\'catalog_album\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchSongs':
            self.searchItems(['tracks','catalog_track'],30011)
        elif mode in ['search1Songs','search2Songs','search3Songs']:
            exec('self.searchItems([\'tracks\',\'catalog_track\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchArtist':
            self.searchItems(['artists','catalog_artist'],30014)
        elif mode in ['search1Artists','search2Artists','search3Artists']:
            exec('self.searchItems([\'artists\',\'catalog_artist\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'searchStations':
            self.searchItems(['stations','catalog_station'],30016)
        elif mode in ['search1Stations','search2Stations','search3Stations']:
            exec('self.searchItems([\'stations\',\'catalog_station\'],None,self.AMs.getSetting("{}"))'.format(mode))

        elif mode == 'getArtistDetails':
            asin = self.AMs.addonArgs.get('asin', [None])
            self.getArtistDetails(asin[0])

        elif mode == 'getRecentlyPlayed':
            self.getRecentlyPlayed('PLAYED')
        elif mode == 'getRecentlyAddedSongs':
            self.getRecentlyAddedSongs()

        elif mode == 'getPopularPlayLists':
            self.getPlayLists('popularity-rank')
        elif mode == 'getNewPlayLists':
            self.getPlayLists('newly-released')
        elif mode == 'getFollowedPlayLists':
            self.getFollowedPlayLists()
        elif mode == 'getOwnedPlaylists':
            self.getOwnedPlaylists()
        elif mode == 'getPlaylistsByIdV2':
            asin = self.AMs.addonArgs.get('asin', [None])
            self.getPlaylistsByIdV2(asin[0])

        elif mode == 'getRecomPlayLists':
            self.getRecommendations('playlists','mp3-prime-browse-carousels_playlistStrategy')
        elif mode == 'getRecomAlbums':
            self.getRecommendations('albums','mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy')
        elif mode == 'getRecomStations':
            self.getRecommendations('stations','mp3-prime-browse-carousels_mp3ArtistStationStrategy')

        elif mode == 'getNewRecom':
            self.getNewRecommendations()
        elif mode == 'getNewRecomDetails':
            asin = self.AMs.addonArgs.get('target', [None])
            self.getNewRecomDetails(asin[0])
        # get own music, differentiate betwenn purchased and own lib
        # param: searchReturnType , caller, sortCriteriaList.member.1.sortColumn
        elif mode in ['getPurAlbums','getAllAlbums']:
            self.getPurchased(['ALBUMS','getAllDataByMetaType','sortAlbumName'],'albums')
        elif mode in ['getAllSongs','getPurSongs']:
            self.getPurchased(['TRACKS','getServerSongs','sortTitle'],'songs')
        # get amazon stations
        elif mode in ['getStations','getAllArtistsStations','getGenres','getGenres2']:
            self.getStations(mode.replace('get','').lower())
        elif mode in ['getGenrePlaylist','createQueue']:
            asin = self.AMs.addonArgs.get('asin', None)
            exec('self.{}(asin[0])'.format(mode))
        # get song lists
        elif mode == 'lookup':
            asin = self.AMs.addonArgs.get('asin', None)
            self.lookup(asin)
        # play the song
        elif mode == 'getTrack':
            asin = self.AMs.addonArgs.get('asin', [None])[0]
            objectId = self.AMs.addonArgs.get('objectId', [None])[0]
            self.getTrack(asin,objectId)
        # Amazon Soccer Live
        elif mode in ['soccerBUND','soccerBUND2','soccerCHAMP','soccerDFBPOKAL','soccerSUPR']:
            self.getSoccerFilter(mode.replace('soccer',''))
        elif mode == 'getSoccerLive':
<<<<<<< HEAD
            objectId = self.AMs.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'LIVE')
        elif mode == 'getSoccerOnDemand':
            objectId = self.AMs.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'ONDEMAND')
=======
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'LIVE')
        elif mode == 'getSoccerOnDemand':
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'ONDEMAND')
    def translation(self,oId):
        return self.addon.getLocalizedString(oId).encode('utf-8')
    def getInfo(self,oProp):
        return self.addon.getAddonInfo(oProp)
    def getSetting(self,oProp):
        return self.addon.getSetting(oProp)
    def setSetting(self,oProp,val):
        self.addon.setSetting(oProp,val)
    def toBool(self,s):
        if s == 'True' or s == 'true':
             return True
        else:
             return False
    def setContent(self,cont):
        xbmcplugin.setContent(int(sys.argv[1]), cont)
    def setCookie(self):
        self.cj.save(self.cookieFile, ignore_discard=True, ignore_expires=True)
    def setSearch(self,item,query):
        q = []
        update = True
        if   item == 'playlists':
            q = self.sPlayLists
        elif item == 'albums':
            q = self.sAlbums
        elif item == 'tracks':
            q = self.sSongs
        elif item == 'stations':
            q = self.sStations
        elif item == 'artists':
            q = self.sArtists
        for i in q:
            if self.getSetting(i) == query:
                update = False
                break
        if update:
            self.setSetting(q[2],self.getSetting(q[1]))
            self.setSetting(q[1],self.getSetting(q[0]))
            self.setSetting(q[0],query)
    def getFolder(self,oPath):
        return xbmc.translatePath(oPath).decode('utf-8') # xbmcvfs
    def getUserInput(self,title,txt,hidden=False,uni=False):
        kb = xbmc.Keyboard()
        kb.setHeading(title)
        kb.setDefault(txt)
        kb.setHiddenInput(hidden)
        kb.doModal()
        if kb.isConfirmed() and kb.getText():
            if uni:
                try:
                    return unicode(kb.getText(), "utf-8")
                except:
                    return str(kb.getText(), encoding = 'utf-8')
            else:
                return kb.getText() # for password needed, due to encryption
        else:
            return False
    def log(self, msg, level=xbmc.LOGNOTICE):
        log_message = '[{}] {}'.format(self.addonName, msg).encode("utf-8")
        xbmc.log(log_message, level)
    def checkSiteVersion(self,siteVersion):
        if siteVersion in self.siteVerList:
            x = 0
            for i in self.siteVerList:
                if siteVersion == i:
                    self.setSetting("siteVersion", str(x))
                    break
                else:
                    x+=1
        else:
            self.setSetting("siteVersion", "0")
    # read / write config file
    def appConfig(self,app_config):
        if app_config is None:
            return False
        self.setSetting('deviceId',         app_config['deviceId'])
        self.setSetting('csrf_token',       app_config['CSRFTokenConfig']['csrf_token'])
        self.setSetting('csrf_ts',          app_config['CSRFTokenConfig']['csrf_ts'])
        self.setSetting('csrf_rnd',         app_config['CSRFTokenConfig']['csrf_rnd'])
        self.setSetting('customerId',       app_config['customerId'])
        self.setSetting('marketplaceId',    app_config['marketplaceId'])
        self.setSetting('deviceType',       app_config['deviceType'])
        self.setSetting('musicTerritory',   app_config['musicTerritory'])
        self.setSetting('locale',           app_config['i18n']['locale'])
        self.setSetting('customerLang',     app_config['customerLanguage'])
        self.setSetting('region',           app_config['realm'][:2])
        self.setSetting('url',              'https://{}'.format(app_config['serverInfo']['returnUrlServer']))
        self.setSetting('access',           'true')
        if app_config['customerBenefits']['tier'] == 'UNLIMITED_HD':
                self.setSetting('accessType', 'UNLIMITED')
        else:
            self.setSetting('accessType',   app_config['customerBenefits']['tier'])
        self.checkSiteVersion(app_config['musicTerritory'].lower())
    def appConfig2(self,app_config):
        if app_config is None:
            return False
        self.setSetting('deviceId',         app_config['deviceId'])
        self.setSetting('csrf_token',       app_config['csrf']['token'])
        self.setSetting('csrf_ts',          app_config['csrf']['ts'])
        self.setSetting('csrf_rnd',         app_config['csrf']['rnd'])
        self.setSetting('customerId',       app_config['customerId'])
        self.setSetting('marketplaceId',    app_config['marketplaceId'])
        self.setSetting('deviceType',       app_config['deviceType'])
        self.setSetting('musicTerritory',   app_config['musicTerritory'])
        self.setSetting('locale',           app_config['displayLanguage'])
        self.setSetting('customerLang',     app_config['musicTerritory'].lower())
        self.setSetting('region',           app_config['siteRegion'])
        self.setSetting('url',              self.musicURL)
        self.setSetting('access',           'true')
        if app_config['tier'] == 'UNLIMITED_HD':
                self.setSetting('accessType', 'UNLIMITED')
        else:
            self.setSetting('accessType',   app_config['tier'])
        self.checkSiteVersion(app_config['musicTerritory'].lower())
    # cleanup
    def delCookies(self):
        if os.path.exists(self.cookieFile):
            os.remove(self.cookieFile)
    def resetAddon(self):
        self.delCookies()
        settings = '{}{}{}'.format(self.addonUDatFo, os.sep, 'settings.xml')
        if os.path.exists(settings):
            os.remove(settings)
        self.setSetting('csrf_ts', "")
        self.setSetting('csrf_rnd', "")
        self.setSetting('csrf_token', "")
        self.setSetting('customerId', "")
        self.setSetting('marketplaceId', "")
        self.setSetting('deviceId', "")
        self.setSetting('deviceType', "")
        self.setSetting('musicTerritory', "")
        self.setSetting('locale', "")
        self.setSetting('customerLang', "")
        self.setSetting('region', "")
        self.setSetting('url', "")
        self.setSetting('saveUsername', "false")
        self.setSetting('savePassword', "false")
        self.setSetting('userEmail', "")
        self.setSetting('userPassword', "")
        self.setSetting('access', "false")
        self.setSetting('logging', "false")
        self.setSetting('showimages', "false")
        self.setSetting('showUnplayableSongs', "false")
        self.setSetting('showcolentr', "true")
        self.setSetting('accessType', "")
        self.setSetting('search1PlayLists', "")
        self.setSetting('search2PlayLists', "")
        self.setSetting('search3PlayLists', "")
        self.setSetting('search1Albums', "")
        self.setSetting('search2Albums', "")
        self.setSetting('search3Albums', "")
        self.setSetting('search1Songs', "")
        self.setSetting('search2Songs', "")
        self.setSetting('search3Songs', "")
        self.setSetting('search1Stations', "")
        self.setSetting('search2Stations', "")
        self.setSetting('search3Stations', "")
        self.setSetting('search1Artists', "")
        self.setSetting('search2Artists', "")
        self.setSetting('search3Artists', "")
        self.access = False
        xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self.translation(30071)))
    def delCredentials(self):
        self.userEmail = ''
        self.userPassword = ''
    def getCredentials(self):
        if not self.userEmail or not self.userPassword:
            if not self.userEmail:
                user = self.getUserInput(self.translation(30030),'', hidden=False, uni=False) # get Email
                if user:
                    self.userEmail = user
                    if self.saveUsername:
                        self.setSetting('userEmail', user)
            else:
                user = True
            if user and not self.userPassword:
                pw = self.getUserInput(self.translation(30031),'', hidden=True, uni=False) # get Password
                if pw:
                    self.userPassword = pw
                    if self.savePassword and self.saveUsername:
                        self.setSetting('userPassword', base64.urlsafe_b64encode(pw.encode("utf-8")))
                    return True
                else:
                    return False
            else:
                return False
        return True
    # web communication
    def parseHTML(self,resp):
        resp = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', resp)
        return BeautifulSoup(resp, 'html.parser')
    ################################################################################
    def setAPIConstants(self):
        """
        Amazon API definitions
        amzUrl      = AmazonBaseUrl + region + /api/ + path
        amzTarget   = target
        """
        base = 'com.amazon.musicensembleservice.MusicEnsembleService.'
        self.API_getBrowseRecommendations = {
            'path':   'muse/legacy/getBrowseRecommendations',
            'target': '{}{}'.format(base,'getBrowseRecommendations')
        }
        self.API_lookup = {
            'path':   'muse/legacy/lookup',
            'target': '{}lookup'.format(base)
        }
        self.API_getAddToLibraryRecommendations = {
            'path':   'muse/legacy/getAddToLibraryRecommendations',
            'target': '{}getAddToLibraryRecommendations'.format(base)
        }
        self.API_getSimilarityRecommendations = {
            'path':   'muse/legacy/getSimilarityRecommendations',
            'target': '{}getSimilarityRecommendations'.format(base)
        }
        self.API_getMusicStoreRecommendations = {
            'path':   'muse/legacy/getMusicStoreRecommendations',
            'target': '{}getMusicStoreRecommendations'.format(base)
        }
        self.API_artistDetailCatalog = {
            'path':   'muse/artistDetailCatalog',
            'target': '{}artistDetailCatalog'.format(base),
            'method': 'POST'
        }
        self.API_getStationSections = {
            'path':   'muse/stations/getStationSections',
            'target': '{}getStationSectionsGet'.format(base),
            'method': 'GET'
        }
        self.API_artistDetailsMetadata = {
            'path':   'muse/artistDetailsMetadata',
            'target': '{}artistDetailsMetadata'.format(base)
        }
        self.API_getTopMusicEntities = { # playlists
            'path':   'muse/getTopMusicEntities',
            'target': '{}getTopMusicEntities'.format(base)
        }
        self.API_browseHierarchyV2 = {
            'path':   'muse/browseHierarchyV2',
            'target': '{}browseHierarchyV2'.format(base)
        }
        self.API_seeMore = {
            'path':   'muse/seeMore',
            'target': '{}seeMore'.format(base)
        }
        # new
        self.API_getHome = {
            'path':   'muse/getHome',
            'target': '{}getHome'.format(base)
        }
        # new end
        self.API_lookupStationsByStationKeys = {
            'path':   'muse/stations/lookupStationsByStationKeys',
            'target': '{}lookupStationsByStationKeys'.format(base)
        }
        base = 'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.'
        self.API_createQueue = { # genres
            'path':   'mpqs/voiceenabled/createQueue',
            'target': '{}createQueue'.format(base)
        }
        self.API_QueueGetNextTracks = { # genres
            'path':   'mpqs/voiceenabled/getNextTracks',
            'target': '{}getNextTracks'.format(base)
        }
        # get streaming url
        base = 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.'
        self.API_stream  = { # ASIN / COID
            'path':   'dmls/',
            'target': '{}getRestrictedStreamingURL'.format(base)
        }
        self.API_streamHLS = { # ASIN (hlsVersion:V3)
            'path':   'dmls/',
            'target': '{}getHLSManifest'.format(base)
        }
        self.API_streamDash = { # ASIN (musicDashVersionList: ["V1", "V2"])
            'path':   'dmls/',
            'target': '{}getDashManifestsV2'.format(base)
        }
        self.API_LicenseForPlaybackV2 = {
            'path':   'dmls/',
            'target': '{}getLicenseForPlaybackV2'.format(base)
        }
        self.API_search = {
            'path':   'textsearch/search/v1_1/',
            'target': 'com.amazon.tenzing.textsearch.v1_1.TenzingTextSearchServiceExternalV1_1.search'
        }
        # cirrus
        base = 'com.amazon.cirrus.libraryservice.'
        self.API_cirrus   = {
            'path'  : 'cirrus/',
            'target': None
        }
        self.API_cirrusV1 = {
            'path':   'cirrus/',
            'target': '{}CirrusLibraryServiceExternal.'.format(base)
        }
        self.API_cirrusV2 = {
            'path':   'cirrus/2011-06-01/',
            'target': '{}v2.CirrusLibraryServiceExternalV2.'.format(base)
        }
        self.API_cirrusV3 = {
            'path':   'cirrus/v3/',
            'target': '{}v3.CirrusLibraryServiceExternalV3.'.format(base)
        }
        self.API_V3getTracksByAsin = {
            'path':   'cirrus/v3/',
            'target': '{}getTracksByAsin'.format(self.API_cirrusV3['target'])
        }
        self.API_V3getTracks = {
            'path':   'cirrus/v3/',
            'target': '{}getTracks'.format(self.API_cirrusV3['target']),
            'operation': 'getTracks'
        }
        self.API_V3getTracksById = {
            'path':   'cirrus/v3/',
            'target': '{}getTracksById'.format(self.API_cirrusV3['target']),
            'operation': 'getTracksById'
        }
        # default
        base = 'com.amazon.musicplaylist.model.MusicPlaylistService.'
        self.API_getPlaylistsByIdV2 = {
            'path':   'playlists/',
            'target': '{}getPlaylistsByIdV2'.format(base)
        }
        self.API_getPubliclyAvailablePlaylistsById = {
            'path':   'playlists/',
            'target': '{}getPubliclyAvailablePlaylistsById'.format(base)
        }
        self.API_sociallySharePlaylist = {
            'path':   'playlists/',
            'target': '{}sociallySharePlaylist'.format(base)
        }
        self.API_getConfigurationV2 = {
            'path':   'playlists/',
            'target': '{}getConfigurationV2'.format(base)
        }
        self.API_getFollowedPlaylistsInLibrary = {
            'path':   'playlists/',
            'target': '{}getFollowedPlaylistsInLibrary'.format(base)
        }
        self.API_getOwnedPlaylistsInLibrary = {
            'path':   'playlists/',
            'target': '{}getOwnedPlaylistsInLibrary'.format(base)
        }
        base = 'com.amazon.nimblymusicservice.NimblyMusicService.'
        self.API_GetRecentTrackActivity = {
            'path':   'nimbly/',
            'target': '{}GetRecentTrackActivity'.format(base)
        }
        self.API_GetRecentActivity = {
            'path':   'nimbly/',
            'target': '{}GetRecentActivity'.format(base)
        }
        # soccer live
        base = 'com.amazon.eventvendingservice.EventVendingService.getProgramDetails'
        self.API_GetSoccerMain = {
            'path':   'eve/getPrograms',
            'target': base
        }
        self.API_GetSoccerProgramDetails = {
            'path':   'eve/getProgramDetails',
            'target': base
        }
        self.API_GetSoccerLiveURLs = {
            'path':   'amals/getLiveStreamingUrls',
            'target': 'com.amazon.amazonmusicaudiolocatorservice.model.AmazonMusicAudioLocatorServiceExternal.GetLiveStreamingURLs'
        }
        self.API_GetSoccerOnDemandURLs = {
            'path':   'amals/getOnDemandStreamingURLs',
            'target': 'com.amazon.amazonmusicaudiolocatorservice.model.AmazonMusicAudioLocatorServiceExternal.GetOnDemandStreamingURLs'
        }
    def setQueryConstants(self):
        self.Q_getServerSongs = {
            'Operation'         : 'searchLibrary',
            'caller'            : 'getServerSongs',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : '' # 'sortTitle'
        }
        self.Q_getAllDataCountByMetaType = {
            'Operation'         : 'searchLibrary',
            'caller'            : 'getAllDataCountByMetaType',
            'searchReturnType'  : 'ALBUMS',
            'sortColumn'        : 'sortAlbumName'
        }
        self.Q_getAllDataByMetaType = {
            'Operation'         : 'searchLibrary',
            'caller'            : 'getAllDataByMetaType',
            'searchReturnType'  : 'ALBUMS',
            'sortColumn'        : 'sortAlbumName'
        }
        self.Q_getAlbumsCountForMetatype = {
            'Operation'         : 'searchLibrary',
            'caller'            : 'getAlbumsCountForMetatype',
            'searchReturnType'  : 'ALBUMS',
            'sortColumn'        : 'sortAlbumName'
        }
        self.Q_getAlbumsForMetatype = {
            'Operation'         : 'searchLibrary',
            'caller'            : 'getAlbumsForMetatype',
            'searchReturnType'  : 'ALBUMS',
            'sortColumn'        : 'sortAlbumName'
        }
        self.Q_getSongForPlayerBySearchLibrary = {
            'Operation'         : 'searchLibrary',
            'caller'            : 'getSongForPlayerBySearchLibrary',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : '' # 'sortTitle'
        }
        self.Q_getTracks = {
            'Operation'         : 'getTracks',
            'caller'            : 'dataServices.getTracks',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : 'sortTitle'
        }
        self.Q_getTracksByAlbum = {
            'Operation'         : 'selectTracks',
            'caller'            : 'dataServices.getTracksByAlbum',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : 'sortTitle'
        }
        """
        self.Q_getSongForDowloadBySelectTrackMetadata = {
            'Operation'         : 'selectTrackMetadata',
            'caller'            : 'getSongForDowload',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : '' # 'sortTitle'
        }
        self.Q_getSongForPlayerBySelectTrackMetadata = {
            'Operation'         : 'selectTrackMetadata',
            'caller'            : 'getSongForPlayerBySelectTrackMetadata',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : 'sortTitle'
        }
        self.Q_getSongForPlayerFromSmartList = {
            'Operation'         : 'selectTrackMetadata',
            'caller'            : 'getSongForPlayerFromSmartList',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : 'sortTitle'
        }
        self.Q_getServerSmartList = { # done
            'Operation'         : 'selectTrackMetadata',
            'caller'            : 'getServerSmartList',
            'searchReturnType'  : '',
            'sortColumn'        : 'creationDate'
        }
        """
        self.Q_getServerListSongs = {
            'Operation'         : 'getPlaylists',
            'caller'            : 'getServerListSongs',
            'searchReturnType'  : '', # 'ALBUMS',
            'sortColumn'        : ''  # 'sortAlbumName'
        }
        """
        self.Q_getServerAlbumData = { # done
            'Operation'         : 'selectTrackMetadata',
            'caller'            : 'getServerData',
            'searchReturnType'  : 'TRACKS',
            'sortColumn'        : 'trackNum'
        }
        self.Q_getServerData = { # done
            'Operation'         : 'selectTrackMetadata',
            'caller'            : 'getServerData',
            'searchReturnType'  : '',
            'sortColumn'        : 'sortAlbumName' # discNum + trackNum
        }
        """
    ################################################################################
    # amazon logon
    def amazonLogon(self):
        app_config = None
        self.delCookies()
        #xbmcaddon.Addon(id=self.addonId).openSettings()
        self.doReInit()
        self.addonMode = None
        self.access = False
        x = 1
        while not self.access:
            if not self.getCredentials():
                return False
            self.br.open(self.logonURL)
            #self.log(self.br.response().code)
            #self.log(self.br.response().info())
            #self.log(unicode(self.br.response().read(), "utf-8"))

            #self.doLogonForm()
            #self.content = self.getLogonResponse()
            try: 
                self.doLogonForm()
            except:
                self.checkCaptcha()
                continue
            self.content = self.getLogonResponse()
            
            if x == 3:
                return False
            # if 'message error' in self.content or x == 3:
            #     xbmcgui.Dialog().ok(self.addonName, 'Logon issue')
            #     return False
            
            if not self.checkMFA():
                return False

            self.setCookie()
            if not os.path.isfile(self.cookieFile):
                break

            self.cj.load(self.cookieFile)
            head = self.prepReqHeader('')
            resp = requests.post(self.musicURL, data=None, headers=head, cookies=self.cj)

            alt = False
            for line in resp.iter_lines(decode_unicode=True):
                if ('applicationContextConfiguration =' in line
                    or 'amznMusic.appConfig =' in line):
                    app_config = json.loads(re.sub(r'^[^{]*', '', re.sub(r';$', '', line)))
                    break
                elif 'appConfig:' in line:
                    soup = self.parseHTML(resp.text)
                    script = soup.find('script').getText().strip()
                    script = script.replace("window.amznMusic = ","")
                    script = script.replace("appConfig:","\"appConfig\":")
                    script = script.replace(" false","\"false\"")
                    script = script.replace(" true","\"true\"")
                    script = script.replace(" null","\"null\"")
                    script = script.replace(os.linesep,"")
                    script = script.replace(" ","")
                    script = script.replace("/","_")
                    script = script.replace("},};","}}")
                    app_config = json.loads(script)
                    alt = True
                    break

            if not alt:
                if app_config is None or app_config['isRecognizedCustomer'] == 0:
                    if app_config is not None and app_config['isTravelingCustomer']:
                        self.checkSiteVersion(app_config['stratusMusicTerritory'].lower())
                        self.doReInit()
                    self.delCookies()
                    app_config = None
                    self.access = False
                else:
                    self.appConfig(app_config)
                    self.setCookie()
                    self.doReInit()
                    self.delCredentials()
                    self.access = True
            else:
                self.appConfig2(app_config['appConfig'])
                self.setCookie()
                self.doReInit()
                self.delCredentials()
                self.access = True
            x+=1
        return True
    def doReInit(self):
        self.setVariables()
        self.prepFolder()
        self.prepBrowser()
    def doLogonForm(self):
        self.br.select_form(name="signIn")
        if not self.br.find_control("email").readonly:
            self.br["email"] = self.userEmail
        self.br["password"] = self.userPassword
    def getLogonResponse(self):
        self.br.submit()
        resp = self.br.response()
        try:
            return unicode(resp.read(), "utf-8") # for kodi 18
        except:
            return str(resp.read(), encoding = 'utf-8') # for kodi 19
    def checkMFA(self):
        while 'action="verify"' in self.content or 'id="auth-mfa-remember-device' in self.content:
            soup = self.parseHTML(self.content)
            if 'cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none' in self.content:
                self.log('MFA - account name')
                form = soup.find('form', class_="cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none")
                msgheading = form.find('label', class_="a-form-label").getText().strip()
                msgtxt = ""
                inp = self.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'dcq_question_subjective_1') == False:
                    return False
            elif 'name="claimspicker"' in self.content:
                self.log('MFA - SMS code step 1')
                form = soup.find_all('form', attrs={'name':'claimspicker'})
                msgheading = form[0].find('h1').renderContents().strip()
                msgtxt = form[0].findAll('div', class_='a-row')[1].renderContents().strip()
                if xbmcgui.Dialog().yesno(msgheading, msgtxt):
                    self.br.select_form(nr=0)
                    self.content = self.getLogonResponse()
                else:
                    return False
            elif 'name="code"' in self.content: # sms info
                self.log('MFA - SMS code step 2')
                form = soup.find_all('form', class_='cvf-widget-form fwcim-form a-spacing-none')
                msgheading = form[0].findAll(lambda tag: tag.name == 'span' and not tag.attrs)
                msgheading = msgheading[1].text + '\n' + msgheading[2].text
                msgtxt = ''
                inp = self.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'code') == False:
                    return False
            elif 'auth-mfa-form' in self.content:
                msg = soup.find('form', id='auth-mfa-form')
                self.log('### MFA ###############')
                msgheading = msg.p.renderContents().strip()
                msgtxt = ''
                inp = self.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'otpCode','ActivateWindow(busydialog)') == False:
                    return False
            else: # Unknown form
                # captcha call here
                return False
        return True
    def checkMFAInput(self, inp, target, action=None):
        if inp:
            if action:
                xbmc.executebuiltin(action)
            self.br.select_form(nr=0)
            self.br[target] = inp
            self.content = self.getLogonResponse()
        else:
            return False
    def checkCaptcha(self):
        self.log('########### captcha ###########')
        #self.br.select_form(name="")
        # self.br.select_form(action="/errors/validateCaptcha")
        self.br.select_form(nr=0)
        try:
            self.content = unicode(str(self.br.response().read()), "utf-8") # for kodi 18
        except:
            self.content = str(self.br.response().read(), encoding = 'utf-8') # for kodi 19
        # self.content = str(self.br.response().read(), encoding = 'utf-8')
        soup = self.parseHTML(self.content)
        # self.log(soup)
        form = soup.find_all('form')
        try:
            msgheading = unicode(str(form[0].find('h4').renderContents().strip()), "utf-8") # for kodi 18
        except:
            msgheading = str(form[0].find('h4').renderContents().strip(), encoding = 'utf-8') # for kodi 19
        # msgheading = str(form[0].find('h4').renderContents().strip(), encoding = 'utf-8')

        img = form[0].find('img') #.renderContents().strip()
        # self.log(msgheading)
        # self.log(img['src'])
        self.showCaptcha('captcha.xml',img['src'],msgheading)
        self.captcha = self.getSetting('captcha')
        if self.captcha == "":
            return False
        self.br["field-keywords"] = self.captcha
        self.setSetting('captcha',"")
    def showCaptcha(self,layout, imagefile, message):
        class Captcha(xbmcgui.WindowXMLDialog):
            def __init__(self, *args, **kwargs):
                self.image = kwargs["image"]
                self.text  = kwargs["text"]
                self.addon = kwargs["addon"]
                self.inp   = ""
            def onInit(self):
                self.title          = 501
                self.imagecontrol   = 502
                self.textbox        = 503
                self.inptxt         = 504
                self.btn_input      = 505
                self.btn_cancel     = 506
                self.btn_ok         = 507
                self.show_dialog()
            def show_dialog(self):
                self.getControl(self.title).setLabel('Captcha Entry')
                self.getControl(self.imagecontrol).setImage(self.image)
                self.getControl(self.textbox).setText(self.text)
                self.getControl(self.inptxt).setText('Your entry: ' + self.inp)
                self.setFocus(self.getControl(self.btn_ok))
            def getUserInput(self,title,txt=''):
                dialog = xbmcgui.Dialog()
                self.inp = dialog.input('Captcha Entry', defaultt=self.inp, type=xbmcgui.INPUT_ALPHANUM, option=0)
                del dialog
                self.addon.setSetting('captcha',self.inp)
                self.show_dialog()
            def onClick(self, controlid):
                if controlid == self.btn_ok:
                    self.close()
                elif controlid == self.btn_cancel:
                    self.addon.setSetting('captcha',"")
                    self.close()
                elif controlid == self.btn_input:
                    self.getUserInput('Captcha Entry')
        cp = Captcha(layout, self.addonFolder, 'Default', image=imagefile, text=message, addon=self.addon)
        cp.doModal()
        self.captcha = self.getSetting("captcha")
        del cp
    # default communication
    def amzCall(self,amzUrl,mode,referer=None,asin=None,mediatype=None):
        url = '{}/{}/api/{}'.format(self.url, self.region, amzUrl['path'])
        head = self.prepReqHeader(amzUrl['target'],referer)
        data = self.prepReqData(mode,asin,mediatype)
        resp = requests.post(url=url, data=data, headers=head, cookies=self.cj)
        self.setCookie()
        if resp.status_code == 401 :
            if self.amazonLogon():
                return self.amzCall(amzUrl,mode,referer,asin,mediatype)
        if self.logging:
            self.log(resp.text)
        if mode == 'getTrack' or mode == 'getTrackHLS' or mode == 'getTrackDash':
            return resp
        else:
            return resp.json()
    def prepBrowser(self):
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_gzip(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_equiv(True)
        self.br.set_cookiejar(self.cj)
        self.br.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
             ('Accept-Encoding', 'deflate,br'), #gzip,
             ('Accept-Language', '{},en-US;q=0.7,en;q=0.3'.format(self.siteVerList[int(self.siteVersion)])), #'de,en-US;q=0.7,en;q=0.3'),
             ('Cache-Control', 'no-cache'),
             ('Connection', 'keep-alive'),
             ('Content-Type', 'application/x-www-form-urlencoded'),
             ('User-Agent', self.userAgent),
             ('csrf-token', self.csrf_token),
             ('csrf-rnd',   self.csrf_rnd),
             ('csrf-ts',    self.csrf_ts),
             ('Upgrade-Insecure-Requests', '1')]
    def prepReqHeader(self, amzTarget, referer=None):
        head = { 'Accept' : 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding' : 'gzip,deflate,br',
                'Accept-Language' : '{},en-US,en;q=0.9'.format(self.siteVerList[int(self.siteVersion)]),
                'csrf-rnd' :        self.csrf_rnd,
                'csrf-token' :      self.csrf_token,
                'csrf-ts' :         self.csrf_ts,
                'Host' :            'music.amazon.{}'.format(self.siteVerList[int(self.siteVersion)]),
                'Origin' :          self.musicURL,
                'User-Agent' :      self.userAgent,
                'X-Requested-With' : 'XMLHttpRequest'
        }
        if amzTarget is not None:
            head['Content-Encoding'] = 'amz-1.0'
            head['content-type'] = 'application/json'
            head['X-Amz-Target'] = amzTarget
        if referer == 'soccer':
            head['Content-Encoding'] = None
        return head
    def prepReqData(self,mode,asin=None,mediatype=None):
        #data = json.dumps(data)
        #data = json.JSONEncoder().encode(data)
        """
        rankType:           newly-added, popularity-rank, top-sellers, newly-released
        requestedContent:   FULL_CATALOG, KATANA, MUSIC_SUBSCRIPTION, PRIME_UPSELL_MS, ALL_STREAMABLE, PRIME
        features:           fullAlbumDetails, playlistLibraryAvailability, childParentOwnership, trackLibraryAvailability,
                            hasLyrics, expandTracklist, ownership, popularity, albumArtist, collectionLibraryAvailability
        types:              artist, track, album, similarArtist, playlist, station
        """
        token = self.addonArgs.get('token', [''])
        if   mode == 'searchItems':
            if self.addonArgs.get('token', [None])[0] == None:
                prop = 'maxResults'
                val = self.maxResults
            else:
                prop = 'pageToken'
                val = self.addonArgs.get('token', [None])[0]
            #if self.accessType == 'UNLIMITED':
            #    tier = 'MUSIC_SUBSCRIPTION'
            #else:
            #    tier = self.accessType
            data = {
                'customerIdentity': {
                    'deviceId': self.deviceId,
                    'deviceType': self.deviceType,
                    'sessionId': '',
                    'customerId': self.customerId
                },
                'features': {
                    'spellCorrection': {
                        'allowCorrection': 'true'
                    }
                },
                'locale': self.locale,
                'musicTerritory': self.musicTerritory,
                'query': asin,
                'requestContext': 'true',
                'resultSpecs': [{
                    'label': mediatype[0], #'albums',
                    'documentSpecs': [{
                        'type': mediatype[1], #'catalog_album',
                        'fields': [
                            '__DEFAULT',
                            'artOriginal',
                            'artMedium',
                            'artLarge',
                            'artFull',
                            'isMusicSubscription',
                            'primeStatus',
                            'albumName',
                            'albumReleaseDate'
                        ]
                    }],
                    prop : val,
                    'contentRestrictions': {
                        'allowedParentalControls': {
                            'hasExplicitLanguage': 'true'
                        },
                        'eligibility': {
                            'tier': self.accessType # correction for unlimited accounts necessary?
                        }
                    }
                }]
            }
            data = json.JSONEncoder().encode(data)
        elif mode == 'getArtistDetails':
            if self.accessType == 'UNLIMITED':
                tier = 'MUSIC_SUBSCRIPTION'
            else:
                tier = self.accessType
            data  = {
                'requestedContent': tier,
                'asin': asin,
                'types':[{
                    'sortBy':'popularity-rank',
                    'type':'album',
                    'maxCount':     self.maxResults,
                    'nextToken':    self.addonArgs.get('token', [''])[0]
                }],
                'features':[
                    #'expandTracklist',
                    #'collectionLibraryAvailability',
                    'popularity'
                ],
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId
            }
            data = json.dumps(data)
        elif mode == 'recentlyplayed':
            data = {
                'activityTypeFilters': [mediatype],
                'pageToken':        token[0],
                'lang':             self.locale,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId,
            }
            data = json.dumps(data)
        elif mode == 'getMetaTracks':
            """
            available fields in attributeList:
            ['uploaded', 'composer', 'primaryGenre', 'albumArtistName', 'albumCoverImageFull', 'sortAlbumArtistName', 'purchased', 'fileExtension', 'albumReleaseDate',
            'albumAsin', 'fileName', 'albumCoverImageXL', 'albumContributors', 'songWriter', 'albumCoverImageMedium', 'albumCoverImageLarge', 'orderId', 'assetType',
            'parentalControls', 'marketplace', 'lyricist', 'localFilePath', 'albumRating', 'creationDate', 'bitrate', 'albumArtistAsin', 'performer', 'purchaseDate',
            'sortArtistName', 'albumPrimaryGenre', 'primeStatus', 'discNum', 'status', 'rogueBackfillDate', 'physicalOrderId', 'artistName', 'lastUpdatedDate', 'albumCoverImageTiny',
            'duration', 'audioUpgradeDate', 'albumCoverImageSmall', 'errorCode', 'asin', 'title', 'isMusicSubscription', 'contributors', 'sortTitle', 'objectId', 'albumName',
            'trackNum', 'sortAlbumName', 'publisher', 'fileSize', 'rating', 'md5', 'artistAsin']
            """
            data = {
                'filterList':[
                    {
                        'attributeName':'albumAsin',
                        'comparisonType':'EQUALS',
                        'attributeValue':asin
                    },
                    {
                        'attributeName':'status',
                        'comparisonType':'EQUALS',
                        'attributeValue':'AVAILABLE'
                    }
                ],
                'attributeList':[
                    'trackNum',
                    'discNum',
                    'duration',
                    'albumReleaseDate',
                    'primaryGenre',
                    'albumName',
                    'artistName',
                    'title',
                    'asin',
                    'objectId',

                    'albumAsin',
                    'artistAsin',
                    'purchased',
                    'status',
                    'primeStatus'
                ],
                'sortOrder':{
                    'sort':'albumName',
                    'order':'ASC'
                },
                'maxResults':       self.maxResults,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType
            }
            data = json.JSONEncoder().encode(data)
        elif mode == 'recentlyaddedsongs':
            data = {
                'selectCriteria': None,
                'albumArtUrlsRedirects': 'false',
                'distinctOnly': 'false',
                'countOnly': 'false',
                'sortCriteriaList': None,
                'maxResults': self.maxResults,
                'nextResultsToken': self.addonArgs.get('token', [0])[0],
                'selectCriteriaList.member.1.attributeName': 'status',
                'selectCriteriaList.member.1.comparisonType': 'EQUALS',
                'selectCriteriaList.member.1.attributeValue': 'AVAILABLE',
                'selectCriteriaList.member.2.attributeName': 'creationDate',
                'selectCriteriaList.member.2.comparisonType': 'GREATER_THAN',
                'selectCriteriaList.member.2.attributeValue': datetime.date.today()-datetime.timedelta(days=90),
                'sortCriteriaList.member.1.sortColumn': 'creationDate',
                'sortCriteriaList.member.1.sortType': 'DESC',
                'Operation': 'selectTrackMetadata',
                'caller': 'getServerSmartList',
                'ContentType': 'JSON',
                'customerInfo.customerId':  self.customerId,
                'customerInfo.deviceId':    self.deviceId,
                'customerInfo.deviceType':  self.deviceType
            }
        elif mode == 'followedplaylists':
            data = {
                'optIntoSharedPlaylists': 'true',
                'entryOffset':      0, # todo
                'pageSize':         self.maxResults,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId
            }
            data = json.dumps(data)
        elif mode == 'getownedplaylists':
            data = {
                'entryOffset':      0, #todo
                'pageSize':         self.maxResults,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId
            }
            data = json.dumps(data)
        elif mode == 'getplaylistsbyid':
            data = {
                'playlistIds':      [asin],
                'requestedMetadata':['asin','albumName','sortAlbumName','artistName','primeStatus','isMusicSubscription','duration','sortArtistName','sortAlbumArtistName','objectId','title','status','assetType','discNum','trackNum','instantImport','purchased'],
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId
            }
            data = json.dumps(data)
        elif mode == 'playlist':
            data  = {
                'rankType':         mediatype,
                'requestedContent': 'PRIME',#self.accessType,
                'features':         ['playlistLibraryAvailability','collectionLibraryAvailability'],
                'types':            ['playlist'],
                'nextTokenMap':     {'playlist' : token[0]},
                'maxCount':         self.maxResults,
                'lang':             self.locale,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId
            }
            data = json.dumps(data)
        elif mode == 'recommendations':
            # mediatypes:
            # mp3-prime-browse-carousels_playlistStrategy
            # mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy
            # mp3-prime-browse-carousels_mp3PrimeTracksStrategy
            # mp3-prime-browse-carousels_mp3ArtistStationStrategy
            token = self.addonArgs.get('token', [0])
            data  = {
                'maxResultsPerWidget' : self.maxResults,
                'minResultsPerWidget' : 1,
                'lang' :                self.locale,
                'requestedContent' :    'PRIME', #self.accessType,
                'musicTerritory' :      self.musicTerritory,
                'deviceId' :            self.deviceId,
                'deviceType' :          self.deviceType,
                'customerId' :          self.customerId,
                'widgetIdTokenMap' : { mediatype : int(token[0]) }
            }
            data = json.dumps(data)
        elif mode == 'new_recommendations':
            data = {
                'deviceId' :            self.deviceId,
                'deviceType' :          self.deviceType,
                'customerId' :          self.customerId,
                'musicTerritory' :      self.musicTerritory,
                'lang' :                self.customerLang,
                'requestedContent' :    'PRIME_UPSELL_MS',#,
                'options' :             ['populateRecentlyPlayed']
                #'options' :             'requestBundesligaContent'
            }
            data = json.dumps(data)
            #data = json.JSONEncoder().encode(data)
        elif mode == 'getPurchased': # purchased and all Songs / purchased Albums
            data = {
                'searchReturnType': mediatype[0],
                'searchCriteria.member.1.attributeName': 'assetType',
                'searchCriteria.member.1.comparisonType': 'EQUALS',
                'searchCriteria.member.1.attributeValue': 'AUDIO',
                'searchCriteria.member.2.attributeName':  'status',
                'searchCriteria.member.2.comparisonType': 'EQUALS',
                'searchCriteria.member.2.attributeValue': 'AVAILABLE',
                #'searchCriteria.member.3.attributeName':  filter[0],
                #'searchCriteria.member.3.comparisonType': filter[1],
                #'searchCriteria.member.3.attributeValue': filter[2],
                'albumArtUrlsRedirects': 'false',
                'distinctOnly': 'false',
                'countOnly': 'false',
                'selectedColumns.member.1': 'trackNum',
                'selectedColumns.member.2': 'discNum',
                'selectedColumns.member.3': 'duration',
                'selectedColumns.member.4': 'albumReleaseDate',
                'selectedColumns.member.5': 'primaryGenre',
                'selectedColumns.member.6': 'albumName',
                'selectedColumns.member.7': 'artistName',
                'selectedColumns.member.8': 'title',
                'selectedColumns.member.9': 'asin',
                'selectedColumns.member.10': 'objectId',
                'selectedColumns.member.11': 'albumCoverImageFull',
                'selectedColumns.member.12': 'purchased',
                'selectedColumns.member.13': 'status',
                'selectedColumns.member.14': 'primeStatus',
                'selectedColumns.member.15': 'sortAlbumName',
                'selectedColumns.member.16': 'sortTitle',
                'sortCriteriaList': None,
                'maxResults': self.maxResults,
                'nextResultsToken': token[0],
                'Operation': 'searchLibrary',
                'caller': mediatype[1],
                'sortCriteriaList.member.1.sortColumn': mediatype[2],
                'sortCriteriaList.member.1.sortType': 'ASC',
                'ContentType': 'JSON',
                'customerInfo.customerId': self.customerId,
                'customerInfo.deviceId': self.deviceId,
                'customerInfo.deviceType': self.deviceType
            }
            if self.addonMode[0] == 'getPurSongs' or self.addonMode[0] == 'getPurAlbums':
                data['searchCriteria.member.3.attributeName']  = 'purchased'
                data['searchCriteria.member.3.comparisonType'] = 'EQUALS'
                data['searchCriteria.member.3.attributeValue'] = 'true'
            #else:
                #filter = ['primeStatus','NOT_EQUALS','NOT_PRIME']
        elif mode == 'songs':
            data  = {
                'asins' : [ asin ],
                'features' : [ 'collectionLibraryAvailability','expandTracklist','playlistLibraryAvailability','trackLibraryAvailability','hasLyrics'],
                'requestedContent' : 'MUSIC_SUBSCRIPTION',
                'deviceId' : self.deviceId,
                'deviceType' : self.deviceType,
                'musicTerritory' : self.musicTerritory,
                'customerId' : self.customerId
            }
            data = json.dumps(data)
        elif mode == 'itemLookup':
            data = {
                'asins': asin, # [asin], is an array!!
                'features': mediatype, # is an array!!
                'requestedContent': 'MUSIC_SUBSCRIPTION',
                'deviceId': self.deviceId,
                'deviceType': self.deviceType,
                'musicTerritory': self.musicTerritory,
                'customerId': self.customerId
            }
            data = json.JSONEncoder().encode(data)
        elif mode == 'itemLookup2ndRound':
            data = {
                'selectCriteriaList.member.1.attributeName':'status',
                'selectCriteriaList.member.1.comparisonType':'EQUALS',
                'selectCriteriaList.member.1.attributeValue':'AVAILABLE',
                'selectCriteriaList.member.2.attributeName':'trackStatus',
                'selectCriteriaList.member.2.comparisonType':'IS_NULL',
                'selectCriteriaList.member.2.attributeValue':'',
                'selectCriteriaList.member.3.attributeName':'albumAsin',
                'selectCriteriaList.member.3.comparisonType':'EQUALS',
                'selectCriteriaList.member.3.attributeValue':asin,
                'sortCriteriaList':'',
                'albumArtUrlsSizeList.member.1':'FULL',
                'albumArtUrlsSizeList.member.2':'LARGE',
                'albumArtUrlsRedirects':'false',
                'maxResults':   self.maxResults,
                'nextResultsToken':0,
                'Operation':'selectTrackMetadata',
                'distinctOnly':'false',
                'countOnly':'false',
                'caller':'getServerData',
                'selectedColumns.member.1':'albumArtistName',
                'selectedColumns.member.2':'albumAsin',
                'selectedColumns.member.3':'albumName',
                'selectedColumns.member.4':'albumReleaseDate',
                'selectedColumns.member.5':'artistAsin',
                'selectedColumns.member.6':'artistName',
                'selectedColumns.member.7':'asin',
                'selectedColumns.member.8':'assetType',
                'selectedColumns.member.9':'creationDate',
                'selectedColumns.member.10':'discNum',
                'selectedColumns.member.11':'duration',
                'selectedColumns.member.12':'extension',
                'selectedColumns.member.13':'purchased',
                'selectedColumns.member.14':'lastUpdatedDate',
                'selectedColumns.member.15':'name',
                'selectedColumns.member.16':'objectId',
                'selectedColumns.member.17':'orderId',
                'selectedColumns.member.18':'primaryGenre',
                'selectedColumns.member.19':'purchaseDate',
                'selectedColumns.member.20':'size',
                'selectedColumns.member.21':'sortAlbumArtistName',
                'selectedColumns.member.22':'sortAlbumName',
                'selectedColumns.member.23':'sortArtistName',
                'selectedColumns.member.24':'sortTitle',
                'selectedColumns.member.25':'status',
                'selectedColumns.member.26':'title',
                'selectedColumns.member.27':'trackNum',
                'selectedColumns.member.28':'trackStatus',
                'selectedColumns.member.29':'payerId',
                'selectedColumns.member.30':'physicalOrderId',
                'selectedColumns.member.31':'primeStatus',
                'selectedColumns.member.32':'purchased',
                'selectedColumns.member.33':'uploaded',
                'selectedColumns.member.34':'instantImport',
                'selectedColumns.member.35':'parentalControls',
                'selectedColumns.member.36':'albumCoverImageFull',
                'selectedColumns.member.37':'albumCoverImageLarge',
                'selectedColumns.member.38':'albumCoverImageMedium',
                'selectedColumns.member.39':'albumCoverImageSmall',
                'selectedColumns.member.40':'isMusicSubscription',
                'sortCriteriaList.member.1.sortColumn':'discNum',
                'sortCriteriaList.member.1.sortType':'ASC',
                'sortCriteriaList.member.2.sortColumn':'trackNum',
                'sortCriteriaList.member.2.sortType':'ASC',
                'ContentType':'JSON',
                'customerInfo.customerId':  self.customerId,
                'customerInfo.deviceId':    self.deviceId,
                'customerInfo.deviceType':  self.deviceType
            }
        elif mode == 'getStations':
            data = {
                'requestedContent': 'PRIME', #self.accessType,
                'lang':             self.locale,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId
            }
            data = json.dumps(data)
        elif mode == 'createQueue':
            data = {
                'identifier': asin,
                'identifierType':'STATION_KEY',
                'customerInfo': {
                    'deviceId':     self.deviceId,
                    'deviceType':   self.deviceType,
                    'musicTerritory':self.musicTerritory,
                    'customerId':   self.customerId
                },
                'allowedParentalControls':{}
            }
            data = json.dumps(data)
        elif mode == 'getNextTracks':
            data = {
                'pageToken' : mediatype,
                'numberOfTracks':10,
                'customerInfo': {
                    'deviceId':     self.deviceId,
                    'deviceType':   self.deviceType,
                    'musicTerritory':self.musicTerritory,
                    'customerId':   self.customerId
                },
                'allowedParentalControls':{}
            }
            data = json.dumps(data)
        elif mode == 'getGenrePlaylist':
            data = {
                'identifier': asin,
                'identifierType': 'STATION_KEY',
                'customerInfo': {
                    'deviceId':     self.deviceId,
                    'deviceType':   self.deviceType,
                    'musicTerritory':self.musicTerritory,
                    'customerId':   self.customerId
                },
                'allowedParentalControls': {}
            }
        elif mode == 'getMetaData':
            data = {
                'trackIdList': asin,
                'attributeList': [
                    'albumCoverImageFull',
                    'albumCoverImageLarge',
                    'albumCoverImageMedium',
                    'albumCoverImageSmall',
                    'albumName',
                    'albumAsin',
                    'sortAlbumName',
                    'artistName',
                    'artistAsin',
                    'sortArtistName',
                    'sortAlbumArtistName',
                    'objectId',
                    'asin',
                    'title',
                    'status',
                    'primeStatus',
                    'isMusicSubscription',
                    'assetType',
                    'duration',
                    'discNum',
                    'trackNum',
                    'instantImport',
                    'purchased',
                    'uploaded',
                    'albumReleaseDate'
                ],
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId,
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType
            }
            data = json.dumps(data)
        elif mode == 'getTrack':
            data = {
                'customerId' : self.customerId,
                'deviceToken' : {
                    'deviceTypeId': self.deviceType,
                    'deviceId' :    self.deviceId
                },
                'bitRate' : self.audioQuality,
                'appMetadata' : { 'https' : 'true' },
                'clientMetadata' : { 'clientId' : 'WebCP' },
                'contentId' : {
                    'identifier' : asin,
                    'identifierType' : mediatype #, # 'ASIN',
                    #'bitRate' : self.audioQuality
                }
            }
            data = json.dumps(data)
        elif mode == 'getTrackHLS':
            data = {
                'customerId' : self.customerId,
                'deviceToken' : {
                    'deviceTypeId': self.deviceType,
                    'deviceId' :    self.deviceId
                },
                'bitRate' : self.audioQuality,
                'appMetadata' : { 'https' : 'true' },
                'clientMetadata' : { 'clientId' : 'WebCP' },
                'contentId' : {
                    'identifier' : asin,
                    'identifierType' : mediatype #, # 'ASIN',
                },
                'bitRateList' : [ self.audioQuality ],
                'hlsVersion': 'V3'
            }
            data = json.dumps(data)
        elif mode == 'getTrackDash':
            mID = self.getMaestroID()
            data = {
                'customerId' :          self.customerId,
                'deviceToken' : {
                    'deviceTypeId' :    self.deviceType,
                    'deviceId' :        self.deviceId
                },
                'contentIdList' : [{
                    'identifier' :      asin,
                    'identifierType' :  mediatype
                }],
                'bitrateTypeList' : [ self.audioQuality ],
                'musicDashVersionList' : [ 'V2' ],
                'appInfo' : {
                    'musicAgent': mID # 'Maestro/1.0 WebCP/1.0.202513.0 (9a46-5ad0-dmcp-8d19-ee5c6)'
                },
                'customerInfo' : {
                    'marketplaceId' :   self.marketplaceId,
                    'customerId' :      self.customerId,
                    'territoryId' :     self.musicTerritory,
                    'entitlementList' : [ 'HAWKFIRE' ]
                }
            }
            data = json.dumps(data)
        elif mode == 'getLicenseForPlaybackV2':
            mID = self.getMaestroID()
            # 'b{SSM}' base64NonURLencoded
            # 'B{SSM}' Base64URLencoded
            # 'R{SSM}' Raw format.
            data = {
                'DrmType':'WIDEVINE',
                #'licenseChallenge':'b{SSM}',
                'customerId':self.customerId,
                'deviceToken':{
                    'deviceTypeId':self.deviceType,
                    'deviceId':self.deviceId
                },
                'appInfo':{
                    'musicAgent':mID
                }
            }
            if mediatype:
                data['licenseChallenge'] = mediatype
            else:
                data['licenseChallenge'] = 'b{SSM}'
            data = json.dumps(data)
        elif mode == 'getSoccerMain':
            data = { # TODO
                'competitionId':    mediatype,
                'localTimeOffset': '+02:00',
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId,
                'lang':             self.locale
            }
            data = json.dumps(data)
        elif mode == 'getSoccerProgramDetails':
            data = { # TODO
                'programId':        mediatype,
                'localTimeOffset': '+02:00',
                'deviceId':         self.deviceId,
                'deviceType':       self.deviceType,
                'musicTerritory':   self.musicTerritory,
                'customerId':       self.customerId,
                'lang':             self.locale
            }
            data = json.dumps(data)
        elif mode == 'getSoccerLiveURL':
            data = {
                'Operation':'com.amazon.amazonmusicaudiolocatorservice.model.getlivestreamingurls#GetLiveStreamingURLs',
                'Service':'com.amazon.amazonmusicaudiolocatorservice.model#AmazonMusicAudioLocatorServiceExternal',
                'Input':{
                    'customerId':self.customerId,
                    'deviceToken':{
                        'deviceTypeId':self.deviceType,
                        'deviceId':self.deviceId
                    },
                    'appMetadata':{'appId':'WebCP'},
                    'clientMetadata':{
                        'clientId':self.deviceType,
                        'clientIpAddress':''},
                    'contentIdList':[{
                        'identifier':mediatype,
                        'identifierType':'MCID'}],
                    'protocol':'DASH'
                }
            }
            data = json.dumps(data)
        elif mode == 'getSoccerOnDemandURL':
            data = {
                'Operation':'com.amazon.amazonmusicaudiolocatorservice.model.getondemandstreamingurls#GetOnDemandStreamingURLs',
                'Service':'com.amazon.amazonmusicaudiolocatorservice.model#AmazonMusicAudioLocatorServiceExternal',
                'Input':{
                    'customerId':self.customerId,
                    'deviceToken':{
                        'deviceTypeId':self.deviceType,
                        'deviceId':self.deviceId
                    },
                    'appMetadata':{'appId':'WebCP'},
                    'clientMetadata':{
                        'clientId':self.deviceType,
                        'clientIpAddress':''},
                    'contentIdList':[{
                        'identifier':mediatype,
                        'identifierType':'MCID'}],
                    'protocol':'DASH'
                }
            }
            data = json.dumps(data)
        return data
    # music content
    def menuHome(self):
        self.createList([   {'txt':30023,'fct':'menuPlaylists',         'img':self.getSetting("img_playlists")},
                            {'txt':30024,'fct':'menuAlbums',            'img':self.getSetting("img_albums")},
                            {'txt':30022,'fct':'menuSongs',             'img':self.getSetting("img_songs")},
                            {'txt':30008,'fct':'menuStations',          'img':self.getSetting("img_stations")},
                            {'txt':30015,'fct':'getGenres',             'img':self.getSetting("img_genres")},
                            {'txt':30027,'fct':'menuArtists',           'img':self.getSetting("img_artists")},
                            {'txt':30041,'fct':'getNewRecom',           'img':self.getSetting("img_newrecom")},
                            {'txt':30035,'fct':'menuSoccer',            'img':self.getSetting("img_soccer")}
        ])
    def menuPlaylists(self):
        self.createList([   {'txt':30013,'fct':'searchPlayLists',       'img':self.getSetting("img_search")},
                            {'txt':30032,'fct':'search1PlayLists',      'img':self.getSetting("img_search"),'search':self.getSetting(self.sPlayLists[0])},
                            {'txt':30033,'fct':'search2PlayLists',      'img':self.getSetting("img_search"),'search':self.getSetting(self.sPlayLists[1])},
                            {'txt':30034,'fct':'search3PlayLists',      'img':self.getSetting("img_search"),'search':self.getSetting(self.sPlayLists[2])},
                            {'txt':30003,'fct':'getRecomPlayLists',     'img':self.getSetting("img_playlists")},
                            {'txt':30002,'fct':'getNewPlayLists',       'img':self.getSetting("img_playlists")},
                            {'txt':30001,'fct':'getPopularPlayLists',   'img':self.getSetting("img_playlists")},
                            {'txt':30018,'fct':'getFollowedPlayLists',  'img':self.getSetting("img_playlists")},
                            {'txt':30019,'fct':'getOwnedPlaylists',     'img':self.getSetting("img_playlists")}
        ],True)
    def menuAlbums(self):
        self.createList([   {'txt':30010,'fct':'searchAlbums',          'img':self.getSetting("img_search")},
                            {'txt':30032,'fct':'search1Albums',         'img':self.getSetting("img_search"),'search':self.getSetting(self.sAlbums[0])},
                            {'txt':30033,'fct':'search2Albums',         'img':self.getSetting("img_search"),'search':self.getSetting(self.sAlbums[1])},
                            {'txt':30034,'fct':'search3Albums',         'img':self.getSetting("img_search"),'search':self.getSetting(self.sAlbums[2])},
                            {'txt':30004,'fct':'getRecomAlbums',        'img':self.getSetting("img_albums")},
                            {'txt':30012,'fct':'getPurAlbums',          'img':self.getSetting("img_albums")},
                            {'txt':30007,'fct':'getAllAlbums',          'img':self.getSetting("img_albums")}
        ],True)
    def menuSongs(self):
        self.createList([   {'txt':30011,'fct':'searchSongs',           'img':self.getSetting("img_search")},
                            {'txt':30032,'fct':'search1Songs',          'img':self.getSetting("img_search"),'search':self.getSetting(self.sSongs[0])},
                            {'txt':30033,'fct':'search2Songs',          'img':self.getSetting("img_search"),'search':self.getSetting(self.sSongs[1])},
                            {'txt':30034,'fct':'search3Songs',          'img':self.getSetting("img_search"),'search':self.getSetting(self.sSongs[2])},
                            {'txt':30009,'fct':'getPurSongs',           'img':self.getSetting("img_songs")},
                            {'txt':30006,'fct':'getAllSongs',           'img':self.getSetting("img_songs")},
                            {'txt':30017,'fct':'getRecentlyPlayed',     'img':self.getSetting("img_songs")},
                            {'txt':30021,'fct':'getRecentlyAddedSongs', 'img':self.getSetting("img_songs")}
        ],True)
    def menuStations(self):
        self.createList([   {'txt':30016,'fct':'searchStations',        'img':self.getSetting("img_search")},
                            {'txt':30032,'fct':'search1Stations',       'img':self.getSetting("img_search"),'search':self.getSetting(self.sStations[0])},
                            {'txt':30033,'fct':'search2Stations',       'img':self.getSetting("img_search"),'search':self.getSetting(self.sStations[1])},
                            {'txt':30034,'fct':'search3Stations',       'img':self.getSetting("img_search"),'search':self.getSetting(self.sStations[2])},
                            {'txt':30005,'fct':'getRecomStations',      'img':self.getSetting("img_stations")},
                            {'txt':30026,'fct':'getStations',           'img':self.getSetting("img_stations")},
                            {'txt':30025,'fct':'getAllArtistsStations', 'img':self.getSetting("img_stations")}
        ],True)
    def menuArtists(self):
        self.createList([   {'txt':30014,'fct':'searchArtist',          'img':self.getSetting("img_search")},
                            {'txt':30032,'fct':'search1Artists',        'img':self.getSetting("img_search"),'search':self.getSetting(self.sArtists[0])},
                            {'txt':30033,'fct':'search2Artists',        'img':self.getSetting("img_search"),'search':self.getSetting(self.sArtists[1])},
                            {'txt':30034,'fct':'search3Artists',        'img':self.getSetting("img_search"),'search':self.getSetting(self.sArtists[2])}
        ],True)
    def menuSoccer(self):
        self.createList([   {'txt':30036,'fct':'soccerBUND',            'img':self.getSetting("img_sBUND")},
                            {'txt':30037,'fct':'soccerBUND2',           'img':self.getSetting("img_sBUND2")},
                            {'txt':30038,'fct':'soccerDFBPOKAL',        'img':self.getSetting("img_sDFBPOKAL")},
                            {'txt':30039,'fct':'soccerCHAMP',           'img':self.getSetting("img_sCHAMP")},
                            {'txt':30040,'fct':'soccerSUPR',            'img':self.getSetting("img_sSUPR")}
        ])
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
    def createList(self,data,dynentry=False,soccer=False):
        itemlist = []
        url = None
        for item in data:
            # self.AMs.log(item)
            isFolder = True
            if dynentry and 'search' in item and self.AMs.getSetting(item['search']) == '':
                continue
            # if soccer:
            if soccer or ('special' in item and item['special'] == 'newrecom'):
                title = item['txt']
            else:
                title = self.AMs.translation(item['txt'])
            if dynentry and 'search' in item:
                title += self.AMs.getSetting(item['search']).encode("UTF-8")
            li = xbmcgui.ListItem(label=title)
            li.setInfo(type="music", infoLabels={"title": title})
            if 'img' in item:
                if 'http' in item['img']:
                    url = item['img']
                else:
                    url = '{}/resources/images/{}'.format(self.AMs.addonFolder, self.AMs.getSetting(item['img']) )
                li.setArt({'icon':url,'thumb':url,'fanart':url,'poster':url,'banner':url,'landscape':url})
            url = '{}?mode={}'.format(self.AMs.addonBaseUrl,str(item['fct']))
            if soccer:
                url+="&objectId={}".format(str(item['target']))
                if item['playable']:
                    pl = 'true'
                else:
                    pl = 'false'
                li.setProperty('IsPlayable', pl)
                isFolder = False
            if 'special' in item and item['special'] == 'newrecom' and 'target' in item:
                url+='&target={}'.format(str(item['target']))
            itemlist.append((url, li, isFolder))
        self.finalizeContent(itemlist,'albums')
    # get music information
    def lookup(self,asin):
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        data = self.AMc.amzCall( self.AMapi.lookup,'itemLookup',None,asin,mediatype)
        sel = ''
        if   len(data['albumList']) > 0:
            sel = 'albumList'
        elif len(data['artistList']) > 0:
            sel = 'artistList'
        elif len(data['playlistList']) > 0:
            sel = 'playlistList'
        elif len(data['trackList']) > 0:
            sel = 'trackList'
        else:
            data = self.AMc.amzCall(self.AMapi.cirrus, 'itemLookup2ndRound', '/my/albums', [asin], None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
            sel = 'trackInfoList'
        self.setAddonContent(sel,data[sel],'songs')
    def getRecentlyPlayed(self,mediatype):
        items = self.AMc.amzCall(self.AMapi.GetRecentTrackActivity,'recentlyplayed',None,None,mediatype)['recentActivityMap']['PLAYED']
        self.setAddonContent('recentlyplayed',items,'songs')
    def getRecentlyAddedSongs(self):
        items = self.AMc.amzCall(self.AMapi.cirrus,'recentlyaddedsongs',None,None,None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
        self.setAddonContent('recentlyaddedsongs',items,'songs')
    def getPlayLists(self,mediatype):
        items = self.AMc.amzCall(self.AMapi.getTopMusicEntities,'playlist',None,None,mediatype)
        # data structure is similar to lookup
        self.setAddonContent('playlists',items,'albums')
    def getFollowedPlayLists(self):
        items = self.AMc.amzCall(self.AMapi.getFollowedPlaylistsInLibrary,'followedplaylists',None,None,None)
        self.setAddonContent('followedplaylists',items,'albums')
    def getOwnedPlaylists(self):
        items = self.AMc.amzCall(self.AMapi.getOwnedPlaylistsInLibrary,'getownedplaylists',None,None,None)
        self.setAddonContent('ownedplaylists',items,'albums')
    def getPlaylistsByIdV2(self,asin):
        items = self.AMc.amzCall(self.AMapi.getPlaylistsByIdV2,'getplaylistsbyid',None,asin,None)
        self.setAddonContent('getplaylistsbyid',items,'songs')
    def getStations(self,mediatype):
        items = self.AMc.amzCall(self.AMapi.getStationSections,'getStations','/stations')
        self.setAddonContent(mediatype,items,'albums')
    def getGenrePlaylist(self,asin):
        items = self.AMc.amzCall(self.AMapi.createQueue,'getGenrePlaylist',None,asin)
        self.setAddonContent('genreplaylist',items,'albums')
    def getRecommendations(self,mode,mediatype):
        resp = self.AMc.amzCall(self.AMapi.getBrowseRecommendations,'recommendations',None,None,mediatype)
        sel = ''
        if   resp['recommendations'][0]['recommendationType'] == 'PLAYLIST':
            sel = 'recplaylists'
        elif resp['recommendations'][0]['recommendationType'] == 'ALBUM':
            sel = 'recalbums'
        elif resp['recommendations'][0]['recommendationType'] == 'STATION':
            sel = 'recstations'
        self.setAddonContent(sel,resp['recommendations'][0],'albums')
    def getNewRecommendations(self):
        menuEntries = []
        resp = self.AMc.amzCall(self.AMapi.getHome,'new_recommendations')
        for item in resp['blocks']:
            if (('ButtonGrid' in item['__type']) or ('Barker' in item['__type'])):
                continue
            menuEntries.append({
                'txt':      item['title'],
                'fct':      'getNewRecomDetails',
                'special':  'newrecom',
                'target':   urlquote(item['title'].encode('utf8')),
                'img':      'newrecom.jpg'
            })
        self.createList(menuEntries)
    def getNewRecomDetails(self,target):
        menuEntries = []
        items = None
        resp = self.AMc.amzCall(self.AMapi.getHome,'new_recommendations')
        for item in resp['blocks']:
            if (('ButtonGrid' in item['__type']) or ('Barker' in item['__type'])): # ignore button fields
                continue
            if target in item['title']: # find the category
                items = item['blocks']
                break
        if items == None: # in case of empty list
            return
        self.setAddonContent('newrecom',items,'albums')
    def getPurchased(self,mode,ctype):
        resp = self.AMc.amzCall(self.AMapi.cirrus,'getPurchased',None,None,mode)
        items = resp['searchLibraryResponse']['searchLibraryResult']
        if ctype == 'songs':
            mode = 'purchasedsongs'
        elif ctype == 'albums':
            mode = 'purchasedalbums'
        self.setAddonContent(mode,items,ctype)
    def searchItems(self,mode=None,txt=None,query=None):
        if query == None:
            if self.AMs.addonArgs.get('token', False):
                query = self.AMs.addonArgs.get('query', [''])[0]
            else:
                query = self.AMl.getUserInput(self.AMs.translation(txt), '')
                if not query:
                    return
        resp = self.AMc.amzCall( self.AMapi.search , 'searchItems' , '/search' , query,mode )
        items = resp['results'][0]
        if   mode[0] == 'albums':
            if not txt == None:
                self.AMs.setSearch('albums',query)
            self.setAddonContent('searchitems',items,'albums','albums',query)
        elif mode[0] == 'tracks':
            if not txt == None:
                self.AMs.setSearch('tracks',query)
            self.setAddonContent('searchitems',items,'songs','tracks',query)
        elif mode[0] == 'playlists':
            if not txt == None:
                self.AMs.setSearch('playlists',query)
            self.setAddonContent('searchplaylists',items,'albums',None,query)
        elif mode[0] == 'artists':
            if not txt == None:
                self.AMs.setSearch('artists',query)
            self.setAddonContent('searchartists',items,'songs',None,query)
        elif mode[0] == 'stations':
            if not txt == None:
                self.AMs.setSearch('stations',query)
            self.setAddonContent('searchstations',items,'albums',None,query)
    def getArtistDetails(self,asin):
        resp = self.AMc.amzCall(self.AMapi.artistDetailsMetadata,'getArtistDetails',None,asin,None)
        items = resp
        self.setAddonContent('artistdetails',items,'albums',None,asin)
    def createQueue(self,asin):
        resp = self.AMc.amzCall(self.AMapi.createQueue,'createQueue',None,asin,None)
        token = resp['queue']['pageToken']
        tracklist = resp['trackMetadataList']
        i = 1
        while token: # 5 songs per loop
            resp = self.AMc.amzCall(self.AMapi.QueueGetNextTracks,'getNextTracks',None,asin,token)
            token = resp['nextPageToken']
            for item in resp['trackMetadataList']:
                tracklist.append(item)
            if i == 10:
                break
            i += 1
        self.setAddonContent('stationList',tracklist,'songs')
    # kodi visualization
    def getMeta(self,resp,filter):
        meta = []
        for item in resp:
            if len(filter) == 1:
                meta.append(item[filter['array1']])
            else:
                meta.append(item[filter['array1']][filter['array2']])
        seen = set()
        uniq = [x for x in meta if x not in seen and not seen.add(x)] # make it unique
        return self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,uniq,['fullAlbumDetails'])#['albumList']
    def getMetaTracks(self,filter):
        return self.AMc.amzCall(self.AMapi.V3getTracks,'getMetaTracks',None,filter,None)
    def setData(self,item,filter):
        if 'update' in filter and filter['update']:
            info = filter['info']
            meta = filter['meta']
        else:
            info = {
                'tracknumber':  None,
                'discnumber':   None,
                'duration':     None,
                'year':         None,
                'genre':        None,
                'album':        None,
                'artist':       None,
                'title':        None,
                'rating':       None
            }
            meta = {
                'mode':         None,
                'asin':         None,
                'objectId':     None,
                'thumb':        None,
                'purchased':    False,
                'isPrime':      False,
                'isUnlimited':  False,
                'color':        '%s',
                'isPlayable':   True
            }
            meta['mode'] = filter['mode']
        # tracknumber : discnumber : duration : year : genre : album : artist : title : rating
        # if 'isAlbum' in filter and filter['isAlbum']:
        #     #filter['isAlbum'] = filter['isAlbum']
        #     if 'totalNumberOfTracks' in item:
        #         info['tracknumber'] = item['totalNumberOfTracks']
        # else:
        #     if 'trackNum' in item:
        #         info['tracknumber'] = item['trackNum']
        #     if 'trackCount' in item:
        #         info['tracknumber'] = item['trackCount']
        #     if 'totalTrackCount' in item:
        #         info['tracknumber'] = item['totalTrackCount']

        if 'trackNum' in item:
            info['tracknumber'] = item['trackNum']
        elif 'trackCount' in item:
            info['tracknumber'] = item['trackCount']
        elif 'totalTrackCount' in item:
            info['tracknumber'] = item['totalTrackCount']
        elif 'totalNumberOfTracks' in item:
            info['tracknumber'] = item['totalNumberOfTracks']

        if 'discNum' in item:
            info['discnumber'] = item['discNum']

        if 'duration' in item:
            info['duration'] = item['duration']
        elif 'durationSeconds' in item:
            info['duration'] = item['durationSeconds']

        if 'albumReleaseDate' in item:
            info['year'] = item['albumReleaseDate'][:4]

        if 'primaryGenre' in item:
            info['genre'] = item['primaryGenre']
        elif 'genreName' in item:
            info['genre'] = item['genreName']
        elif 'productDetails' in item:
            info['genre'] = item['productDetails']['primaryGenreName']

        if 'albumName' in item:
            info['album'] = item['albumName']
        if 'description' in item:
            info['album'] = item['description']
        if 'stationTitle' in item:
            info['album'] = item['stationTitle']
        if 'album' in item:
            try:
                info['album'] = item['album']['name']
            except:
                info['album'] = item['album']['title']

        if 'albumArtistName' in item:
            info['artist'] = item['albumArtistName']
        if 'artist' in item:
            info['artist'] = item['artist']['name']
        if 'artistName' in item:
            info['artist'] = item['artistName']

        if 'stationTitle' in item:
            info['title'] = item['stationTitle']
        if 'displayName' in item:
            info['title'] = item['displayName']

        if 'isAlbum' in filter and filter['isAlbum']:
            if info['title'] == None and 'albumName' in item:
                info['title'] = item['albumName']
        else:
            if 'title' in item:
                info['title'] = item['title']
            if info['title'] == None and 'name' in item:
                info['title'] = item['name']

        if 'reviews' in item:
            info['rating'] = item['reviews']['average']
        if 'rating' in item:
            info['rating'] = item['rating']
        if 'averageOverallRating' in item:
            info['rating'] = item['averageOverallRating']

        # mode : asin : objectId : thumb : purchased : isPrime : isUnlimited
        # order of 'playlistId' and 'asin' is important. Do not change the order -> reason: followed playlists
        if 'playlistId' in item:
            meta['asin'] = item['playlistId']
        if 'asin' in item:
            meta['asin'] = item['asin']
        if 'seedId' in item:
            meta['asin'] = item['seedId']
        if 'categoryId' in item:
            meta['asin'] = item['categoryId']
        if 'stationKey' in item:
            meta['asin'] = item['stationKey']
        if 'identifier' in item:
            meta['asin'] = item['identifier']
        if 'isAlbum' in filter and filter['isAlbum']:
            if 'albumAsin' in item:
                meta['asin'] = item['albumAsin']

        if 'trackId' in item:
            meta['objectId'] = item['trackId']
        if 'objectId' in item:
            meta['objectId'] = item['objectId']
        if 'stationSeedId' in item:
            meta['objectId'] = item['stationSeedId']

        if 'image' in item:
            meta['thumb'] = item['image']
        if 'imageFull' in item:
            meta['thumb'] = item['imageFull']
        if 'albumCoverImageFull' in item:
            meta['thumb'] = item['albumCoverImageFull']
        if 'albumArtImageUrl' in item:
            meta['thumb'] = item['albumArtImageUrl']
        if 'stationImageUrl' in item and item['stationImageUrl'] is not None:
            meta['thumb'] = item['stationImageUrl']
        if 'foregroundImageUrl' in item and item['foregroundImageUrl'] is not None:
            meta['thumb'] = item['foregroundImageUrl']
        if 'artOriginal' in item:
            meta['thumb'] = item['artOriginal']['URL']
        if 'artFull' in item:
            meta['thumb'] = item['artFull']['URL']
        if 'artUrlMap' in item:
            meta['thumb'] = item['artUrlMap']['FULL']
        if 'fourSquareImage' in item:
            meta['thumb'] = item['fourSquareImage']['url']
        try:
            meta['thumb'] = item['album']['image']
        except:
            pass

        if (('purchased' in item and (item['purchased'] == True or item['purchased'] == 'true')) or
            ('isPurchased' in item and (item['isPurchased'] == True or item['isPurchased'] == 'true'))):
            meta['purchased'] = True

        if (('isPrime' in item and (item['isPrime'] == True or item['isPrime'] == 'true')) or
            ('primeStatus' in item and item['primeStatus'] == 'PRIME') or
            ('serviceTier' in item and item['serviceTier'] == 'PRIME') or
            ('playlistId' in item) or
            ('isStation' in filter and filter['isStation'] == True)):
            meta['isPrime'] = True

        if ('isMusicSubscription' in item and (item['isMusicSubscription'] == True or item['isMusicSubscription'] == 'true')):
            meta['isUnlimited'] = True

        if self.AMs.showcolentr:
            if meta['purchased']:
                meta['color'] = '[COLOR gold]%s[/COLOR]'
            elif meta['isPrime'] or 'stationMapIds' in item:
                meta['color'] = '%s'
            elif meta['isUnlimited']:
                meta['color'] = '[COLOR blue]%s[/COLOR]'
            else:
                meta['color'] = '[COLOR red]%s[/COLOR]'

        if ((self.AMs.accessType == 'PRIME'     and not meta['isPrime'] and not meta['purchased']) or
            (self.AMs.accessType == 'UNLIMITED' and not meta['isPrime'] and not meta['purchased'] and not meta['isUnlimited'] )):
            meta['isPlayable'] = False
        else:
            meta['isPlayable'] = True

        if (self.AMs.accessType == 'UNLIMITED' and meta['isUnlimited']):
            meta['isPlayable'] = True
        
        #self.AMs.log('vor: ' + str(info['tracknumber']))
        if 'isList' in filter and filter['isList'] and info['tracknumber'] is not None:
            info['title'] =  '{}  ({} Hits'.format(info['title'],info['tracknumber'])
            if info['duration'] is not None:
                info['title'] =  '{} - {}'.format(info['title'],datetime.timedelta(seconds=info['duration']))
            info['title'] =  '{})'.format(info['title'])
            info['tracknumber'] = None
        #self.AMs.log('nach: ' + str(info['tracknumber']))
        #self.AMs.log(info)
        #self.AMs.log(meta)
        return (info,meta)
    def setItem(self,inf,met):
        li = xbmcgui.ListItem(label=met['color'] % (inf['title']))
        if not met['thumb'] == None:
            li.setArt(self.setImage(met['thumb']))
        li.setInfo(type="music", infoLabels=inf)
        if not met['isPlayable']: # workaround for unplayable items
            met['mode'] = '1234'
        url = self.setUrl(inf,met)
        li.setProperty('IsPlayable', str(met['isPlayable']))
        # self.AMs.log(url)
        # self.AMs.log(inf)
        # self.AMs.log(met)
        return (url,li)
    def setListItem(self,itemList,item,param):
        inf, met = self.setData(item,param)
        url, li  = self.setItem(inf,met)
        itemList.append((url, li, True))
        return itemList
    def setImage(self,img):
        if self.AMs.showimages:
            return ({'icon':img,'thumb':img,'fanart':img,'poster':img,'banner':img,'landscape':img})
        else:
            return ({'thumb':img}) # there is a bug in the listitems, after setting multiple arts, setInfo shows the Genre only
    def addPaginator(self,itemList,resultToken,resultLen):
        if not resultToken == None and not len(resultLen) < self.AMs.maxResults: # next page
            itemList.append(self.setPaginator(resultToken))
        return itemList
    def setPaginator(self,nextToken,query=None,asin=None):
        li = xbmcgui.ListItem(label=self.AMs.translation(30020))
        li.setProperty('IsPlayable', 'false')
        url = "{}?mode={}&token={}".format(self.AMs.addonBaseUrl,str(self.AMs.addonMode[0]),str(nextToken))
        if query:
            url += "&query={}".format(urlquoteplus(query.encode("utf8")))
        if asin:
            url += "&asin={}".format(urlquoteplus(asin.encode("utf8")))
        return (url, li, True)
    def setUrl(self,inf,met):
        url = {
            'mode':     met['mode'],
            'asin':     met['asin']
        }
        if met['objectId'] is not None:
            url['objectId'] = met['objectId']
        return '{}?{}'.format(self.AMs.addonBaseUrl,urlencode(url))
    def setAddonContent(self,mode,param,ctype,stype=None,query=None):
        itemlist = []
        meta = []
        mod = None
        mediatype = ['playlistLibraryAvailability','expandTracklist','trackLibraryAvailability','collectionLibraryAvailability']
        if   mode == 'albumList' or mode == 'playlistList':
            meta = self.getMetaTracks(param[0]['asin'])['resultList']
            for item in param[0]['tracks']:
                inf, met = self.setData(item,{'mode':'getTrack'})
                for i in meta:
                    if item['asin'] == i['metadata']['asin']:
                        inf, met = self.setData(i['metadata'],{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                inf['album'] = param[0]['title']
                inf['rating'] = param[0]['reviews']['average']
                met['thumb'] = param[0]['image']
                met['album'] = param[0]['title']
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'artistList':      # no content at the moment
            self.AMs.log('artistList')
        elif mode == 'trackInfoList':           # track info list
            for item in param:
                meta.append(item['metadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'stationList':             # station playlist
            for item in param:
                meta.append(item['identifier'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self.setData(item,{'mode':'getTrack'})
                for i in meta:
                    if item['identifier'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                itemlist.append((url, li, False))
        elif mode == 'playlists':               # playlists
            for item in param['playlistList']:
                self.setListItem(itemlist,item,{'mode':'lookup','isList':True})
            self.addPaginator(itemlist,param['nextTokenMap']['playlist'],param['playlistList'])
        elif mode == 'followedplaylists':       # followed playlists
            for item in param['playlists']:
                self.setListItem(itemlist,item,{'mode':'lookup','isList':True})
        elif mode == 'ownedplaylists':          # owned playlists
            for item in param['playlists']:
                inf, met = self.setData(item,{'mode':'getPlaylistsByIdV2','isList':True})
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, True))
        elif mode == 'getplaylistsbyid':        # playlists by Id
            for item in param['playlists']:
                for track in item['tracks']:
                    meta.append(track['metadata']['requestedMetadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param['playlists']:
                for track in item['tracks']:
                    inf, met = self.setData(track['metadata']['requestedMetadata'],{'mode':'getTrack'})
                    for i in meta:
                        if track['metadata']['requestedMetadata']['asin'] == i['asin']:
                            inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                        else:
                            continue
                    url, li  = self.setItem(inf,met)
                    if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                        continue
                    itemlist.append((url, li, False))
        elif mode == 'recplaylists':            # recommended playlists
            for item in param['playlists']:
                self.setListItem(itemlist,item,{'mode':'lookup','isList':True})
            self.addPaginator(itemlist,param['nextResultsToken'],param['playlists'])
        elif mode == 'recalbums':               # recommended albums
            for item in param['albums']:
                self.setListItem(itemlist,item,{'mode':'lookup','isAlbum':True,'isList':True})
            self.addPaginator(itemlist,param['nextResultsToken'],param['albums'])
        elif mode == 'recstations':             # recommended stations
            for item in param['stations']:
                self.setListItem(itemlist,item,{'mode':'createQueue'})
            self.addPaginator(itemlist,param['nextResultsToken'],param['stations'])
        elif mode == 'recentlyplayed':          # recently played songs
            for item in param['recentTrackList']:
                inf, met = self.setData(item,{'mode':'getTrack'})
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextToken'],param['recentTrackList'])
        elif mode == 'newrecom':                # new recommendations
            for item in param:
                i = item['hint']['__type']
                #self.AMs.log(i)
                if (('AlbumHint'    in i) or
                    ('PlaylistHint' in i) or
                    ('ArtistHint'   in i)):
                    ctype   = 'albums'
                    mod     = {'mode':'lookup'}
                    fold    = True
                elif 'StationHint' in i:
                    ctype   = 'albums'
                    mod     = {'mode':'createQueue'}
                    fold    = True
                elif 'TrackHint' in i:
                    ctype   = 'songs'
                    mod    = {'mode':'getTrack'}
                    fold    = False
                inf, met = self.setData(item['hint'],mod)
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
        elif mode == 'recentlyaddedsongs':      # recently added songs
            for item in param['trackInfoList']:
                meta.append(item['metadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param['trackInfoList']:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextResultsToken'],param['trackInfoList'])
        elif mode == 'stations':                # (all) stations
            items = param['categories'].get('allStations')['stationMapIds']
            for item in items:
                self.setListItem(itemlist,param['stations'].get(item),{'mode':'createQueue'})
        elif mode == 'allartistsstations':      # (all artists) stations
<<<<<<< HEAD
=======
            # items = param['categories'].get('artistsAZ')['stationMapIds']
            #for item in items:
            #    inf, met = self.setData(param['stations'].get(item),{'mode':'createQueue'})
            #    url, li  = self.setItem(inf,met)
            #    itemlist.append((url, li, True))
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
            items = param['stations']
            for item in items:
                i = param['stations'].get(item)
                if not i['seedType'] == 'ARTIST':
                    continue
<<<<<<< HEAD
                self.setListItem(itemlist,i,{'mode':'createQueue'})
=======
                inf, met = self.setData(i,{'mode':'createQueue'})
                url, li  = self.setItem(inf,met)
                itemlist.append((url, li, True))
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
        elif mode == 'genres':                  # genre 1st level
            for sec in param['sections']:
                if sec['sectionId'] == 'genres':
                    for item in sec['categoryMapIds']:
                        self.setListItem(itemlist,param['categories'].get(item),{'mode':'getGenres2','isStation':True})
                else:
                    continue
        elif mode == 'genres2':                 # genres 2nd level
            asin = self.AMs.addonArgs.get('asin', None)[0]
            items = param['categories'].get(asin)['stationMapIds']
            for item in items:
                self.setListItem(itemlist,param['stations'].get(item),{'mode':'createQueue'})
        elif mode == 'purchasedalbums':         # purchased and owned albums
            for item in param['searchReturnItemList']:
                meta.append(item['metadata']['asin'])
            meta = self.AMc.amzCall(self.AMapi.lookup,'itemLookup',None,meta,['fullAlbumDetails'])['albumList']
            for item in param['searchReturnItemList']:
                inf, met = self.setData(item['metadata'],{'mode':'lookup','isAlbum':True})
                for i in meta:
                    if item['metadata']['albumAsin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'isAlbum':True,'update':True,'isList':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                itemlist.append((url, li, True))
            self.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])
        elif mode == 'purchasedsongs':          # purchased and owned songs
            meta = self.getMeta(param['searchReturnItemList'],{'array1':'metadata','array2':'albumAsin'})['albumList']
            for item in param['searchReturnItemList']:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])
        elif mode == 'searchitems':             # search items (songs / albums)
            for item in param['hits']:
                if stype == 'albums':
                    mod  = {'mode':'lookup'}
                    fold = True
                elif stype == 'tracks' or stype == 'artists':
                    mod  = {'mode':'getTrack'}
                    fold = False
                inf, met = self.setData(item['document'],mod)
                url, li  = self.setItem(inf,met)
                if not self.AMs.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchplaylists':         # search playlists
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'lookup'})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchartists':           # search artists
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'getArtistDetails'})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchstations':          # search stations
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'createQueue','query':query})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.AMs.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'artistdetails':           # artitist details (albums)
            for item in param['albumList']:
                self.setListItem(itemlist,item,{'mode':'lookup'})
            try:
                if len(param['albumList']) == self.AMs.maxResults:
                    itemlist.append(self.setPaginator(param['nextTokenMap']['album'],None,query))
                    itemlist.append((url, li, True))
            except:
                pass
        self.finalizeContent(itemlist,ctype)
        xbmc.sleep(100)
    def finalizeContent(self,itemlist,ctype):
<<<<<<< HEAD
        xbmcplugin.addDirectoryItems(self.AMs.addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(self.AMs.addonHandle, ctype)
        xbmcplugin.endOfDirectory(self.AMs.addonHandle)
=======
        xbmcplugin.addDirectoryItems(self.addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(self.addonHandle, ctype)
        xbmcplugin.endOfDirectory(self.addonHandle)
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
    # play music
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
                ''' proxy try - START '''
                song = 'http://{}/mpd/{}'.format(xbmcaddon.Addon().getSetting('proxy'),'song.mpd')
                ''' proxy try - END '''
                stream['ia']  = True
                stream['lic'] = True
        if song == None:
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.AMs.translation(30073),' ',self.AMs.translation(30074)))
            return False
        self.finalizeItem(song,stream['ia'],stream['lic'])        
    def tryGetStream(self,asin,objectId):
        if objectId == None:
            resp = self.AMc.amzCall(self.AMapi.stream,'getTrack',None,asin,'ASIN')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['statusCode'] == 'MAX_CONCURRENCY_REACHED':
                xbmc.PlayList(0).clear()
                xbmc.Player().stop()
                xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.AMs.translation(30073),' ',self.AMs.translation(30075)))
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        else:
            resp = self.AMc.amzCall(self.AMapi.stream,'getTrack',None,objectId,'COID')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['contentResponse']['statusCode'] == 'CONTENT_NOT_ELIGIBLE' or obj['contentResponse']['statusCode'] == 'BAD_REQUEST':
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        return song
    def tryGetStreamHLS(self,asin,objectId):
        resp = self.AMc.amzCall(self.AMapi.streamHLS,'getTrackHLS',None,asin,'ASIN')
        return re.compile('manifest":"(.+?)"',re.DOTALL).findall(resp.text)
    def tryGetStreamDash(self,asin,objectId):
<<<<<<< HEAD
        resp = self.AMc.amzCall(self.AMapi.streamDash,'getTrackDash',None,asin,'ASIN')
        return json.loads(resp.text)['contentResponseList'][0]['manifest']
    def finalizeItem(self,song,ia=False,lic=False):
        li = xbmcgui.ListItem(path=song)
        if ia:
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.stream_headers', 'user-agent={}'.format(self.AMs.userAgent))
=======
        resp = self.amzCall(self.API_streamDash,'getTrackDash',None,asin,'ASIN')
        manifest = json.loads(resp.text)['contentResponseList'][0]['manifest']
        if manifest:
            lic = self.getLicenseKey()
            song = self.writeSongFile(manifest,'mpd')
            li = xbmcgui.ListItem(path=song)
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.stream_headers', 'user-agent={}'.format(self.userAgent))
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if lic:
                li.setProperty('inputstream.adaptive.license_key', self.getLicenseKey() )
            li.setProperty('isFolder', 'false')
            li.setProperty('IsPlayable', 'true')
            # li.setInfo('video', {})
            li.setMimeType('application/dash+xml')
        li.setInfo('audio', {'codec': 'aac'})
        li.addStreamInfo('audio', {'codec': 'aac'})
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.AMs.addonHandle, True, listitem=li)
    def writeSongFile(self,manifest,ftype='m3u8'):
        song = '{}{}song.{}'.format(self.AMs.addonUDatFo,os.sep,ftype)
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
    def getLicenseKey(self):
        amzUrl = self.AMapi.LicenseForPlaybackV2
        url = '{}/{}/api/{}'.format(self.AMs.url, self.AMs.region, amzUrl['path'])
        head = self.AMs.prepReqHeader(amzUrl['target'])

        cookiedict = {}
        for cookie in self.AMs.cj:
            cookiedict[cookie.name] = cookie.value

        cj_str = ';'.join(['%s=%s' % (k, v) for k, v in cookiedict.items()])

        head['Cookie'] = cj_str
        licHeader = '&'.join(['%s=%s' % (k, urlquote(v, safe='')) for k, v in head.items()])
        licBody = self.AMc.prepReqData('getLicenseForPlaybackV2')
        # licURL expected (req / header / body / response)
        return '{}|{}|{}|JBlicense'.format(url,licHeader,licBody)
    def getSoccerFilter(self,target=None): # 'BUND', 'BUND2', 'CHAMP', 'DFBPOKAL', 'SUPR'
        menuEntries = []
        resp = self.AMc.amzCall(self.AMapi.GetSoccerMain,'getSoccerMain',None,None,target)
        idx = resp['blocks'][0]['positionSelector']['currentPosition']['blockIndex'] # current matchday
        if idx == -1: # if no entries are available
<<<<<<< HEAD
            menuEntries.append({'txt':'Empty List','fct':None,'target':None,'img':self.AMs.getSetting('img_soccer'),'playable':False})
=======
            menuEntries.append({'txt':'Empty List','fct':None,'target':None,'img':self.getSetting('img_soccer'),'playable':False})
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
            self.createList(menuEntries,False,True)
            return
        param = resp['blocks'][0]['positionSelector']['positionOptions']
        idx1 = 0
        for item in param: # find last matchday based on current matchday
            if item['blockIndex'] < idx:
                idx1+=1
                continue
            break
        idx1-= 1
        if idx1 < 0:
            idx1 = 0
        idx1 = resp['blocks'][0]['positionSelector']['positionOptions'][idx1]['blockIndex'] # last matchday index
        playable = True
        fct = None
        while idx1 <= idx: # + 1: # next match day is now visible
            dat = resp['blocks'][0]['blocks'][idx1]['title'] # day of matchday
            for item in resp['blocks'][0]['blocks'][idx1]['blocks']:
                img = None
                if 'programHint' in item: # show matches only
                    target = item['programHint']['programId']
                    streamStatus = item['programHint']['streamStatus']
                else:
                    target = None
                    streamStatus = None
                    continue
                title = '{}  {}'.format(dat,item['title'])
                if 'decorator1' in item and item['decorator1'] is not None:
                    if len(str(item['decorator1'])) > 0:
                        title+= '   {}:{}'.format(str(item['decorator1']),str(item['decorator2']))
                if 'title1' in item:
                    title+= '   {}'.format(item['title1'])
                if 'title2' in item and item['title2'] is not None:
                    title+= ' - {}'.format(item['title2'])
                if 'image3' in item:
                    img = item['image3']['IMAGE_PROGRAM_COVER']
                else:
                    img = item['image']
                if streamStatus == 'PAST': # ignore outdated conferences
                    continue
                elif streamStatus == 'FUTURE': # future matches are not playable
                    playable = False
                    fct = None
                elif streamStatus == 'AVAILABLE':
                    playable = True
                    fct = 'getSoccerOnDemand'
                elif streamStatus == 'LIVE':
                    playable = True
                    fct = 'getSoccerLive'
                else: # unknown status
                    playable = False
                    fct = None
                menuEntries.append({'txt':title,'fct':fct,'target':target,'img':img,'playable':playable})
            idx1 += 1
        self.createList(menuEntries,False,True)
    def getSoccer(self,target,status):
        if status == 'LIVE':
<<<<<<< HEAD
            amz = { 'path': self.AMapi.GetSoccerLiveURLs,
                    'target': 'getSoccerLiveURL' }
        elif status == 'ONDEMAND':
            amz = { 'path': self.AMapi.GetSoccerOnDemandURLs,
                    'target': 'getSoccerOnDemandURL' }
        else:
            return False
        resp = self.AMc.amzCall(self.AMapi.GetSoccerProgramDetails,'getSoccerProgramDetails',None,None,target)
=======
            amz = {
                'path': self.API_GetSoccerLiveURLs,
                'target': 'getSoccerLiveURL'
            }
        elif status == 'ONDEMAND':
            amz = {
                'path': self.API_GetSoccerOnDemandURLs,
                'target': 'getSoccerOnDemandURL'
            }
        else:
            return False
        resp = self.amzCall(self.API_GetSoccerProgramDetails,'getSoccerProgramDetails',None,None,target)
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7
        try:
            target = resp['program']['mediaContentList'][0]['mediaContentId']
        except:
            return False
        # target for xml source
<<<<<<< HEAD
        resp = self.AMc.amzCall(amz['path'],amz['target'],'soccer',None,target)
        target = resp['Output']['contentResponseList'][0]['urlList'][0] # link to mpd file
        r = requests.get(target)
        song = self.writeSongFile(r.content.decode('utf-8'),'mpd')

        ''' proxy try - START '''
        song = 'http://{}/mpd/{}'.format(xbmcaddon.Addon().getSetting('proxy'),'song.mpd')
        ''' proxy try - END '''
        self.finalizeItem(song,True)
=======
        resp = self.amzCall(amz['path'],amz['target'],'soccer',None,target)
        target = resp['Output']['contentResponseList'][0]['urlList'][0] # link to mpd file
        r = requests.get(target)
        song = self.writeSongFile(r.content,'mpd')
        # get the xml file and extract the source
        li = xbmcgui.ListItem(path=song)
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.stream_headers', 'user-agent={}'.format(self.userAgent))
        li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        #li.setProperty('inputstream.adaptive.license_key', lic)
        li.setProperty('isFolder', 'false')
        li.setProperty('IsPlayable', 'true')
        li.setInfo('video', {})
        li.setMimeType('application/dash+xml')
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.addonHandle, True, listitem=li)
    def getLicenseKey(self):
        amzUrl = self.API_LicenseForPlaybackV2
        url = '{}/{}/api/{}'.format(self.url, self.region, amzUrl['path'])
        head = self.prepReqHeader(amzUrl['target'])

        cookiedict = {}
        for cookie in self.cj:
            cookiedict[cookie.name] = cookie.value

        cj_str = ';'.join(['%s=%s' % (k, v) for k, v in cookiedict.items()])

        head['Cookie'] = cj_str
        licHeader = '&'.join(['%s=%s' % (k, urlquote(v, safe='')) for k, v in head.items()])
        licBody = self.prepReqData('getLicenseForPlaybackV2')
        # licURL expected (req / header / body / response)
        return '{}|{}|{}|JBlicense'.format(url,licHeader,licBody)
    def getMaestroID(self):
        return 'Maestro/1.0 WebCP/1.0.202638.0 ({})'.format(self.generatePlayerUID())
    def generatePlayerUID(self):
        a = str(float.hex(math.floor(16 * (1 + random.random()))))[4:5]
        return '{}-{}-dmcp-{}-{}{}'.format(self.doCalc(),self.doCalc(),self.doCalc(),self.doCalc(),a)
    def doCalc(self):
        return str(float.hex(math.floor(65536 * (1 + random.random()))))[4:8]
>>>>>>> 8329005b02034e75c21395e0cc7221f09a41b4b7

if __name__ == '__main__':
    amz = AmazonMedia()
    amz.reqDispatch()
