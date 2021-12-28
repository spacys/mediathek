#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from resources.lib.singleton import Singleton
from resources.lib.tools import AMtools

class AMreset(Singleton):
    def resetAddon(self):
        # AMtools().delCookies(self.cookieFile)
        self.addonUDatFo = AMtools().getFolder('special://profile/addon_data/{}'.format(AMtools().getInfo('id')))
        settings = '{}{}{}'.format(self.addonUDatFo, os.sep, 'settings.xml')
        if os.path.exists(settings):
             os.remove(settings)
        data = {
            'csrf_ts':'',
            'csrf_rnd': '',
            'csrf_ts': '' ,
            'csrf_rnd': '' ,
            'csrf_token': '' ,
            'accessToken': '' ,
            'customerId': '' ,
            'marketplaceId': '' ,
            'deviceId': '' ,
            'deviceType': '' ,
            'musicTerritory': '' ,
            'locale': '' ,
            'customerLang': '' ,
            'region': '' ,
            'url': '' ,
            'saveUsername': 'false' ,
            'savePassword': 'false' ,
            'userEmail': '' ,
            'userPassword': '' ,
            'access': 'false' ,
            'logging': 'false' ,
            'showimages': 'true' ,
            'showUnplayableSongs': 'false' ,
            'showcolentr': 'true' ,
            'accessType': '' ,
            'search1PlayLists': '' ,
            'search2PlayLists': '' ,
            'search3PlayLists': '' ,
            'search1Albums': '' ,
            'search2Albums': '' ,
            'search3Albums': '' ,
            'search1Songs': '' ,
            'search2Songs': '' ,
            'search3Songs': '' ,
            'search1Stations': '' ,
            'search2Stations': '' ,
            'search3Stations': '' ,
            'search1Artists': '' ,
            'search2Artists': '' ,
            'search3Artists': '' ,
            'captcha': ''
        }
        g = AMtools()
        for key, value in data.items():
            #AMtools().log(key + ' : ' + value)
            g.addon.setSetting(key, value)
            #AMtools().setSetting(key, value)
        #self.setVariables()