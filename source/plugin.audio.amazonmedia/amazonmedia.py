#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import re
import os
import json
import math
import random
import base64
import datetime
import requests
import http.cookiejar as cookielib
import urllib.parse as urlparse
from urllib.parse import quote as urlquote
from urllib.parse import quote_plus as urlquoteplus
from urllib.parse import urlencode as urlencode
from bs4 import BeautifulSoup

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmcvfs
import mechanize

class AmazonMedia():
    def __init__(self):
        self.logonProcess   = False
        self.setVariables()
    def setVariables(self):
        self.addon          = xbmcaddon.Addon()
        self.addonId        = self.getInfo('id')
        self.addonName      = self.getInfo('name')
        self.addonFolder    = self.getFolder('special://home/addons/{}'.format(self.addonId))
        self.addonUDatFo    = self.getFolder('special://profile/addon_data/{}'.format(self.addonId))
        self.addonBaseUrl   = sys.argv[0]
        self.addonHandle    = int(sys.argv[1])
        self.addonArgs      = urlparse.parse_qs(sys.argv[2][1:])
        self.addonMode      = self.addonArgs.get('mode', None)
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
        self.reqloop        = 0
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
        self.accessType     = self.getSetting("accessType")
        self.maxResults     = 50
        self.audioQualist   = ["HIGH","MEDIUM","LOW","ALL"]
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
        self.content        = ""
        if not xbmcvfs.exists(self.addonUDatFo):
            xbmcvfs.mkdirs(self.addonUDatFo)
        self.addonFolRes    = os.path.join(self.addonFolder, "resources")
        self.addonIcon      = os.path.join(self.addonFolder, "icon.png")
        self.cookieFile     = os.path.join(self.addonUDatFo, "cookie")
        if os.path.isfile(self.cookieFile):
            self.cj.load(self.cookieFile)
            self.isCookie = True
        else:
            self.isCookie = False
        self.AMapi()
        if self.logging:
            self.log( 'Handle: ' + self.addonHandle.__str__() + '\n'
                    + 'Args  : ' + self.addonArgs.__str__() + '\n'
                    + 'Mode  : ' + self.addonMode.__str__())
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
        self.setSetting('showimages', "true")
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
        self.setSetting('captcha', "")
        self.setVariables()
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
    def getUserInput(self,title,txt,hidden=False,uni=False):
        if self.logging: self.log()
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
    def log(self, msg=None, level=xbmc.LOGINFO):
        fct_name  = sys._getframe(1).f_code.co_name
        lin_nmbr  = sys._getframe(1).f_lineno
        if msg:
            msg = '\n{}'.format(msg)
        else:
            msg = ''
        log_message = '[{}] {} : {}{}'.format(self.addonName, fct_name, lin_nmbr,msg)
        xbmc.log(log_message, level)
    ############ Start of Menu ##################################
    def menuHome(self):
        """
            Amazon Media Main Menu Entries
                'txt'    - String ID for translation
                'fct'    - Function to call
                'img'    - Folder/Background image
                'search' - last searched items
        """
        return [{'txt':30023,'fct':'menuPlaylists',         'img':'img_playlists'},
                {'txt':30024,'fct':'menuAlbums',            'img':'img_albums'},
                {'txt':30022,'fct':'menuSongs',             'img':'img_songs'},
                {'txt':30008,'fct':'menuStations',          'img':'img_stations'},
                {'txt':30015,'fct':'getGenres',             'img':'img_genres'},
                {'txt':30027,'fct':'menuArtists',           'img':'img_artists'},
                {'txt':30041,'fct':'getNewRecom',           'img':'img_newrecom'}#,
                #{'txt':30035,'fct':'menuSoccer',            'img':'img_soccer'}
                ]
    def menuPlaylists(self):
        return [{'txt':30013,'fct':'searchPlayLists',       'img':'img_search'},
                {'txt':30032,'fct':'search1PlayLists',      'img':'img_search','search':self.sPlayLists[0]},
                {'txt':30033,'fct':'search2PlayLists',      'img':'img_search','search':self.sPlayLists[1]},
                {'txt':30034,'fct':'search3PlayLists',      'img':'img_search','search':self.sPlayLists[2]},
                {'txt':30003,'fct':'getRecomPlayLists',     'img':'img_playlists'},
                {'txt':30002,'fct':'getNewPlayLists',       'img':'img_playlists'},
                {'txt':30001,'fct':'getPopularPlayLists',   'img':'img_playlists'},
                {'txt':30018,'fct':'getFollowedPlayLists',  'img':'img_playlists'},
                {'txt':30019,'fct':'getOwnedPlaylists',     'img':'img_playlists'}]
    def menuAlbums(self):
        return [{'txt':30010,'fct':'searchAlbums',          'img':'img_search'},
                {'txt':30032,'fct':'search1Albums',         'img':'img_search','search':self.sAlbums[0]},
                {'txt':30033,'fct':'search2Albums',         'img':'img_search','search':self.sAlbums[1]},
                {'txt':30034,'fct':'search3Albums',         'img':'img_search','search':self.sAlbums[2]},
                {'txt':30004,'fct':'getRecomAlbums',        'img':'img_albums'},
                {'txt':30012,'fct':'getPurAlbums',          'img':'img_albums'},
                {'txt':30007,'fct':'getAllAlbums',          'img':'img_albums'}]
    def menuSongs(self):
        return [{'txt':30011,'fct':'searchSongs',           'img':'img_search'},
                {'txt':30032,'fct':'search1Songs',          'img':'img_search','search':self.sSongs[0]},
                {'txt':30033,'fct':'search2Songs',          'img':'img_search','search':self.sSongs[1]},
                {'txt':30034,'fct':'search3Songs',          'img':'img_search','search':self.sSongs[2]},
                {'txt':30009,'fct':'getPurSongs',           'img':'img_songs'},
                {'txt':30006,'fct':'getAllSongs',           'img':'img_songs'},
                {'txt':30017,'fct':'getRecentlyPlayed',     'img':'img_songs'},
                {'txt':30021,'fct':'getRecentlyAddedSongs', 'img':'img_songs'}]
    def menuStations(self):
        return [{'txt':30016,'fct':'searchStations',        'img':'img_search'},
                {'txt':30032,'fct':'search1Stations',       'img':'img_search','search':self.sStations[0]},
                {'txt':30033,'fct':'search2Stations',       'img':'img_search','search':self.sStations[1]},
                {'txt':30034,'fct':'search3Stations',       'img':'img_search','search':self.sStations[2]},
                {'txt':30005,'fct':'getRecomStations',      'img':'img_stations'},
                {'txt':30026,'fct':'getStations',           'img':'img_stations'},
                {'txt':30025,'fct':'getAllArtistsStations', 'img':'img_stations'}]
    def menuArtists(self):
        return [{'txt':30014,'fct':'searchArtist',          'img':'img_search'},
                {'txt':30032,'fct':'search1Artists',        'img':'img_search','search':self.sArtists[0]},
                {'txt':30033,'fct':'search2Artists',        'img':'img_search','search':self.sArtists[1]},
                {'txt':30034,'fct':'search3Artists',        'img':'img_search','search':self.sArtists[2]}]
    def menuSoccer(self):
        return [{'txt':30036,'fct':'soccerBUND',            'img':'img_sBUND'},
                {'txt':30037,'fct':'soccerBUND2',           'img':'img_sBUND2'},
                {'txt':30038,'fct':'soccerDFBPOKAL',        'img':'img_sDFBPOKAL'},
                {'txt':30039,'fct':'soccerCHAMP',           'img':'img_sCHAMP'},
                {'txt':30040,'fct':'soccerSUPR',            'img':'img_sSUPR'}]
    ############ End of Menu ####################################
    ############ Start of Logon #################################
    def parseHTML(self,resp):
        if self.logging: self.log()
        resp = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', resp)
        return BeautifulSoup(resp, 'html.parser')
    def delCredentials(self):
        if self.logging: self.log()
        self.userEmail = ''
        self.userPassword = ''
    def getCredentials(self):
        if self.logging: self.log()
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
    def prepBrowser(self):
        if self.logging: self.log()
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_gzip(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_equiv(True)
        self.br.set_cookiejar(self.cj)
        self.br.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
             ('Accept-Encoding', 'deflate,br'),
             ('Accept-Language', '{},en-US;q=0.7,en;q=0.3'.format(self.siteVerList[int(self.siteVersion)])),
             ('Cache-Control', 'no-cache'),
             ('Connection', 'keep-alive'),
             ('Content-Type', 'application/x-www-form-urlencoded'),
             ('User-Agent', self.userAgent),
             ('csrf-token', self.csrf_token),
             ('csrf-rnd',   self.csrf_rnd),
             ('csrf-ts',    self.csrf_ts),
             ('Upgrade-Insecure-Requests', '1')]
    def amazonLogon(self):
        if self.logging: self.log()
        self.logonProcess = True
        self.addonMode = None
        self.access = False

        self.setSetting('access','false')
        self.prepBrowser()

        x = 1
        ret = False
        while not self.access:
            if x == 3:
                break
            if self.logging: self.log('loop: ' + str(x) + ' | access: ' + str(self.access))
            x+=1
            self.br.open(self.logonURL)
            # self.br.open('https://music.amazon.de')
            # self.br.open('https://www.amazon.de/gp/aw/si.html')
            # self.log(self.br.response().info())
            # self.log( str(self.br.response().read(), encoding = 'utf-8') )
            if not self.doLogonForm(): break
            if not self.checkMFA(): break
            if self.checkConfig():
                ret = True
                if self.logging: self.log('checkConfig - true')
                break
            else:
                if self.logging: self.log('checkConfig - false')
                continue
        return ret
    def doLogonForm(self):
        if self.logging: self.log()
        try:
            self.br.select_form(name="signIn")
            if not self.getCredentials():
                return False
            if not self.br.find_control("email").readonly:
                self.br["email"] = self.userEmail
            self.br["password"] = self.userPassword
            self.getLogonResponse()
            return True
        except:
            if not self.checkCaptcha() or self.btn_cancel:
                return False
            else:
                self.getLogonResponse()
                return True
    def getLogonResponse(self):
        if self.logging: self.log()
        self.br.submit()
        resp = self.br.response()
        self.setCookie()
        self.cj.load(self.cookieFile)
        self.content = str(resp.read(), encoding = 'utf-8')
    def checkConfig(self):
        if self.logging: self.log()
        app_config = None
        self.cj.load(self.cookieFile)
        head = self.prepReqHeader('')
        resp = requests.post(self.musicURL, data=None, headers=head, cookies=self.cj)
        self.setCookie()
        #self.log(resp.text)
        configfound = False
        soup = self.parseHTML(resp.text)
        script_list = soup.find_all('script')
        for scripts in script_list:
            # self.log(scripts.contents)
            if 'appConfig' in scripts.contents[0]:
                if self.logging: self.log('Config available')
                #######################
                # self.log(scripts.contents)
                #######################
                sc = scripts.contents[0]
                sc = sc.replace("window.amznMusic = ","")
                sc = sc.replace("appConfig:","\"appConfig\":")
                sc = sc.replace(" false,}","\"false\"}")
                sc = sc.replace(" false","\"false\"")
                sc = sc.replace(" true","\"true\"")
                sc = sc.replace(" null","\"null\"")
                sc = sc.replace("ssr","\"ssr\"")
                sc = sc.replace(os.linesep,"")
                sc = sc.replace(" ","")
                sc = sc.replace("/","_")
                sc = sc.replace("},};","}}")
                sc = sc.replace(",};","}")
                sc = sc.replace(";","")
                sc = sc.replace("\"ssr\":\"false\",","\"ssr\":\"false\"")
                # self.log(sc)
                if not 'tier' in sc:
                    break
                app_config = json.loads(sc)
                configfound = True
                break
            else:
                if self.logging: self.log('No config available')
                continue
        if not configfound:
            return False
        # self.log(app_config)
        self.access = True
        self.logonProcess = False
        self.setSetting('access','true')

        self.appConfig2(app_config['appConfig'])
        self.setVariables()
        self.prepBrowser()
        return True
    def checkMFA(self):
        if self.logging: self.log()
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
                    self.getLogonResponse()
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
        if self.logging: self.log()
        if inp:
            if action:
                xbmc.executebuiltin(action)
            self.br.select_form(nr=0)
            self.br[target] = inp
            self.getLogonResponse()
        else:
            return False
    def checkCaptcha(self):
        if self.logging: self.log()
        self.setSetting('captcha',"")
        self.br.select_form(action="/errors/validateCaptcha")
        self.content = str(self.br.response().read(), encoding = 'utf-8')
        soup = self.parseHTML(self.content)
        # self.log(soup)
        form = soup.find_all('form')
        msgheading = str(form[0].find('h4').renderContents().strip(), encoding = 'utf-8')
        img = form[0].find('img') #.renderContents().strip()
        # self.log(msgheading)
        # self.log(img['src'])
        self.btn_cancel = False
        self.showCaptcha('captcha.xml',img['src'],msgheading)
        self.captcha = self.getSetting('captcha')
        if self.captcha == "":
            return False
        self.br["field-keywords"] = self.captcha
        return True
    def showCaptcha(self,layout, imagefile, message):
        if self.logging: self.log()
        class Captcha(xbmcgui.WindowXMLDialog):
            def __init__(self, *args, **kwargs):
                self.image = kwargs["image"]
                self.text  = kwargs["text"]
                self.s     = kwargs["settings"]
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
                self.setSetting('captcha',self.inp)
                self.show_dialog()
            def onClick(self, controlid):
                # self.log(controlid)
                if controlid == self.btn_ok:
                    # self.log('btn_ok')
                    self.close()
                elif controlid == self.btn_cancel:
                    # self.log('btn_cancel')
                    self.captcha = ""
                    self.btn_cancel = True
                    self.close()
                elif controlid == self.btn_input:
                    # self.log('btn_input')
                    self.getUserInput('Captcha Entry')
        cp = Captcha(layout, self.addonFolder, 'Default', image=imagefile, text=message, settings=self.s)
        cp.doModal()
        del cp
    ############ End of Logon #################################
    ############ Start of AMZ Call ############################
    def getMaestroID(self):
        return 'Maestro/1.0 WebCP/1.0.202638.0 ({})'.format(self.generatePlayerUID())
    def generatePlayerUID(self):
        a = str(float.hex(float(math.floor(16 * (1 + random.random())))))[4:5]
        return '{}-{}-dmcp-{}-{}{}'.format(self.doCalc(),self.doCalc(),self.doCalc(),self.doCalc(),a)
    def doCalc(self):
        return str(float.hex(float(math.floor(65536 * (1 + random.random())))))[4:8]
    def amzCall(self,amzUrl,mode,referer=None,asin=None,mediatype=None):
        try:
            self.cj.load(self.cookieFile)
        except:
            if self.amazonLogon():
                self.cj.load(self.cookieFile)
            else:
                xbmc.executebuiltin('Notification("Error:", {}, 5000, )'.format(self.translation(30070)))
                return

        url = '{}/{}/api/{}'.format(self.url, self.region, amzUrl['path'])
        head = self.prepReqHeader(amzUrl['target'],referer)
        data = self.prepReqData(mode,asin,mediatype)
        resp = requests.post(url=url, data=data, headers=head, cookies=self.cj)
        self.setCookie()

        if self.logging:
            self.log('url: ' + url)
            self.log('reason: ' + resp.reason + ', code: ' + str(resp.status_code) + ', reqloop: ' + str(self.reqloop))
            self.log(resp.text)
        if resp.status_code == 401 :
            if self.reqloop < 1:
                self.reqloop = 1
                return self.amzCall(amzUrl,mode,referer,asin,mediatype)
            else:
                self.reqloop = 0
                if self.amazonLogon():
                    return self.amzCall(amzUrl,mode,referer,asin,mediatype)

        if mode == 'getTrack' or mode == 'getTrackHLS' or mode == 'getTrackDash':
            return resp
        else:
            return resp.json()
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
            if int(self.getSetting("quality")) == 3:
                audio = self.audioQualist[0] # fallback to quality 'high'
            else:
                audio = self.audioQuality
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
                'bitrateTypeList' : [ audio ], # self.audioQuality
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
        elif mode == 'getPodcasts': # test only
            data = {
                'customerId' :          self.customerId,
                'deviceToken' : {
                    'deviceTypeId' :    self.deviceType,
                    'deviceId' :        self.deviceId
                }
             }
            data = json.dumps(data)
        elif mode == 'getTrackDashV2': # test only
            if int(self.getSetting("quality")) == 3:
                audio = self.audioQualist[0] # fallback to quality 'high'
            else:
                audio = self.audioQuality
            # case "PRIME":
            #     return "ROBIN";
            # case "UNLIMITED":
            #     return "HAWKFIRE";
            # case "UNLIMITED_HD":
            #     return "KATANA";
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
                #'bitrateTypeList' : [ audio ], # self.audioQuality missing
                #'musicDashVersionList' : [ 'V2' ], # missing
                #'appInfo' : { # missing
                #    'musicAgent': mID
                #},
                'musicRequestIdentityContext': {
                    'musicIdentities': {
                        'musicAccountCid': self.customerId
                    }
                },
                'customerInfo' : {
                    'marketplaceId' :   self.marketplaceId,
                    # 'customerId' :      self.customerId,   # missing
                    'territoryId' :     self.musicTerritory,
                    'entitlementList' : [ 'ROBIN' ] # account mapping
                },
                'appMetadata': { 'https': 'true' },
                'clientMetadata': {
                    'clientId': 'WebCP',
                    'clientRequestId': ''
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
    ############ End of AMZ Call #################################
    """ Amazon Media APIs """
    def AMapi(self):
        """
        Amazon API definitions
        amzUrl      = AmazonBaseUrl + region + /api/ + path
        amzTarget   = target
        """
        self.APIbase = 'com.amazon.musicensembleservice.MusicEnsembleService.'
        self.APIgetBrowseRecommendations = {
            'path':   'muse/legacy/getBrowseRecommendations',
            'target': '{}{}'.format(self.APIbase,'getBrowseRecommendations')
        }
        self.APIlookup = {
            'path':   'muse/legacy/lookup',
            'target': '{}lookup'.format(self.APIbase)
        }
        self.APIgetAddToLibraryRecommendations = {
            'path':   'muse/legacy/getAddToLibraryRecommendations',
            'target': '{}getAddToLibraryRecommendations'.format(self.APIbase)
        }
        self.APIgetSimilarityRecommendations = {
            'path':   'muse/legacy/getSimilarityRecommendations',
            'target': '{}getSimilarityRecommendations'.format(self.APIbase)
        }
        self.APIgetMusicStoreRecommendations = {
            'path':   'muse/legacy/getMusicStoreRecommendations',
            'target': '{}getMusicStoreRecommendations'.format(self.APIbase)
        }
        self.APIartistDetailCatalog = {
            'path':   'muse/artistDetailCatalog',
            'target': '{}artistDetailCatalog'.format(self.APIbase),
            'method': 'POST'
        }
        self.APIgetStationSections = {
            'path':   'muse/stations/getStationSections',
            'target': '{}getStationSectionsGet'.format(self.APIbase),
            'method': 'GET'
        }
        self.APIartistDetailsMetadata = {
            'path':   'muse/artistDetailsMetadata',
            'target': '{}artistDetailsMetadata'.format(self.APIbase)
        }
        self.APIgetTopMusicEntities = { # playlists
            'path':   'muse/getTopMusicEntities',
            'target': '{}getTopMusicEntities'.format(self.APIbase)
        }
        self.APIbrowseHierarchyV2 = {
            'path':   'muse/browseHierarchyV2',
            'target': '{}browseHierarchyV2'.format(self.APIbase)
        }
        self.APIseeMore = {
            'path':   'muse/seeMore',
            'target': '{}seeMore'.format(self.APIbase)
        }
        self.APIgetHome = {
            'path':   'muse/getHome',
            'target': '{}getHome'.format(self.APIbase)
        }
        self.APIlookupStationsByStationKeys = {
            'path':   'muse/stations/lookupStationsByStationKeys',
            'target': '{}lookupStationsByStationKeys'.format(self.APIbase)
        }
        self.APIbase = 'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.'
        self.APIcreateQueue = { # genres
            'path':   'mpqs/voiceenabled/createQueue',
            'target': '{}createQueue'.format(self.APIbase)
        }
        self.APIQueueGetNextTracks = { # genres
            'path':   'mpqs/voiceenabled/getNextTracks',
            'target': '{}getNextTracks'.format(self.APIbase)
        }
        # get streaming url
        self.APIbase = 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.'
        self.APIstream  = { # ASIN / COID
            'path':   'dmls/',
            'target': '{}getRestrictedStreamingURL'.format(self.APIbase)
        }
        self.APIstreamHLS = { # ASIN (hlsVersion:V3)
            'path':   'dmls/',
            'target': '{}getHLSManifest'.format(self.APIbase)
        }
        self.APIstreamDash = { # ASIN (musicDashVersionList: ["V1", "V2"])
            'path':   'dmls/',
            'target': '{}getDashManifestsV2'.format(self.APIbase)
        }
        self.APILicenseForPlaybackV2 = {
            'path':   'dmls/',
            'target': '{}getLicenseForPlaybackV2'.format(self.APIbase)
        }
        self.APIgetStreamingURLsWithFirstChunkV2 = { # HD playback?
            'path':   'dmls/',
            'target': '{}getStreamingURLsWithFirstChunkV2'.format(self.APIbase)
        }
        self.APIsearch = {
            'path':   'textsearch/search/v1_1/',
            'target': 'com.amazon.tenzing.textsearch.v1_1.TenzingTextSearchServiceExternalV1_1.search'
        }
        # cirrus
        self.APIbase = 'com.amazon.cirrus.libraryservice.'
        self.APIcirrus   = {
            'path'  : 'cirrus/',
            'target': None
        }
        self.APIcirrusV1 = {
            'path':   'cirrus/',
            'target': '{}CirrusLibraryServiceExternal.'.format(self.APIbase)
        }
        self.APIcirrusV2 = {
            'path':   'cirrus/2011-06-01/',
            'target': '{}v2.CirrusLibraryServiceExternalV2.'.format(self.APIbase)
        }
        self.APIcirrusV3 = {
            'path':   'cirrus/v3/',
            'target': '{}v3.CirrusLibraryServiceExternalV3.'.format(self.APIbase)
        }
        self.APIV3getTracksByAsin = {
            'path':   'cirrus/v3/',
            'target': '{}getTracksByAsin'.format(self.APIcirrusV3['target'])
        }
        self.APIV3getTracks = {
            'path':   'cirrus/v3/',
            'target': '{}getTracks'.format(self.APIcirrusV3['target']),
            'operation': 'getTracks'
        }
        self.APIV3getTracksById = {
            'path':   'cirrus/v3/',
            'target': '{}getTracksById'.format(self.APIcirrusV3['target']),
            'operation': 'getTracksById'
        }
        # default
        self.APIbase = 'com.amazon.musicplaylist.model.MusicPlaylistService.'
        self.APIgetPlaylistsByIdV2 = {
            'path':   'playlists/',
            'target': '{}getPlaylistsByIdV2'.format(self.APIbase)
        }
        self.APIgetPubliclyAvailablePlaylistsById = {
            'path':   'playlists/',
            'target': '{}getPubliclyAvailablePlaylistsById'.format(self.APIbase)
        }
        self.APIsociallySharePlaylist = {
            'path':   'playlists/',
            'target': '{}sociallySharePlaylist'.format(self.APIbase)
        }
        self.APIgetConfigurationV2 = {
            'path':   'playlists/',
            'target': '{}getConfigurationV2'.format(self.APIbase)
        }
        self.APIgetFollowedPlaylistsInLibrary = {
            'path':   'playlists/',
            'target': '{}getFollowedPlaylistsInLibrary'.format(self.APIbase)
        }
        self.APIgetOwnedPlaylistsInLibrary = {
            'path':   'playlists/',
            'target': '{}getOwnedPlaylistsInLibrary'.format(self.APIbase)
        }
        self.APIbase = 'com.amazon.nimblymusicservice.NimblyMusicService.'
        self.APIGetRecentTrackActivity = {
            'path':   'nimbly/',
            'target': '{}GetRecentTrackActivity'.format(self.APIbase)
        }
        self.APIGetRecentActivity = {
            'path':   'nimbly/',
            'target': '{}GetRecentActivity'.format(self.APIbase)
        }
        # soccer live
        self.APIbase = 'com.amazon.eventvendingservice.EventVendingService.getProgramDetails'
        self.APIGetSoccerMain = {
            'path':   'eve/getPrograms',
            'target': self.APIbase
        }
        self.APIGetSoccerProgramDetails = {
            'path':   'eve/getProgramDetails',
            'target': self.APIbase
        }
        self.APIGetSoccerLiveURLs = {
            'path':   'amals/getLiveStreamingUrls',
            'target': 'com.amazon.amazonmusicaudiolocatorservice.model.AmazonMusicAudioLocatorServiceExternal.GetLiveStreamingURLs'
        }
        self.APIGetSoccerOnDemandURLs = {
            'path':   'amals/getOnDemandStreamingURLs',
            'target': 'com.amazon.amazonmusicaudiolocatorservice.model.AmazonMusicAudioLocatorServiceExternal.GetOnDemandStreamingURLs'
        }
        # podcasts
        # api/podcast
        # https://music-uk-dub.dub.proxy.amazon.com/EU/api/podcast/ " + t + "/visual"
        # https://music.amazon.com/" + e + "/api/podcast/" + t + "/visual"
        self.APIGetPodcast = {
            'path':   'podcast',
            'target': 'Podcast.Web.WidgetsInterface.LibraryShowsWidgetElement'
        }
        # "/podcasts/" + e.podcastId + "/" + encodeURI(e.podcastTitle),
        # "/podcasts/" + e.podcastId + "/episodes/" + e.episodeId + "/" + a,
        # "/podcasts/" + e.podcastId + "/" + encodeURI(e.podcastTitle),
        # preset: '{"podcastId":"' + e.podcastId + '","startAtEpisodeId":"' + e.episodeId + '"}',
        # e.PODCAST_LIBRARY_RECENTS_WIDGET = "Podcast.Web.WidgetsInterface.BookmarkedEpisodesWidgetElement",
        # e.PODCAST_LIBRARY_PLAYLIST_WIDGET = "Podcast.Web.WidgetsInterface.LibraryPlaylistWidgetElement",
        # e.PODCAST_LIBRARY_SHOWS_WIDGET = "Podcast.Web.WidgetsInterface.LibraryShowsWidgetElement"
    ############ Start of Request dispatch #######################
    def reqDispatch(self):
        # reset addon
        if self.addonMode is not None and self.addonMode[0] == 'resetAddon':
            self.resetAddon()
            xbmc.executebuiltin('Notification("Information:", {}, 5000, )'.format(self.translation(30071)))
            return
        # if self.logging: self.log('Access: {}'.format(self.access))
        # if not self.isCookie:
        #     if not self.AMl.amazonLogon():
        #         xbmc.executebuiltin('Notification("Error:", {}, 5000, )'.format(self.translation(30070)))
        #         return
        #     else:
        #         self.cj.load(self.cookieFile)

        # define addon mode
        if self.addonMode is None:
            mode = None
        else:
            mode = self.addonMode[0]
        # build menus
        if mode is None:
            self.createList(self.menuHome())
            return
        elif mode in ['menuPlaylists','menuAlbums','menuSongs','menuStations','menuArtists']:
            exec('self.createList(self.{}(),True)'.format(mode))
            return
        elif mode == 'menuSoccer':
            self.createList(self.menuSoccer())
            return

        # if not self.access:
        #     if not self.AMl.amazonLogon():
        #        xbmc.executebuiltin('Notification("Error:", {}, 5000, )'.format(self.translation(30070)))
        #        return

        if mode == 'searchPlayLists':
            self.searchItems(['playlists','catalog_playlist'],30013)
        elif mode in ['search1PlayLists','search2PlayLists','search3PlayLists']:
            exec('self.searchItems([\'playlists\',\'catalog_playlist\'],None,self.getSetting("{}"))'.format(mode))

        # test start
        elif mode == 'getPodcasts':
            self.getPodcasts()
        # test end

        elif mode == 'searchAlbums':
            self.searchItems(['albums','catalog_album'],30010)
        elif mode in ['search1Albums','search2Albums','search3Albums']:
            exec('self.searchItems([\'albums\',\'catalog_album\'],None,self.getSetting("{}"))'.format(mode))

        elif mode == 'searchSongs':
            self.searchItems(['tracks','catalog_track'],30011)
        elif mode in ['search1Songs','search2Songs','search3Songs']:
            exec('self.searchItems([\'tracks\',\'catalog_track\'],None,self.getSetting("{}"))'.format(mode))

        elif mode == 'searchArtist':
            self.searchItems(['artists','catalog_artist'],30014)
        elif mode in ['search1Artists','search2Artists','search3Artists']:
            exec('self.searchItems([\'artists\',\'catalog_artist\'],None,self.getSetting("{}"))'.format(mode))

        elif mode == 'searchStations':
            self.searchItems(['stations','catalog_station'],30016)
        elif mode in ['search1Stations','search2Stations','search3Stations']:
            exec('self.searchItems([\'stations\',\'catalog_station\'],None,self.getSetting("{}"))'.format(mode))

        elif mode == 'getArtistDetails':
            asin = self.addonArgs.get('asin', [None])
            self.getArtistDetails(asin[0])

        elif mode == 'getRecentlyPlayed':
            #self.getRecentlyPlayed('PLAYED')
            items = self.amzCall(self.APIGetRecentTrackActivity,'recentlyplayed',None,None,'PLAYED')['recentActivityMap']['PLAYED']
            self.setAddonContent('recentlyplayed',items,'songs')
        elif mode == 'getRecentlyAddedSongs':
            #self.getRecentlyAddedSongs()
            items = self.amzCall(self.APIcirrus,'recentlyaddedsongs',None,None,None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
            self.setAddonContent('recentlyaddedsongs',items,'songs')
        elif mode == 'getPopularPlayLists':
            self.getPlayLists('popularity-rank')
        elif mode == 'getNewPlayLists':
            self.getPlayLists('newly-released')
        elif mode == 'getFollowedPlayLists':
            #self.getFollowedPlayLists()
            items = self.amzCall(self.APIgetFollowedPlaylistsInLibrary,'followedplaylists',None,None,None)
            self.setAddonContent('followedplaylists',items,'albums')
        elif mode == 'getOwnedPlaylists':
            #self.getOwnedPlaylists()
            items = self.amzCall(self.APIgetOwnedPlaylistsInLibrary,'getownedplaylists',None,None,None)
            self.setAddonContent('ownedplaylists',items,'albums')
        elif mode == 'getPlaylistsByIdV2':
            asin = self.addonArgs.get('asin', [None])
            #self.getPlaylistsByIdV2(asin[0])
            items = self.amzCall(self.APIgetPlaylistsByIdV2,'getplaylistsbyid',None,asin[0],None)
            self.setAddonContent('getplaylistsbyid',items,'songs')

        elif mode == 'getRecomPlayLists':
            self.getRecommendations('mp3-prime-browse-carousels_playlistStrategy')
        elif mode == 'getRecomAlbums':
            self.getRecommendations('mp3-prime-browse-carousels_mp3PrimeAlbumsStrategy')
        elif mode == 'getRecomStations':
            self.getRecommendations('mp3-prime-browse-carousels_mp3ArtistStationStrategy')

        elif mode == 'getNewRecom':
            self.getNewRecommendations()
        elif mode == 'getNewRecomDetails':
            asin = self.addonArgs.get('target', [None])
            self.getNewRecomDetails(asin[0])
        # get own music, differentiate betwenn purchased and own lib
        # param: searchReturnType , caller, sortCriteriaList.member.1.sortColumn
        elif mode in ['getPurAlbums','getAllAlbums']:
            self.getPurchased(['ALBUMS','getAllDataByMetaType','sortAlbumName'],'albums')
        elif mode in ['getAllSongs','getPurSongs']:
            self.getPurchased(['TRACKS','getServerSongs','sortTitle'],'songs')
        # get amazon stations
        elif mode in ['getStations','getAllArtistsStations','getGenres','getGenres2']:
            #self.getStations(mode.replace('get','').lower())
            items = self.amzCall(self.APIgetStationSections,'getStations','/stations')
            self.setAddonContent(mode.replace('get','').lower(),items,'albums')
        elif mode in ['getGenrePlaylist','createQueue']:
            asin = self.addonArgs.get('asin', None)
            exec('self.{}(asin[0])'.format(mode))
        # get song lists
        elif mode == 'lookup':
            asin = self.addonArgs.get('asin', None)
            self.lookup(asin)
        # play the song
        elif mode == 'getTrack':
            asin = self.addonArgs.get('asin', [None])[0]
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getTrack(asin,objectId)
        # Amazon Soccer Live
        elif mode in ['soccerBUND','soccerBUND2','soccerCHAMP','soccerDFBPOKAL','soccerSUPR']:
            self.getSoccerFilter(mode.replace('soccer',''))
        elif mode == 'getSoccerLive':
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'LIVE')
        elif mode == 'getSoccerOnDemand':
            objectId = self.addonArgs.get('objectId', [None])[0]
            self.getSoccer(objectId,'ONDEMAND')
    def createList(self,data,dynentry=False,soccer=False):
        itemlist = []
        url = None
        for item in data:
            # self.log(item)
            isFolder = True
            if dynentry and 'search' in item and self.getSetting(item['search']) == '':
                continue
            # if soccer:
            if soccer or ('special' in item and item['special'] == 'newrecom'):
                title = item['txt']
            else:
                title = self.translation(item['txt'])
            if dynentry and 'search' in item:
                title += self.getSetting(item['search'])
            li = xbmcgui.ListItem(label=title)
            li.setInfo(type="music", infoLabels={"title": title})
            if 'img' in item:
                if 'http' in item['img']:
                    url = item['img']
                else:
                    url = '{}/resources/images/{}'.format(self.addonFolder, self.getSetting(item['img']) )
                li.setArt({'icon':url,'thumb':url,'fanart':url,'poster':url,'banner':url,'landscape':url})
            url = '{}?mode={}'.format(self.addonBaseUrl,str(item['fct']))
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
        data = self.amzCall( self.APIlookup,'itemLookup',None,asin,mediatype)
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
            data = self.amzCall(self.APIcirrus, 'itemLookup2ndRound', '/my/albums', [asin], None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
            sel = 'trackInfoList'
        self.setAddonContent(sel,data[sel],'songs')
    # def getRecentlyPlayed(self,mediatype):
    #     items = self.amzCall(self.APIGetRecentTrackActivity,'recentlyplayed',None,None,mediatype)['recentActivityMap']['PLAYED']
    #     self.setAddonContent('recentlyplayed',items,'songs')
    # def getRecentlyAddedSongs(self):
    #     items = self.amzCall(self.APIcirrus,'recentlyaddedsongs',None,None,None)['selectTrackMetadataResponse']['selectTrackMetadataResult']
    #     self.setAddonContent('recentlyaddedsongs',items,'songs')
    def getPlayLists(self,mediatype):
        items = self.amzCall(self.APIgetTopMusicEntities,'playlist',None,None,mediatype)
        # data structure is similar to lookup
        self.setAddonContent('playlists',items,'albums')
    # def getFollowedPlayLists(self):
    #     items = self.amzCall(self.APIgetFollowedPlaylistsInLibrary,'followedplaylists',None,None,None)
    #     self.setAddonContent('followedplaylists',items,'albums')
    # def getOwnedPlaylists(self):
    #     items = self.amzCall(self.APIgetOwnedPlaylistsInLibrary,'getownedplaylists',None,None,None)
    #     self.setAddonContent('ownedplaylists',items,'albums')
    # def getPlaylistsByIdV2(self,asin):
    #     items = self.amzCall(self.APIgetPlaylistsByIdV2,'getplaylistsbyid',None,asin,None)
    #     self.setAddonContent('getplaylistsbyid',items,'songs')
    # def getStations(self,mediatype):
    #     items = self.amzCall(self.APIgetStationSections,'getStations','/stations')
    #     self.setAddonContent(mediatype,items,'albums')
    def getGenrePlaylist(self,asin):
        items = self.amzCall(self.APIcreateQueue,'getGenrePlaylist',None,asin)
        self.setAddonContent('genreplaylist',items,'albums')
    def getRecommendations(self,mediatype):
        resp = self.amzCall(self.APIgetBrowseRecommendations,'recommendations',None,None,mediatype)
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
        resp = self.amzCall(self.APIgetHome,'new_recommendations')
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
        items = None
        resp = self.amzCall(self.APIgetHome,'new_recommendations')
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
        resp = self.amzCall(self.APIcirrus,'getPurchased',None,None,mode)
        items = resp['searchLibraryResponse']['searchLibraryResult']
        if ctype == 'songs':
            mode = 'purchasedsongs'
        elif ctype == 'albums':
            mode = 'purchasedalbums'
        self.setAddonContent(mode,items,ctype)
    def searchItems(self,mode=None,txt=None,query=None):
        if query == None:
            if self.addonArgs.get('token', False):
                query = self.addonArgs.get('query', [''])[0]
            else:
                query = self.getUserInput(self.translation(txt), '')
                if not query:
                    return
        resp = self.amzCall( self.APIsearch , 'searchItems' , '/search' , query,mode )
        items = resp['results'][0]
        if   mode[0] == 'albums':
            if not txt == None:
                self.setSearch('albums',query)
            self.setAddonContent('searchitems',items,'albums','albums',query)
        elif mode[0] == 'tracks':
            if not txt == None:
                self.setSearch('tracks',query)
            self.setAddonContent('searchitems',items,'songs','tracks',query)
        elif mode[0] == 'playlists':
            if not txt == None:
                self.setSearch('playlists',query)
            self.setAddonContent('searchplaylists',items,'albums',None,query)
        elif mode[0] == 'artists':
            if not txt == None:
                self.setSearch('artists',query)
            self.setAddonContent('searchartists',items,'songs',None,query)
        elif mode[0] == 'stations':
            if not txt == None:
                self.setSearch('stations',query)
            self.setAddonContent('searchstations',items,'albums',None,query)
    def getArtistDetails(self,asin):
        resp = self.amzCall(self.APIartistDetailsMetadata,'getArtistDetails',None,asin,None)
        items = resp
        self.setAddonContent('artistdetails',items,'albums',None,asin)
    def createQueue(self,asin):
        resp = self.amzCall(self.APIcreateQueue,'createQueue',None,asin,None)
        token = resp['queue']['pageToken']
        tracklist = resp['trackMetadataList']
        i = 1
        while token: # 5 songs per loop
            resp = self.amzCall(self.APIQueueGetNextTracks,'getNextTracks',None,asin,token)
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
        return self.amzCall(self.APIlookup,'itemLookup',None,uniq,['fullAlbumDetails'])#['albumList']
    def getMetaTracks(self,filter):
        return self.amzCall(self.APIV3getTracks,'getMetaTracks',None,filter,None)
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

        if 'discNum' in item:           info['discnumber'] = item['discNum']

        if 'duration' in item:
            info['duration'] = item['duration']
        elif 'durationSeconds' in item:
            info['duration'] = item['durationSeconds']

        if 'albumReleaseDate' in item:  info['year'] = item['albumReleaseDate'][:4]

        if 'primaryGenre' in item:
            info['genre'] = item['primaryGenre']
        elif 'genreName' in item:
            info['genre'] = item['genreName']
        elif 'productDetails' in item:
            info['genre'] = item['productDetails']['primaryGenreName']

        if 'albumName' in item:             info['album'] = item['albumName']
        if 'description' in item:           info['album'] = item['description']
        if 'stationTitle' in item:          info['album'] = item['stationTitle']
        if 'album' in item:
            try:
                info['album'] = item['album']['name']
            except:
                info['album'] = item['album']['title']

        if 'albumArtistName' in item:       info['artist'] = item['albumArtistName']
        if 'artist' in item:                info['artist'] = item['artist']['name']
        if 'artistName' in item:            info['artist'] = item['artistName']

        if 'stationTitle' in item:          info['title'] = item['stationTitle']
        if 'displayName' in item:           info['title'] = item['displayName']

        if 'isAlbum' in filter and filter['isAlbum']:
            if info['title'] == None and 'albumName' in item:
                info['title'] = item['albumName']
        else:
            if 'title' in item:
                info['title'] = item['title']
            if info['title'] == None and 'name' in item:
                info['title'] = item['name']

        if 'reviews' in item:               info['rating'] = item['reviews']['average']
        if 'rating' in item:                info['rating'] = item['rating']
        if 'averageOverallRating' in item:  info['rating'] = item['averageOverallRating']

        # mode : asin : objectId : thumb : purchased : isPrime : isUnlimited
        # order of 'playlistId' and 'asin' is important. Do not change the order -> reason: followed playlists
        if 'playlistId' in item:            meta['asin'] = item['playlistId']
        if 'asin' in item:                  meta['asin'] = item['asin']
        if 'seedId' in item:                meta['asin'] = item['seedId']
        if 'categoryId' in item:            meta['asin'] = item['categoryId']
        if 'stationKey' in item:            meta['asin'] = item['stationKey']
        if 'identifier' in item:            meta['asin'] = item['identifier']
        if 'isAlbum' in filter and filter['isAlbum']:
            if 'albumAsin' in item:
                meta['asin'] = item['albumAsin']

        if 'trackId' in item:               meta['objectId'] = item['trackId']
        if 'objectId' in item:              meta['objectId'] = item['objectId']
        if 'stationSeedId' in item:         meta['objectId'] = item['stationSeedId']

        # images - 'icon','thumb','fanart','poster','banner','landscape'
        if 'image' in item:                 meta['thumb'] = item['image']
        if 'imageFull' in item:             meta['thumb'] = item['imageFull']
        if 'albumCoverImageFull' in item:   meta['thumb'] = item['albumCoverImageFull']
        if 'albumArtImageUrl' in item:      meta['thumb'] = item['albumArtImageUrl']
        if 'stationImageUrl' in item and item['stationImageUrl'] is not None:
            meta['thumb'] = item['stationImageUrl']
        if 'foregroundImageUrl' in item and item['foregroundImageUrl'] is not None:
            meta['thumb'] = item['foregroundImageUrl']
        if 'artOriginal' in item:           meta['thumb'] = item['artOriginal']['URL']
        if 'artFull' in item:               meta['thumb'] = item['artFull']['URL']
        if 'artUrlMap' in item:             meta['thumb'] = item['artUrlMap']['FULL']
        if 'fourSquareImage' in item:       meta['thumb'] = item['fourSquareImage']['url']
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

        if self.showcolentr:
            if meta['purchased']:
                meta['color'] = '[COLOR gold]%s[/COLOR]'
            elif meta['isPrime'] or 'stationMapIds' in item:
                meta['color'] = '%s'
            elif meta['isUnlimited']:
                meta['color'] = '[COLOR blue]%s[/COLOR]'
            else:
                meta['color'] = '[COLOR red]%s[/COLOR]'

        if ((self.accessType == 'PRIME'     and not meta['isPrime'] and not meta['purchased']) or
            (self.accessType == 'UNLIMITED' and not meta['isPrime'] and not meta['purchased'] and not meta['isUnlimited'] )):
            meta['isPlayable'] = False
        else:
            meta['isPlayable'] = True

        if (self.accessType == 'UNLIMITED' and meta['isUnlimited']):
            meta['isPlayable'] = True
        
        #self.log('vor: ' + str(info['tracknumber']))
        if 'isList' in filter and filter['isList'] and info['tracknumber'] is not None:
            info['title'] =  '{}  ({} Hits'.format(info['title'],info['tracknumber'])
            if info['duration'] is not None:
                info['title'] =  '{} - {}'.format(info['title'],datetime.timedelta(seconds=info['duration']))
            info['title'] =  '{})'.format(info['title'])
            info['tracknumber'] = None
        #self.log('nach: ' + str(info['tracknumber']))
        #self.log(info)
        #self.log(meta)
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
        # self.log(url)
        # self.log(inf)
        # self.log(met)
        return (url,li)
    def setListItem(self,itemList,item,param):
        inf, met = self.setData(item,param)
        url, li  = self.setItem(inf,met)
        itemList.append((url, li, True))
        return itemList
    def setImage(self,img):
        if self.showimages:
            return ({'icon':img,'thumb':img,'fanart':img,'poster':img,'banner':img,'landscape':img})
        else:
            return ({'thumb':img}) # there is a bug in the listitems, after setting multiple arts, setInfo shows the Genre only
    def addPaginator(self,itemList,resultToken,resultLen):
        if not resultToken == None and not len(resultLen) < self.maxResults: # next page
            itemList.append(self.setPaginator(resultToken))
        return itemList
    def setPaginator(self,nextToken,query=None,asin=None):
        li = xbmcgui.ListItem(label=self.translation(30020))
        li.setProperty('IsPlayable', 'false')
        url = "{}?mode={}&token={}".format(self.addonBaseUrl,str(self.addonMode[0]),str(nextToken))
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
        return '{}?{}'.format(self.addonBaseUrl,urlencode(url))
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
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'artistList':      # no content at the moment
            self.log('artistList')
        elif mode == 'trackInfoList':           # track info list
            for item in param:
                meta.append(item['metadata']['asin'])
            meta = self.amzCall(self.APIlookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
        elif mode == 'stationList':             # station playlist
            for item in param:
                meta.append(item['identifier'])
            meta = self.amzCall(self.APIlookup,'itemLookup',None,meta,mediatype)['trackList']
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
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, True))
        elif mode == 'getplaylistsbyid':        # playlists by Id
            for item in param['playlists']:
                for track in item['tracks']:
                    meta.append(track['metadata']['requestedMetadata']['asin'])
            meta = self.amzCall(self.APIlookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param['playlists']:
                for track in item['tracks']:
                    inf, met = self.setData(track['metadata']['requestedMetadata'],{'mode':'getTrack'})
                    for i in meta:
                        if track['metadata']['requestedMetadata']['asin'] == i['asin']:
                            inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                        else:
                            continue
                    url, li  = self.setItem(inf,met)
                    if not self.showUnplayableSongs and not met['isPlayable']:
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
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextToken'],param['recentTrackList'])
        elif mode == 'newrecom':                # new recommendations
            for item in param:
                i = item['hint']['__type']
                #self.log(i)
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
                if not self.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
        elif mode == 'recentlyaddedsongs':      # recently added songs
            for item in param['trackInfoList']:
                meta.append(item['metadata']['asin'])
            meta = self.amzCall(self.APIlookup,'itemLookup',None,meta,mediatype)['trackList']
            for item in param['trackInfoList']:
                inf, met = self.setData(item['metadata'],{'mode':'getTrack'})
                for i in meta:
                    if item['metadata']['asin'] == i['asin']:
                        inf, met = self.setData(i,{'info':inf,'meta':met,'update':True})
                    else:
                        continue
                url, li  = self.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextResultsToken'],param['trackInfoList'])
        elif mode == 'stations':                # (all) stations
            items = param['categories'].get('allStations')['stationMapIds']
            for item in items:
                self.setListItem(itemlist,param['stations'].get(item),{'mode':'createQueue'})
        elif mode == 'allartistsstations':      # (all artists) stations
            items = param['stations']
            for item in items:
                i = param['stations'].get(item)
                if not i['seedType'] == 'ARTIST':
                    continue
                self.setListItem(itemlist,i,{'mode':'createQueue'})
        elif mode == 'genres':                  # genre 1st level
            for sec in param['sections']:
                if sec['sectionId'] == 'genres':
                    for item in sec['categoryMapIds']:
                        self.setListItem(itemlist,param['categories'].get(item),{'mode':'getGenres2','isStation':True})
                else:
                    continue
        elif mode == 'genres2':                 # genres 2nd level
            asin = self.addonArgs.get('asin', None)[0]
            items = param['categories'].get(asin)['stationMapIds']
            for item in items:
                self.setListItem(itemlist,param['stations'].get(item),{'mode':'createQueue'})
        elif mode == 'purchasedalbums':         # purchased and owned albums
            for item in param['searchReturnItemList']:
                meta.append(item['metadata']['asin'])
            meta = self.amzCall(self.APIlookup,'itemLookup',None,meta,['fullAlbumDetails'])['albumList']
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
                if not self.showUnplayableSongs and not met['isPlayable']:
                    continue
                itemlist.append((url, li, False))
            self.addPaginator(itemlist,param['nextResultsToken'],param['searchReturnItemList'])
        elif mode == 'searchitems':             # search items (songs / albums)
            for item in param['hits']:
                if stype == 'albums':
                    mod  = {'mode':'lookup','isList':True}
                    fold = True
                elif stype == 'tracks' or stype == 'artists':
                    mod  = {'mode':'getTrack'}
                    fold = False
                inf, met = self.setData(item['document'],mod)
                url, li  = self.setItem(inf,met)
                if not self.showUnplayableSongs and not met['isPlayable'] and mod['mode'] == 'getTrack':
                    continue
                itemlist.append((url, li, fold))
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchplaylists':         # search playlists
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'lookup','isList':True})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchartists':           # search artists
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'getArtistDetails'})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'searchstations':          # search stations
            for item in param['hits']:
                self.setListItem(itemlist,item['document'],{'mode':'createQueue','query':query})
            try:
                if not param['nextPage'] == None and len(param['hits']) <= self.maxResults: # next page
                    itemlist.append(self.setPaginator(param['nextPage'],query))
            except:
                pass
        elif mode == 'artistdetails':           # artitist details (albums)
            for item in param['albumList']:
                self.setListItem(itemlist,item,{'mode':'lookup'})
            try:
                if len(param['albumList']) == self.maxResults:
                    itemlist.append(self.setPaginator(param['nextTokenMap']['album'],None,query))
                    #itemlist.append((url, li, True))
            except:
                pass
        self.finalizeContent(itemlist,ctype)
        xbmc.sleep(100)
    def finalizeContent(self,itemlist,ctype):
        xbmcplugin.addDirectoryItems(self.addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(self.addonHandle, ctype)
        xbmcplugin.endOfDirectory(self.addonHandle)
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
                song = 'http://{}/mpd/{}'.format(self.getSetting('proxy'),'song.mpd')
                stream['ia']  = True
                stream['lic'] = True
        if song == None:
            xbmc.PlayList(0).clear()
            xbmc.Player().stop()
            xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.translation(30073),' ',self.translation(30074)))
            return False
        self.finalizeItem(song,stream['ia'],stream['lic'])        
    def tryGetStream(self,asin,objectId):
        if objectId == None:
            resp = self.amzCall(self.APIstream,'getTrack',None,asin,'ASIN')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['statusCode'] == 'MAX_CONCURRENCY_REACHED':
                xbmc.PlayList(0).clear()
                xbmc.Player().stop()
                xbmc.executebuiltin('Notification("Information:", %s %s %s, 10000, )'%(self.translation(30073),' ',self.translation(30075)))
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        else:
            resp = self.amzCall(self.APIstream,'getTrack',None,objectId,'COID')
            obj = json.loads(resp.text)
            if 'statusCode' in obj and obj['contentResponse']['statusCode'] == 'CONTENT_NOT_ELIGIBLE' or obj['contentResponse']['statusCode'] == 'BAD_REQUEST':
                return None
            try:
                song = obj['contentResponse']['urlList'][0]
            except:
                return None
        return song
    def tryGetStreamHLS(self,asin,objectId):
        resp = self.amzCall(self.APIstreamHLS,'getTrackHLS',None,asin,'ASIN')
        return re.compile('manifest":"(.+?)"',re.DOTALL).findall(resp.text)
    def tryGetStreamDash(self,asin,objectId):
        resp = self.amzCall(self.APIstreamDash,'getTrackDash',None,asin,'ASIN')
        return json.loads(resp.text)['contentResponseList'][0]['manifest']
    # resp = self.amzCall(self.APIgetStreamingURLsWithFirstChunkV2,'getTrackDashV2',None,asin,'ASIN')
    def finalizeItem(self,song,ia=False,lic=False):
        li = xbmcgui.ListItem(path=song)
        if ia:
            li.setMimeType('application/xml+dash')
            li.setProperty('inputstream', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.adaptive.stream_headers', 'user-agent={}'.format(self.userAgent))
            # for live soccer only - test start
            li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            # for live soccer only - test end
            if lic:
                li.setProperty('inputstream.adaptive.license_key', self.getLicenseKey() )
            li.setProperty('isFolder', 'false')
            li.setProperty('IsPlayable', 'true')
            li.setInfo('video', {})
        li.setInfo('audio', {'codec': 'aac'})
        li.addStreamInfo('audio', {'codec': 'aac'})
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(self.addonHandle, True, listitem=li)
    def writeSongFile(self,manifest,ftype='m3u8'):
        song = '{}{}song.{}'.format(self.addonUDatFo,os.sep,ftype)
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
        amzUrl = self.APILicenseForPlaybackV2
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
    def getSoccerFilter(self,target=None): # 'BUND', 'BUND2', 'CHAMP', 'DFBPOKAL', 'SUPR'
        menuEntries = []
        resp = self.amzCall(self.APIGetSoccerMain,'getSoccerMain',None,None,target)
        idx = resp['blocks'][0]['positionSelector']['currentPosition']['blockIndex'] # current matchday
        if idx == -1: # if no entries are available
            menuEntries.append({'txt':'Empty List','fct':None,'target':None,'img':self.getSetting('img_soccer'),'playable':False})
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
            amz = { 'path': self.APIGetSoccerLiveURLs,
                    'target': 'getSoccerLiveURL' }
        elif status == 'ONDEMAND':
            amz = { 'path': self.APIGetSoccerOnDemandURLs,
                    'target': 'getSoccerOnDemandURL' }
        else:
            return False
        resp = self.amzCall(self.APIGetSoccerProgramDetails,'getSoccerProgramDetails',None,None,target)
        try:
            target = resp['program']['mediaContentList'][0]['mediaContentId']
        except:
            return False
        # target for xml source
        resp = self.amzCall(amz['path'],amz['target'],'soccer',None,target)
        target = resp['Output']['contentResponseList'][0]['urlList'][0] # link to mpd file
        r = requests.get(target)
        song = self.writeSongFile(r.content.decode('utf-8'),'mpd')

        ''' proxy try - START '''
        song = 'http://{}/mpd/{}'.format(self.getSetting('proxy'),'song.mpd')
        ''' proxy try - END '''
        self.finalizeItem(song,True)
    def getPodcasts(self):
        resp = self.amzCall(self.APIGetPodcast,'getPodcasts',None,None,None)

if __name__ == '__main__':
    AmazonMedia().reqDispatch()
