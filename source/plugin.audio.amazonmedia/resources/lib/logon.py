#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import os, re, base64, requests, json
from random import randint

from resources.lib.singleton import Singleton
from resources.lib.tools import AMtools

import xbmc
import xbmcgui
import mechanize

class AMlogon(Singleton):
    def __init__(self):
        self._t = AMtools()
        self.content    = ''
        self.btn_cancel = False
        self.captcha    = ''
        self.userEmail      = self._t.getSetting("userEmail")
        self.userPassword   = base64.urlsafe_b64decode(self._t.getSetting("userPassword"))

    def appConfig(self,app_config):
        if app_config is None:
            return False
        data = {
            'deviceId':         app_config['deviceId'],
            'csrf_token':       app_config['CSRFTokenConfig']['csrf_token'],
            'csrf_ts':          app_config['CSRFTokenConfig']['csrf_ts'],
            'csrf_rnd':         app_config['CSRFTokenConfig']['csrf_rnd'],
            'customerId':       app_config['customerId'],
            'marketplaceId':    app_config['marketplaceId'],
            'deviceType':       app_config['deviceType'],
            'musicTerritory':   app_config['musicTerritory'],
            'locale':           app_config['i18n']['locale'],
            'customerLang':     app_config['customerLanguage'],
            'region':           app_config['realm'][:2],
            'url':              'https://{}'.format(app_config['serverInfo']['returnUrlServer']),
            'siteVersion':      self.checkSiteVersion(app_config['musicTerritory'].lower())
        }
        if app_config['customerBenefits']['tier'] == 'UNLIMITED_HD':
            data['accessType'] = 'UNLIMITED'
        else:
            data['accessType'] =  app_config['customerBenefits']['tier']

    def appConfig2(self,app_config):
        if app_config is None:
            return False
        data = {
            'deviceId':         app_config['deviceId'],
            'csrf_token':       app_config['csrf']['token'],
            'csrf_ts':          app_config['csrf']['ts'],
            'csrf_rnd':         app_config['csrf']['rnd'],
            'customerId':       app_config['customerId'],
            'marketplaceId':    app_config['marketplaceId'],
            'deviceType':       app_config['deviceType'],
            'musicTerritory':   app_config['musicTerritory'],
            'locale':           app_config['displayLanguage'],
            'customerLang':     app_config['musicTerritory'].lower(),
            'region':           app_config['siteRegion'],
            'url':              self._t.musicURL,
            'siteVersion':      self.checkSiteVersion(app_config['musicTerritory'].lower())
        }
        if app_config['tier'] == 'UNLIMITED_HD':
            data['accessType'] = 'UNLIMITED'
        else:
            data['accessType'] =  app_config['tier']

        for key, value in data.items():
            self._t.setSetting(key, value)

    def checkSiteVersion(self,siteVersion):
        if siteVersion in self._t.siteVerList:
            x = 0
            for i in self._t.siteVerList:
                if siteVersion == i:
                    return str(x)
                else:
                    x+=1
        else:
            return "0"

    def parseHTML(self,resp):
        if self._t.logging: self._t.log()
        resp = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', resp)
        return BeautifulSoup(resp, 'html.parser')

    def getCredentials(self):
        if self._t.logging: self._t.log()
        if not self.userEmail or not self.userPassword:
            if not self.userEmail:
                user = self._t.getUserInput(self._t.getTranslation(30030),'', hidden=False, uni=False) # get Email
                if user:
                    self.userEmail = user
                    if self._t.getSetting('saveUsername'):
                        self._t.setSetting('userEmail', user)
            else:
                user = True
            if user and not self.userPassword:
                pw = self._t.getUserInput(self._t.getTranslation(30031),'', hidden=True, uni=False) # get Password
                if pw:
                    self.userPassword = pw
                    if self._t.getSetting('savePassword') and self._t.getSetting('saveUsername'):
                        self._t.setSetting('userPassword', base64.urlsafe_b64encode(pw.encode("utf-8")))
                    return True
                else:
                    return False
            else:
                return False
        return True

    def prepBrowser(self):
        if self._t.logging: self._t.log()
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_gzip(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_equiv(True)
        self.br.set_cookiejar(self._t.cj)
        self.br.addheaders = [
            ('Accept',          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Encoding', 'deflate,br'),
            ('Accept-Language', '{},en-US;q=0.7,en;q=0.3'.format(self._t.siteVerList[int(self._t.getSetting('siteVersion'))])),
            ('Cache-Control',   'no-cache'),
            ('Connection',      'keep-alive'),
            ('Content-Type',    'application/x-www-form-urlencoded'),
            ('User-Agent',      self._t.getSetting('userAgent')),
            ('csrf-token',      self._t.getSetting('csrf_token')),
            ('csrf-rnd',        self._t.getSetting('csrf_rnd')),
            ('csrf-ts',         self._t.getSetting('csrf_ts')),
            ('Upgrade-Insecure-Requests', '1')
        ]

    def amazonLogon(self):
        if self._t.logging: self._t.log()
        access = False
        self.prepBrowser()

        x = 1
        ret = False
        while not access:
            if x == 3:
                break
            if self._t.logging: self._t.log('loop: ' + str(x) + ' | access: ' + str(access))
            x+=1
            self.br.open(self._t.logonURL)
            # self.br.open('https://music.amazon.de')
            # self.br.open('https://www.amazon.de/gp/aw/si.html')
            # self._t.log(self.br.response().info())
            # self._t.log( str(self.br.response().read(), encoding = 'utf-8') )

            if not self.doLogonForm(): break
            if not self.checkMFA(): break
            if self.checkConfig():
                ret = True
                if self._t.logging: self._t.log('checkConfig - true')
                access = True
                break
            else:
                if self._t.logging: self._t.log('checkConfig - false')
                continue
        return ret

    def doLogonForm(self):
        if self._t.logging: self._t.log()
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
        if self._t.logging: self._t.log()
        self.br.submit()
        resp = self.br.response()
        xbmc.sleep(randint(750,1500))
        self.content = str(resp.read(), encoding = 'utf-8')
        self._t.setCookie()

    def checkConfig(self):
        if self._t.logging: self._t.log()
        app_config = None
        head = self._t.prepReqHeader('')
        resp = requests.post(url=self._t.musicURL, headers=head, data=None, cookies=self._t.cj)
        # self._t.setCookie()

        #################
        # self._t.log(resp.text)
        #################
        configfound = False
        soup = self.parseHTML(resp.text)

        script_list = soup.find_all('script')
        for scripts in script_list:
            # self._t.log(scripts.contents)
            if 'appConfig' in scripts.contents[0]:
                if self._t.logging:     self._t.log('Config available')
                #######################
                # self._t.log(scripts.contents)
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
                # self._t.log(sc)
                if not 'tier' in sc:
                    break
                app_config = json.loads(sc)
                configfound = True
                break
            else:
                if self._t.logging:     self._t.log('No config available')
                continue
        if not configfound:
            return False
        # self._t.log(app_config)
        self.appConfig2(app_config['appConfig'])
        return True

    def checkMFA(self):
        if self._t.logging: self._t.log()
        while 'action="verify"' in self.content or 'id="auth-mfa-remember-device' in self.content:
            soup = self.parseHTML(self.content)
            if 'cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none' in self.content:
                self._t.log('MFA - account name')
                form = soup.find('form', class_="cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none")
                msgheading = form.find('label', class_="a-form-label").getText().strip()
                msgtxt = ""
                inp = self._t.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'dcq_question_subjective_1') == False:
                    return False
            elif 'name="claimspicker"' in self.content:
                self._t.log('MFA - SMS code step 1')
                form = soup.find_all('form', attrs={'name':'claimspicker'})
                msgheading = form[0].find('h1').renderContents().strip()
                msgtxt = form[0].findAll('div', class_='a-row')[1].renderContents().strip()
                if xbmcgui.Dialog().yesno(msgheading, msgtxt):
                    self.br.select_form(nr=0)
                    self.getLogonResponse()
                else:
                    return False
            elif 'name="code"' in self.content: # sms info
                self._t.log('MFA - SMS code step 2')
                form = soup.find_all('form', class_='cvf-widget-form fwcim-form a-spacing-none')
                msgheading = form[0].findAll(lambda tag: tag.name == 'span' and not tag.attrs)
                msgheading = msgheading[1].text + os.linesep + msgheading[2].text
                msgtxt = ''
                inp = self._t.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'code') == False:
                    return False
            elif 'auth-mfa-form' in self.content:
                msg = soup.find('form', id='auth-mfa-form')
                self._t.log('### MFA ###############')
                msgheading = msg.p.renderContents().strip()
                msgtxt = ''
                inp = self._t.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'otpCode','ActivateWindow(busydialog)') == False:
                    return False
            else: # Unknown form
                # captcha call here
                return False
        return True

    def checkMFAInput(self, inp, target, action=None):
        if self._t.logging: self._t.log()
        if inp:
            if action:
                xbmc.executebuiltin(action)
            self.br.select_form(nr=0)
            self.br[target] = inp
            self.getLogonResponse()
        else:
            return False

    def checkCaptcha(self):
        if self._t.logging: self._t.log()
        self._t.setSetting('captcha',"")
        self.br.select_form(action="/errors/validateCaptcha")
        self.content = str(self.br.response().read(), encoding = 'utf-8')
        soup = self.parseHTML(self.content)
        # self._t.log(soup)
        form = soup.find_all('form')
        msgheading = str(form[0].find('h4').renderContents().strip(), encoding = 'utf-8')
        img = form[0].find('img') #.renderContents().strip()
        # self._t.log(msgheading)
        # self._t.log(img['src'])
        self.btn_cancel = False
        self.showCaptcha('captcha.xml',img['src'],msgheading)
        self.captcha = self._t.getSetting('captcha')
        if self.captcha == "":
            return False
        self.br["field-keywords"] = self.captcha
        return True

    def showCaptcha(self,layout, imagefile, message):
        if self._t.logging: self._t.log()
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
                self._t.setSetting('captcha',self.inp)
                self.show_dialog()
            def onClick(self, controlid):
                # self._t.log(controlid)
                if controlid == self.btn_ok:
                    # self._t.log('btn_ok')
                    self.close()
                elif controlid == self.btn_cancel:
                    # self._t.log('btn_cancel')
                    self.captcha = ""
                    self.btn_cancel = True
                    self.close()
                elif controlid == self.btn_input:
                    # self._t.log('btn_input')
                    self._t.getUserInput('Captcha Entry')
        cp = Captcha(layout, self._t.addonFolder, 'Default', image=imagefile, text=message, settings=self.s)
        cp.doModal()
        del cp