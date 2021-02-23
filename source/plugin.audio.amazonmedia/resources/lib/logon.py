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
        self.prepBrowser()
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
                ret = str(kb.getText(), encoding = 'utf-8')
            else:
                ret = kb.getText() # for password needed, due to encryption
        else:
            ret = False
        xbmc.sleep(500)
        del kb
        return ret
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
                if self.s.btn_cancel:
                    return False
                else:
                    continue
            self.content = self.getLogonResponse()
            # self.s.log(self.content)

            if x == 3:
                return False

            if not self.checkMFA():
                return False

            self.s.setCookie()
            if not os.path.isfile(self.s.cookieFile):
                break

            self.s.cj.load(self.s.cookieFile)
            head = self.s.prepReqHeader('')
            resp = requests.post(self.s.musicURL, data=None, headers=head, cookies=self.s.cj)
            #self.s.log('########### final page ###########')
            #self.s.log(resp.text)

            configfound = False
            soup = self.parseHTML(resp.text)
            script_list = soup.find_all('script')
            for scripts in script_list:
                # self.s.log(scripts.contents)
                if 'appConfig' in scripts.contents[0]:
                    #self.s.log('########### scripts found ###########')
                    #self.s.log(scripts.contents)
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
                    # self.s.log(sc)
                    app_config = json.loads(sc)
                    configfound = True
                    break
                else:
                    #self.s.log('########### nothing found ###########')
                    continue
            if not configfound:
                return False

            # self.s.log(app_config)
            # if not alt:
            #     if app_config is None or app_config['isRecognizedCustomer'] == 0:
            #         if app_config is not None and app_config['isTravelingCustomer']:
            #             self.s.checkSiteVersion(app_config['stratusMusicTerritory'].lower())
            #             self.doReInit()
            #         self.s.delCookies()
            #         app_config = None
            #         self.s.access = False
            #     else:
            #         self.s.appConfig(app_config)
            #         self.s.setCookie()
            #         self.doReInit()
            #         self.delCredentials()
            #         self.s.access = True
            # else:
            self.s.appConfig2(app_config['appConfig'])
            self.s.setCookie()
            self.doReInit()
            self.delCredentials()
            self.s.access = True
            x+=1
        return True
    def doReInit(self): ##### -->  TODO
        self.s.setVariables()
        self.prepBrowser()
    def doLogonForm(self):
        # self.s.log('########### logon form ###########')
        self.br.select_form(name="signIn")
        if not self.br.find_control("email").readonly:
            self.br["email"] = self.s.userEmail
        self.br["password"] = self.s.userPassword
    def getLogonResponse(self):
        self.br.submit()
        resp = self.br.response()
        return str(resp.read(), encoding = 'utf-8')
    def checkMFA(self):
        # self.s.log('########### check MFA ###########')
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
        # self.s.log('########### captcha ###########')
        self.br.select_form(action="/errors/validateCaptcha")
        self.content = str(self.br.response().read(), encoding = 'utf-8')
        soup = self.parseHTML(self.content)
        # self.s.log(soup)
        form = soup.find_all('form')
        msgheading = str(form[0].find('h4').renderContents().strip(), encoding = 'utf-8')
        img = form[0].find('img') #.renderContents().strip()
        # self.s.log(msgheading)
        # self.s.log(img['src'])
        self.s.btn_cancel = False
        self.showCaptcha('captcha.xml',img['src'],msgheading)
        self.s.captcha = self.s.getSetting('captcha')
        if self.s.captcha == "":
            return False
        self.br["field-keywords"] = self.s.captcha
        self.s.setSetting('captcha',"")
    def showCaptcha(self,layout, imagefile, message):
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
                self.s.setSetting('captcha',self.inp)
                self.show_dialog()
            def onClick(self, controlid):
                if controlid == self.btn_ok:
                    self.close()
                elif controlid == self.btn_cancel:
                    self.s.captcha = ""
                    self.s.btn_cancel = True
                    self.close()
                elif controlid == self.btn_input:
                    self.getUserInput('Captcha Entry')
        cp = Captcha(layout, self.s.addonFolder, 'Default', image=imagefile, text=message, settings=self.s)
        cp.doModal()
        del cp