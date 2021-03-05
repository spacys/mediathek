#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
#import xbmc
import os
import sys
import xbmc
import xbmcaddon
import xbmcvfs
import base64
import http.cookiejar as cookielib
import urllib.parse as urlparse

from .singleton import Singleton

class Settings(Singleton):
    """ Amazon Media Addon Settings """
    def __init__(self):
        self.logonProcess   = False
        self.setVariables()
    def setVariables(self):
        self.addon          = xbmcaddon.Addon()
        self.addonId        = self.getInfo('id')
        self.addonName      = self.getInfo('name')
        self.addonFolder    = self.getFolder('special://home/addons/{}'.format(self.addonId))
        self.addonUDatFo    = self.getFolder('special://profile/addon_data/{}'.format(self.addonId))
        # self.addonBaseUrl   = sys.argv[0]
        # self.addonHandle    = int(sys.argv[1])
        # self.addonArgs      = urlparse.parse_qs(sys.argv[2][1:])
        # self.addonMode      = self.addonArgs.get('mode', None)
        self.siteVerList    = ["de", "fr", "co.uk", "it", "es"]
        self.siteVersion    = self.getSetting("siteVersion")
        self.logonURL       = 'https://www.amazon.{}/gp/aw/si.html'.format(self.siteVerList[int(self.siteVersion)])
        self.musicURL       = 'https://music.amazon.{}'.format(self.siteVerList[int(self.siteVersion)])
        self.saveUsername   = self.toBool(self.getSetting("saveUsername"))
        if not self.logonProcess and not self.saveUsername:
            self.setSetting('savePassword', "false")
            self.setSetting('userEmail', "")
            self.setSetting('userPassword', "")
        self.savePassword   = self.toBool(self.getSetting("savePassword"))
        if not self.logonProcess and not self.savePassword:
            self.setSetting('userPassword', "")
        self.userEmail      = self.getSetting("userEmail")
        self.userPassword   = base64.urlsafe_b64decode(self.getSetting("userPassword"))
        self.captcha        = ""
        self.btn_cancel     = False
        self.userAgent      = self.getSetting("userAgent")
        self.deviceId       = self.getSetting("deviceId")
        self.csrf_token     = self.getSetting("csrf_token")
        self.csrf_ts        = self.getSetting("csrf_ts")
        self.csrf_rnd       = self.getSetting("csrf_rnd")
        self.customerId     = self.getSetting("customerId")
        self.marketplaceId  = self.getSetting("marketplaceId")
        self.deviceType     = self.getSetting("deviceType")
        self.musicTerritory = self.getSetting("musicTerritory")
        self.locale         = self.getSetting("locale")
        self.customerLang   = self.getSetting("customerLang")
        self.region         = self.getSetting("region")
        self.url            = self.getSetting("url")
        self.access         = self.toBool(self.getSetting("access"))
        self.accessType     = self.getSetting("accessType")
        self.maxResults     = 50
        self.audioQualist   = ["HIGH","MEDIUM","LOW"]
        self.audioQuality   = self.audioQualist[int(self.getSetting("quality"))]
        self.cj             = cookielib.MozillaCookieJar()
        self.logging        = self.toBool(self.getSetting("logging"))
        self.showimages     = self.toBool(self.getSetting("showimages"))
        self.showUnplayableSongs = self.toBool(self.getSetting("showUnplayableSongs"))
        self.showcolentr    = self.toBool(self.getSetting("showcolentr"))

        self.sPlayLists     = ["search1PlayLists","search2PlayLists","search3PlayLists"]
        self.sAlbums        = ["search1Albums","search2Albums","search3Albums"]
        self.sSongs         = ["search1Songs","search2Songs","search3Songs"]
        self.sStations      = ["search1Stations","search2Stations","search3Stations"]
        self.sArtists       = ["search1Artists","search2Artists","search3Artists"]

        if not xbmcvfs.exists(self.addonUDatFo):
            xbmcvfs.mkdirs(self.addonUDatFo)
        self.addonFolRes  = os.path.join(self.addonFolder, "resources")
        self.addonIcon    = os.path.join(self.addonFolder, "icon.png")
        self.cookieFile   = os.path.join(self.addonUDatFo, "cookie")
        if os.path.isfile(self.cookieFile):
            self.cj.load(self.cookieFile)
    def getInfo(self,oProp):
        return self.addon.getAddonInfo(oProp)
    def getSetting(self,oProp):
        return self.addon.getSetting(oProp)
    def setSetting(self,oProp,val):
        self.addon.setSetting(oProp,val)
    def getFolder(self,oPath):
        return xbmcvfs.translatePath(oPath)
    def toBool(self,s):
        if s == 'True' or s == 'true':
             return True
        else:
             return False
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
    def setCookie(self):
        self.cj.save(self.cookieFile, ignore_discard=True, ignore_expires=True)
    def delCookies(self):
        if os.path.exists(self.cookieFile):
            os.remove(self.cookieFile)
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
    def translation(self,oId):
        return self.addon.getLocalizedString(oId)
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
    def log(self, msg=None, level=xbmc.LOGINFO):
        # log_message = '[{}] {}'.format(self.addonName, msg)
        # xbmc.log(log_message, level)
        this_function_name  = sys._getframe(1).f_code.co_name
        this_line_number    = sys._getframe(1).f_lineno
        log_message = '[{}] {} : {}'.format(self.addonName, this_function_name, this_line_number)
        if msg: log_message = '{}\n{}'.format(log_message,msg)
        xbmc.log(log_message, level)
