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
        if self.s.logging: self.s.log()
        resp = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', resp)
        return BeautifulSoup(resp, 'html.parser')
    def delCredentials(self):
        if self.s.logging: self.s.log()
        self.s.userEmail = ''
        self.s.userPassword = ''
    def getCredentials(self):
        if self.s.logging: self.s.log()
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
        if self.s.logging: self.s.log()
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
        xbmc.sleep(500)
        return ret
    def prepBrowser(self):
        if self.s.logging: self.s.log()
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
    def doReInit(self):
        if self.s.logging: self.s.log()
        self.s.setVariables()
        self.prepBrowser()
    def amazonLogon(self):
        if self.s.logging: self.s.log()
        self.s.logonProcess = True
        self.s.delCookies()
        self.doReInit()
        self.s.addonMode = None
        self.s.access = False
        x = 1
        while not self.s.access:
            if x == 3: return False
            x+=1
            if not self.getCredentials(): return False
            self.br.open(self.s.logonURL)
            # self.br.open('https://music.amazon.de')
            # self.br.open('https://www.amazon.de/gp/aw/si.html')
            # self.s.log(self.br.response().code())
            # self.s.log(self.br.response().info())
            # self.s.log( str(self.br.response().read(), encoding = 'utf-8') )
            # return False
            try: 
                self.doLogonForm()
            except:
                self.checkCaptcha()

                if self.s.btn_cancel:
                    return False
                else:
                    self.content = self.getLogonResponse()
                    # self.s.log(self.content)
                    self.s.setVariables()
                    try:
                        if self.checkConfig():
                            break
                    except:
                        continue
                
            self.content = self.getLogonResponse()
            # self.s.log(self.content)
            if not self.checkMFA(): return False
            # self.s.setCookie()
            # if not os.path.isfile(self.s.cookieFile): break
            if self.checkConfig():
                break
            else:
                return False
        self.s.logonProcess = False
        # self.delCredentials()
        self.s.setVariables()
        # self.doReInit()
        return True
    def doLogonForm(self):
        if self.s.logging: self.s.log()
        self.br.select_form(name="signIn")
        self.br["email"]    = self.s.userEmail
        self.br["password"] = self.s.userPassword
    def getLogonResponse(self):
        if self.s.logging: self.s.log()
        self.br.submit()
        self.s.setCookie()
        resp = self.br.response()
        return str(resp.read(), encoding = 'utf-8')
    def checkConfig(self):
        if self.s.logging: self.s.log()
        app_config = None
        self.s.cj.load(self.s.cookieFile)
        head = self.s.prepReqHeader('')
        resp = requests.post(self.s.musicURL, data=None, headers=head, cookies=self.s.cj)
        #self.s.log(resp.text)
        configfound = False
        soup = self.parseHTML(resp.text)
        script_list = soup.find_all('script')
        for scripts in script_list:
            # self.s.log(scripts.contents)
            if 'appConfig' in scripts.contents[0]:
                if self.s.logging: self.s.log('Config available')
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
                sc = sc.replace(";","")
                sc = sc.replace("\"ssr\":\"false\",","\"ssr\":\"false\"")
                # self.s.log(sc)
                app_config = json.loads(sc)
                configfound = True
                break
            else:
                if self.s.logging: self.s.log('No config available')
                continue
        if not configfound:
            return False
        # self.s.log(app_config)
        self.s.appConfig2(app_config['appConfig'])
        self.s.setCookie()
        self.s.access = True
        self.s.setSetting('access','true')
        self.s.setVariables()
        return True
    def checkMFA(self):
        if self.s.logging: self.s.log()
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
        if self.s.logging: self.s.log()
        if inp:
            if action:
                xbmc.executebuiltin(action)
            self.br.select_form(nr=0)
            self.br[target] = inp
            self.content = self.getLogonResponse()
        else:
            return False
    def checkCaptcha(self):
        if self.s.logging: self.s.log()
        self.s.setSetting('captcha',"")
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
    def showCaptcha(self,layout, imagefile, message):
        if self.s.logging: self.s.log()
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
                # self.s.log(controlid)
                if controlid == self.btn_ok:
                    # self.s.log('btn_ok')
                    self.close()
                elif controlid == self.btn_cancel:
                    # self.s.log('btn_cancel')
                    self.s.captcha = ""
                    self.s.btn_cancel = True
                    self.close()
                elif controlid == self.btn_input:
                    # self.s.log('btn_input')
                    self.getUserInput('Captcha Entry')
        cp = Captcha(layout, self.s.addonFolder, 'Default', image=imagefile, text=message, settings=self.s)
        cp.doModal()
        del cp
        xbmc.sleep(750)