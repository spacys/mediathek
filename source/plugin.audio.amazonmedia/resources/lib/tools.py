#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from resources.lib.singleton import Singleton
import urllib.parse as urlparse
import http.cookiejar as cookielib
#import requests
import xbmc
import xbmcaddon
import xbmcvfs

class AMtools(Singleton):
    _globals = {}
    """ Allow the usage of dot notation for data inside the _globals dictionary, without explicit function call """
    def __getattr__(self, name):
        return self._globals[name]

    def __init__(self):
        self._globals['maxResults']     = 100
        self._globals['siteVerList']    = ['de', 'fr', 'co.uk', 'it', 'es']
        self._globals['audioQualist']   = ['HIGH','MEDIUM','LOW']
        self.setVariables()

    def setVariables(self):
        """ initialize gloabl addon variables """
        self._globals['addon']          = xbmcaddon.Addon()
        self._globals['addonBaseUrl']   = sys.argv[0]
        self._globals['addonHandle']    = int(sys.argv[1])
        self._globals['addonArgs']      = urlparse.parse_qs(sys.argv[2][1:])
        self._globals['addonMode']      = self._globals['addonArgs'].get('mode', None)
        self._globals['addonFolder']    = self.getFolder('special://home/addons/{}'.format(self.getInfo('id')))
        self._globals['addonUDatFo']    = self.getFolder('special://profile/addon_data/{}'.format(self.getInfo('id')))
        self._globals['reqloop']        = 0

        if not xbmcvfs.exists(self._globals['addonUDatFo']):
            xbmcvfs.mkdirs(self._globals['addonUDatFo'])

        if not xbmcvfs.exists(os.path.join(self._globals['addonFolder'], 'settings.xml')):
            self.setSetting('captcha', '')

        self._globals['siteVersion']    = self.getSetting('siteVersion')
        self._globals['logonURL']       = 'https://www.amazon.{}/gp/aw/si.html'.format(self._globals['siteVerList'][int(self._globals['siteVersion'])])
        self._globals['musicURL']       = 'https://music.amazon.{}'.format(self._globals['siteVerList'][int(self._globals['siteVersion'])])
        self._globals['url']            = self.getSetting('url')

        self._globals['logging']        = self.getSetting('logging')

        if not self.getSetting('saveUsername'): self.setSetting('userEmail', '')
        if not self.getSetting('savePassword'): self.setSetting('userPassword', '')

        self._globals['deviceId']       = self.getSetting('deviceId')
        self._globals['deviceType']     = self.getSetting('deviceType')
        self._globals['customerId']     = self.getSetting('customerId')
        self._globals['marketplaceId']  = self.getSetting('marketplaceId')
        self._globals['musicTerritory'] = self.getSetting('musicTerritory')
        self._globals['region']         = self.getSetting('region')
        self._globals['locale']         = self.getSetting('locale')
        self._globals['customerLang']   = self.getSetting('customerLang')
        self._globals['accessType']     = self.getSetting('accessType')

        self._globals['audioQuality']   = self._globals['audioQualist'][int(self.getSetting('quality'))]
        self._globals['cj']             = cookielib.MozillaCookieJar()
        self._globals['cookieFile']     = os.path.join(self._globals['addonUDatFo'], 'cookie')

        if os.path.isfile(self._globals['cookieFile']):
            self.loadCookie()

    def getInfo(self,oProp):    return self._globals['addon'].getAddonInfo(oProp)
    def getFolder(self,oPath):  return xbmcvfs.translatePath(oPath)

    def getMode(self):
        self._globals['addonArgs']      = urlparse.parse_qs(sys.argv[2][1:])
        self._globals['addonMode']      = self._globals['addonArgs'].get('mode', [None])
        return self._globals['addonMode'][0]

    def getSetting(self,oProp):
        """ provide the current setting """
        prop = self._globals['addon'].getSetting(oProp)
        if (str.lower(prop) == 'true' or
            str.lower(prop) == 'false'):
            prop = self.toBool(prop)
        return prop

    def setSetting(self,oProp,val):
        """ save the given setting """
        self._globals['addon'].setSetting(oProp,val)

    def getTranslation(self,oId):
        """ provide the translation of oID """
        return self._globals['addon'].getLocalizedString(oId)

    def toBool(self,s):
        """ convert the given string to bool """
        if s == 'True' or s == 'true':
             return True
        else:
             return False

    def setCookie(self):    self._globals['cj'].save(self._globals['cookieFile'], ignore_discard=True, ignore_expires=True)
    def loadCookie(self):   self._globals['cj'].load(self._globals['cookieFile'])

    def log(self,msg=None,level=xbmc.LOGINFO):
        """ write some log data """
        fct_name  = sys._getframe(1).f_code.co_name
        lin_nmbr  = sys._getframe(1).f_lineno
        if msg:
            msg = '{}{}'.format(os.linesep,msg)
        else:
            msg = ''
        log_message = '[{}] {} : {}{}'.format(self.getInfo('name'), fct_name, lin_nmbr, msg)
        xbmc.log(log_message, level)

    def setSearch(self,q,query):
        """ store the last three search entries and keep the most recent on the 1st position """
        update = True
        for i in q:
            if self.getSetting(i) == query:
                update = False
                break
        if update:
            self.setSetting(q[2],self.getSetting(q[1]))
            self.setSetting(q[1],self.getSetting(q[0]))
            self.setSetting(q[0],query)

    def delFile(self,delFile):
        """ remove the given file """
        if os.path.exists(delFile):
            os.remove(delFile)

    def getUserInput(self,title,txt,hidden=False,uni=False):
        if self._globals['logging']: self.log()
        kb = xbmc.Keyboard()
        kb.setHeading(title)
        kb.setDefault(txt)
        kb.setHiddenInput(hidden)
        kb.doModal()
        if kb.isConfirmed() and kb.getText():
            if uni:
                ret = str(kb.getText(), encoding = 'utf-8')
            else:
                ret = kb.getText() # for password needed, due to encryption
        else:
            ret = False
        del kb
        return ret

    def prepReqHeader(self, amzTarget, referer=None):
        head = { 'Accept' : 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding' : 'gzip,deflate,br',
                'Accept-Language' : '{},en-US,en;q=0.9'.format(self._globals['siteVerList'][int(self.getSetting('siteVersion'))]),
                'csrf-rnd' :        self.getSetting('csrf_rnd'),
                'csrf-token' :      self.getSetting('csrf_token'),
                'csrf-ts' :         self.getSetting('csrf_ts'),
                'Host' :            'music.amazon.{}'.format(self._globals['siteVerList'][int(self.getSetting('siteVersion'))]),
                'Origin' :          self.getSetting('musicURL'),
                'User-Agent' :      self.getSetting('userAgent'),
                'X-Requested-With' : 'XMLHttpRequest'
        }
        if amzTarget is not None:
            head['Content-Encoding'] = 'amz-1.0'
            head['content-type'] = 'application/json'
            head['X-Amz-Target'] = amzTarget
        if referer == 'soccer':
            head['Content-Encoding'] = None
        return head

    def resetAddon(self):
        """ remove Cookie and Setting, initilialize the variables """
        self.delFile(self._globals['cookieFile'])
        data = {
            'siteVersion': '0',
            'quality': '0',
            'musicTerritory': '',
            'locale': '',
            'customerLang': '',
            'region': '',
            'url': '',
            'csrf_ts': '',
            'csrf_rnd': '',
            'csrf_token': '',
            'customerId': '',
            'marketplaceId': '',
            'deviceId': '',
            'deviceType': '',
            'saveUsername': 'false',
            'savePassword': 'false',
            'userEmail': '',
            'userPassword': '',
            'access': 'false',
            'logging': 'false',
            'showimages': 'true',
            'showUnplayableSongs': 'false',
            'showcolentr': 'true',
            'accessType': '',
            'search1PlayLists': '',
            'search2PlayLists': '',
            'search3PlayLists': '',
            'search1Albums': '',
            'search2Albums': '',
            'search3Albums': '',
            'search1Songs': '',
            'search2Songs': '',
            'search3Songs': '',
            'search1Stations': '',
            'search2Stations': '',
            'search3Stations': '',
            'search1Artists': '',
            'search2Artists': '',
            'search3Artists': '',
            'captcha': ''
        }
        for key, value in data.items():
            self.setSetting(key, value)
        
        self.setVariables()