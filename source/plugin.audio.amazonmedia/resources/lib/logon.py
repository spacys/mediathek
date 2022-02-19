#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json, mechanize
from bs4 import BeautifulSoup
from resources.lib.tools import AMtools

import xbmc, xbmcgui

class AMlogon( AMtools ):
    """
    Connection class provides user login.
    """
    def _getCredentials( self ):
        """
        User dialog for E-Mail and Password
        """
        if not self.credentials.USEREMAIL or not self.credentials.USERPASSWORD:
            if not self.credentials.USEREMAIL:
                user = self.getUserInput( self.getTranslation(30030), '', hidden=False, uni=False ) # get Email
                if user:
                    self.credentials.USEREMAIL = user
            else:
                user = True
            if user and not self.credentials.USERPASSWORD:
                pw = self.getUserInput( self.getTranslation(30031), '', hidden=True, uni=False ) # get Password
                if pw:
                    self.credentials.USERPASSWORD = pw
                    return True
                else:
                    return False
            else:
                return False
        return True

    @staticmethod
    def _parseHTML( resp ):
        """
        Make the request more readable
        """
        resp = re.sub(r'(?i)(<!doctype \w+).*>', r'\1>', resp)
        return BeautifulSoup(resp, 'html.parser')

    def _prepBrowser( self ):
        """
        Setup the virtual brower with header information for logon
        """
        self._br = mechanize.Browser()
        self._br.set_handle_robots(False)
        self._br.set_handle_gzip(False)
        self._br.set_handle_redirect(True)
        self._br.set_handle_referer(True)
        self._br.set_handle_equiv(True)
        self._br.set_cookiejar(self.credentials.COOKIE)
        self._br.addheaders = [
            ('Accept',          'application/json, text/javascript, */*; q=0.01'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Accept-Language', '{},en-US;en;q=0.9'.format(self.credentials.USERTLD) ),
            ('Connection',      'keep-alive'),
            ('Content-Type',    'application/json; charset=utf-8'),
            ('User-Agent',      self.userAgent),
            ('Upgrade-Insecure-Requests', '1')
        ]

    def amazonLogon( self ):
        """
        Entry point for logon procedure
        """
        if not self._getCredentials():  return False
        self._prepBrowser()
        amzURL = 'https://www.amazon.{}/gp/aw/si.html'.format(self.credentials.USERTLD)
        self._br.open(amzURL)
        self._br.select_form(name="signIn")
        if not self._br.find_control("email").readonly:
            self._br["email"] = self.credentials.USEREMAIL
        self._br["password"] = self.credentials.USERPASSWORD
        self._getLogonResponse()

        if not self._checkMFA():    return False
        if not self._checkConfig(): raise Exception("Something went wrong! Logon was not successful!")

        #self.credentials.USEREMAIL      = None # do not store user mail
        self.credentials.USERPASSWORD   = None # do not store user password
        self.save( self.credentials )
        return self.credentials

    def _getLogonResponse( self ):
        """
        Reusable submit function, stores the response in class variable
        """
        self._br.submit()
        # self.log( str(self._br.response().read(), encoding = 'utf-8') )
        self._content = str(self._br.response().read(), encoding = 'utf-8')

    def _checkCaptcha( self ):
        """
        Captcha validation, currently not in use
        """
        self._captcha = ''
        self._br.select_form(action="/errors/validateCaptcha")
        self._content = str(self._br.response().read(), encoding = 'utf-8')
        soup = self._parseHTML(self._content)
        # self.log(soup)
        form = soup.find_all('form')
        msgheading = str(form[0].find('h4').renderContents().strip(), encoding = 'utf-8')
        img = form[0].find('img')
        # self.log(msgheading)
        # self.log(img['src'])
        self._btn_cancel = False
        # TODO
        self._showCaptcha('captcha.xml',img['src'],msgheading)
        self._captcha = self.getSetting('captcha')
        if self._captcha == "":
            return False
        self._br["field-keywords"] = self._captcha
        return True

    def _showCaptcha( self, layout, imagefile, message ):
        """
        Captcha dialog, currently not in use
        """
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
        cp = Captcha(layout, self.G['addonFolder'], 'Default', image=imagefile, text=message, settings=self)
        cp.doModal()
        del cp

    def _checkMFA( self ):
        """
        Validate additional access steps
        """
        while 'action="verify"' in self._content or 'id="auth-mfa-remember-device' in self._content:
            soup = self._parseHTML(self._content)
            if 'cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none' in self._content:
                self.log('MFA - account name')
                form = soup.find('form', class_="cvf-widget-form cvf-widget-form-dcq fwcim-form a-spacing-none")
                msgheading = form.find('label', class_="a-form-label").getText().strip()
                msgtxt = ""
                inp = self.getUserInput(msgheading, msgtxt)
                if self._checkMFAInput(inp,'dcq_question_subjective_1') == False:
                    return False
            elif 'name="claimspicker"' in self._content:
                self.log('MFA - SMS code step 1')
                form = soup.find_all('form', attrs={'name':'claimspicker'})
                msgheading = form[0].find('h1').renderContents().strip()
                msgtxt = form[0].findAll('div', class_='a-row')[1].renderContents().strip()
                if xbmcgui.Dialog().yesno(msgheading, msgtxt):
                    self._br.select_form(nr=0)
                    self._getLogonResponse()
                else:
                    return False
            elif 'name="code"' in self._content: # sms info
                self.log('MFA - SMS code step 2')
                form = soup.find_all('form', class_='cvf-widget-form fwcim-form a-spacing-none')
                msgheading = form[0].findAll(lambda tag: tag.name == 'span' and not tag.attrs)
                msgheading = msgheading[1].text + os.linesep + msgheading[2].text
                msgtxt = ''
                inp = self.getUserInput(msgheading, msgtxt)
                if self._checkMFAInput(inp,'code') == False:
                    return False
            elif 'auth-mfa-form' in self._content:
                msg = soup.find('form', id='auth-mfa-form')
                self.log('### MFA ###############')
                msgheading = msg.p.renderContents().strip()
                msgtxt = ''
                inp = self.getUserInput(msgheading, msgtxt)
                if self._checkMFAInput(inp,'otpCode','ActivateWindow(busydialog)') == False:
                    return False
            else: # Unknown form
                # captcha call here
                return False
        return True

    def _checkMFAInput( self, inp, target, action=None ):
        if inp:
            if action:
                xbmc.executebuiltin(action)
            self._br.select_form(nr=0)
            self._br[target] = inp
            self._getLogonResponse()
        else:
            return False

    def _checkConfig( self ):
        """
        After initial login, check accessibility of music amazon site and collect the user data
        """
        app_config = None
        configfound = False
        self._br.open( self.musicURL.format( self.credentials.USERTLD ) )
        # self.log('after login')
        # self.log( str(self._br.response().read(), encoding = 'utf-8') )
        self._content = str(self._br.response().read(), encoding = 'utf-8')
        soup = self._parseHTML(self._content)
        # self.log(soup)
        script_list = soup.find_all('script')
        for scripts in script_list:
            # self.log(scripts.contents)
            if 'appConfig' in scripts.contents[0]:
                sc = scripts.contents[0]
                sc = sc.replace( "window.amznMusic = " , "" )
                sc = sc.replace( "appConfig:" , "\"appConfig\":" )
                sc = sc.replace( "ssr: false," , "\"ssr\":\"\"" )
                sc = sc.replace( "false" , "\"\"" )
                sc = sc.replace( "true" , "\"\"" )
                sc = sc.replace( os.linesep , "" )
                sc = sc.replace( ";" , "" )
                # self.log(sc)
                if not 'tier' in sc:
                    self.log('No tier available, lonon was not successful.')
                    break
                app_config = json.loads(sc)
                self.log('Config available')
                configfound = True
                break
            else:
                self.log('No config available')
                continue
        if not configfound:
            return False
        self._appConfig( app_config['appConfig'] )
        self.saveCookie( self.credentials.COOKIE )
        return True

    def _appConfig( self, app_config ):
        """
        Obtain access token and other important information
        :param array app_config: The application configuration
        """
        #self.log(app_config)
        self.credentials.CSRF_TOKEN =        app_config['csrf']['token']
        self.credentials.CSRF_TS =           app_config['csrf']['ts']
        self.credentials.CSRF_RND =          app_config['csrf']['rnd']
        self.credentials.DEVICEID =          app_config['deviceId']
        self.credentials.CUSTOMERID =        app_config['customerId']
        self.credentials.MARKETPLACEID =     app_config['marketplaceId']
        self.credentials.DEVICETYPE =        app_config['deviceType']
        self.credentials.MUSICTERRITORY =    app_config['musicTerritory']
        self.credentials.LOCALE =            app_config['displayLanguage']
        self.credentials.CUSTOMERLANG =      app_config['musicTerritory'].lower()
        self.credentials.REGION =            app_config['siteRegion']
        self.set_userTLD(
            self.checkUserTLD(
                app_config['musicTerritory'].lower(),
                self.G['TLDlist']
            )
        )

        if app_config['tier'] == 'UNLIMITED_HD':
            self.credentials.ACCESSTYPE = 'UNLIMITED'
        else:
            self.credentials.ACCESSTYPE =  app_config['tier']
