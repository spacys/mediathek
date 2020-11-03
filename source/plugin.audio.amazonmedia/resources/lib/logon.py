#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from bs4 import BeautifulSoup
import re
import os
import base64
import xbmc
import xbmcgui
import json
import requests
import mechanize
#import pyxbmct
from .singleton import Singleton

class Logon(Singleton):
    def __init__(self,Settings):
        self.s = Settings
    def parseHTML(self,resp):
        resp = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', resp)
        return BeautifulSoup(resp, 'html.parser')
    def delCredentials(self):
        self.s.userEmail = ''
        self.s.userPassword = ''
    def getCredentials(self):
        if not self.s.userEmail or not self.s.userPassword:
            if not self.s.userEmail:
                user = self.getUserInput(self.s.translation(30030),'', hidden=False, uni=False) # get Email
                if user:
                    self.s.userEmail = user
                    if self.s.saveUsername:
                        self.s.setSetting('userEmail', user)
            else:
                user = True
            if user and not self.s.userPassword:
                pw = self.getUserInput(self.s.translation(30031),'', hidden=True, uni=False) # get Password
                if pw:
                    self.s.userPassword = pw
                    if self.s.savePassword and self.s.saveUsername:
                        self.s.setSetting('userPassword', base64.urlsafe_b64encode(pw.encode("utf-8")))
                    return True
                else:
                    return False
            else:
                return False
        return True
    def getUserInput(self,title,txt,hidden=False,uni=False):
        kb = xbmc.Keyboard()
        kb.setHeading(title)
        kb.setDefault(txt)
        kb.setHiddenInput(hidden)
        kb.doModal()
        if kb.isConfirmed() and kb.getText():
            if uni:
                return str(kb.getText(), encoding = 'utf-8')
            else:
                return kb.getText() # for password needed, due to encryption
        else:
            return False
    def prepBrowser(self):
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_gzip(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_equiv(True)
        self.br.set_cookiejar(self.s.cj)
        self.br.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
             ('Accept-Encoding', 'deflate,br'), #gzip,
             ('Accept-Language', '{},en-US;q=0.7,en;q=0.3'.format(self.s.siteVerList[int(self.s.siteVersion)])), #'de,en-US;q=0.7,en;q=0.3'),
             ('Cache-Control', 'no-cache'),
             ('Connection', 'keep-alive'),
             ('Content-Type', 'application/x-www-form-urlencoded'),
             ('User-Agent', self.s.userAgent),
             ('csrf-token', self.s.csrf_token),
             ('csrf-rnd',   self.s.csrf_rnd),
             ('csrf-ts',    self.s.csrf_ts),
             ('Upgrade-Insecure-Requests', '1')]
    def amazonLogon(self):
        app_config = None
        self.s.delCookies()
        self.doReInit()  ### --> TODO
        self.s.addonMode = None
        self.s.access = False
        x = 1
        while not self.s.access:
            if not self.getCredentials():
                return False
            self.br.open(self.s.logonURL)
            
            # self.s.log(self.br.response().code)
            # self.s.log(self.br.response().info())
            # self.s.log( str(self.br.response().read(), encoding = 'utf-8') )

            try: 
                self.doLogonForm()
            except:
                self.checkCaptcha()
                continue

            self.content = self.getLogonResponse()

            if 'message error' in self.content or x == 3:
                xbmcgui.Dialog().ok(self.s.addonName, 'Logon issue')
                return False
            if not self.checkMFA():
                return False

            self.s.setCookie()
            if not os.path.isfile(self.s.cookieFile):
                break

            self.s.cj.load(self.s.cookieFile)
            head = self.s.prepReqHeader('')
            resp = requests.post(self.s.musicURL, data=None, headers=head, cookies=self.s.cj)

            for line in resp.iter_lines(decode_unicode=True):
                if 'applicationContextConfiguration =' in line or 'amznMusic.appConfig =' in line:
                    app_config = json.loads(re.sub(r'^[^{]*', '', re.sub(r';$', '', line)))
                    break

            if app_config is None or app_config['isRecognizedCustomer'] == 0:
                if app_config is not None and app_config['isTravelingCustomer']:
                    self.s.checkSiteVersion(app_config['stratusMusicTerritory'].lower())
                    self.doReInit()
                self.s.delCookies()
                app_config = None
                self.s.access = False
            else:
                self.s.appConfig(app_config)
                self.s.setCookie()
                self.doReInit()
                self.delCredentials()
                self.s.access = True
            x+=1
        return True
    def doReInit(self): ##### -->  TODO
        #self.setVariables()
        # self.prepFolder() --> reinit of AMs
        self.prepBrowser()
        pass
    def doLogonForm(self):
        self.br.select_form(name="signIn")
        if not self.br.find_control("email").readonly:
            self.br["email"] = self.s.userEmail
        self.br["password"] = self.s.userPassword
    def getLogonResponse(self):
        self.br.submit()
        resp = self.br.response()
        #try:
        #    return unicode(resp.read(), "utf-8") # for kodi 18
        #except:
        #    return str(resp.read(), encoding = 'utf-8') # for kodi 19
        return str(resp.read(), encoding = 'utf-8')
    def checkMFA(self):
        while 'action="verify"' in self.content or 'id="auth-mfa-remember-device' in self.content:
            soup = self.parseHTML(self.content)
            if 'cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none' in self.content:
                self.s.log('MFA - account name')
                form = soup.find('form', class_="cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none")
                msgheading = form.find('label', class_="a-form-label").getText().strip()
                msgtxt = ""
                inp = self.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'dcq_question_subjective_1') == False:
                    return False
            elif 'name="claimspicker"' in self.content:
                self.s.log('MFA - SMS code step 1')
                form = soup.find_all('form', attrs={'name':'claimspicker'})
                msgheading = form[0].find('h1').renderContents().strip()
                msgtxt = form[0].findAll('div', class_='a-row')[1].renderContents().strip()
                if xbmcgui.Dialog().yesno(msgheading, msgtxt):
                    self.br.select_form(nr=0)
                    self.content = self.getLogonResponse()
                else:
                    return False
            elif 'name="code"' in self.content: # sms info
                self.s.log('MFA - SMS code step 2')
                form = soup.find_all('form', class_='cvf-widget-form fwcim-form a-spacing-none')
                msgheading = form[0].findAll(lambda tag: tag.name == 'span' and not tag.attrs)
                msgheading = msgheading[1].text + '\n' + msgheading[2].text
                msgtxt = ''
                inp = self.getUserInput(msgheading, msgtxt)
                if self.checkMFAInput(inp,'code') == False:
                    return False
            elif 'auth-mfa-form' in self.content:
                msg = soup.find('form', id='auth-mfa-form')
                self.s.log('### MFA ###############')
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
        self.s.log('########### captcha ###########')
        #self.br.select_form(name="")
        self.br.select_form(action="/errors/validateCaptcha")
        self.content = str(self.br.response().read(), encoding = 'utf-8')
        soup = self.parseHTML(self.content)
        #self.s.log(soup)
        form = soup.find_all('form')
        msgheading = form[0].find('h4').renderContents().strip()
        img = form[0].find('img') #.renderContents().strip()
        self.s.log(msgheading)
        self.s.log(img)
        self.dia = Captcha(msgheading,img)
        xbmc.sleep(5000)
        # """
        # """ create popup window for captcha """
        # """
        # #window = PopupWindow(msgheading,img)
        # #window.show()
        # #xbmc.sleep(5000)
        # #window.close()
        # #del window
        # """
        # #return

# from .l10n import getString

class Captcha(xbmcgui.WindowDialog):
    """ Captcha dialog """
    def __init__(self): #,header,img):
        self.vcode_path = 'https://images-na.ssl-images-amazon.com/captcha/fmvtfjch/Captcha_ntfzkqsebj.jpg'
 
        # windowItems
        self.image          = xbmcgui.ControlImage(80, 100, 200, 70, self.vcode_path) # x, y , width, hight
        self.buttonInput    = xbmcgui.ControlButton(100, 160, 140, 50, label='Input', font='font20')
        self.buttonRefresh  = xbmcgui.ControlButton(250, 160, 140, 50, label='Refresh', font='font20')
        self.addControls([self.image, self.buttonInput, self.buttonRefresh])
        self.setFocus(self.buttonInput)
 
    def onControl(self, event):
        if event == self.buttonInput:
            self.close()
        # elif event == self.buttonRefresh:
        #     (self.codeString, self.vcode_path) = auth.refresh_vcode(self.cookie, self.tokens, self.vcodetype)
        #     if self.codeString and self.vcode_path:
        #         self.removeControl(self.image)
        #         self.image = xbmcgui.ControlImage(80, 100, 500, 200, self.vcode_path)
        #         self.addControl(self.image)
        #     else:
        #         dialog.ok('Error', u'无法刷新验证码，请重试')

    # def get_response(img):
    #     try:
    #         img = xbmcgui.ControlImage(450, 0, 400, 130, img)
    #         wdlg = xbmcgui.WindowDialog()
    #         wdlg.addControl(img)
    #         wdlg.show()
    #         common.kodi.sleep(3000)
    #         solution = common.kodi.get_keyboard(common.i18n('letters_image'))
    #         if not solution:
    #             raise Exception('captcha_error')
    #     finally:
    #         wdlg.close()
    #         return solution

    # value = 0  # Contains the selected options bitmask

    # # def __init__(self, title=getString(30087), label=getString(30088)):
    # def __init__(self, title='TestTitle', label='TestLabel'):
    #     """Class constructor"""
    #     # Call the base class' constructor.
    #     self._label = label
    #     super(Captcha, self).__init__(title)
    #     self.setGeometry(460, 280, 3, 2)
    #     self.set_controls()
    #     # self.set_navigation()
    #     # self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
    #     self.doModal()

    # def set_controls(self):
    #     """Set up UI controls"""
    #     # Text label
    #     label = pyxbmct.Label(self._label)
    #     self.placeControl(label, 0, 0, rowspan=1, columnspan=2)
    #     # None
    #     self.btnNone = pyxbmct.Button('Button 1')
    #     self.placeControl(self.btnNone, 1, 0)
    #     self.connect(self.btnNone, self.close)
    #     # Catalog
    #     self.btnCatalog = pyxbmct.Button('Button 2')
    #     self.placeControl(self.btnCatalog, 1, 1)
    #     self.connect(self.btnCatalog, lambda: self.clear(1))

    # # def set_navigation(self):
    # #     """Set up keyboard/remote navigation between controls."""
    # #     # None Catalog
    # #     # Video   Both
    # #     self.btnNone.controlRight(self.btnCatalog)
    # #     self.btnNone.controlDown(self.btnVideo)
    # #     self.btnCatalog.controlLeft(self.btnNone)
    # #     self.btnCatalog.controlDown(self.btnBoth)
    # #     self.btnVideo.controlUp(self.btnNone)
    # #     self.btnVideo.controlRight(self.btnBoth)
    # #     self.btnBoth.controlLeft(self.btnVideo)
    # #     self.btnBoth.controlUp(self.btnCatalog)
    # #     self.setFocus(self.btnNone)

    # def clear(self, what):
    #     self.value = what
    #     self.close()