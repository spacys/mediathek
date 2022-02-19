#!/usr/bin/env python
# -*- coding: utf-8 -*-

import http.cookiejar as cookielib
from resources.lib.singleton import Singleton

class AMaccess( Singleton ):
    """
    Predefined variables to store user connection information
    """
    CSRF_TOKEN      = CSRF_TS       = CSRF_RND = None
    DEVICEID        = CUSTOMERID    = MARKETPLACEID = None
    DEVICETYPE      = ACCESSTYPE    = None
    MUSICTERRITORY  = CUSTOMERLANG  = LOCALE = REGION =  USERTLD = None
    USEREMAIL       = USERPASSWORD  = None
    COOKIE = cookielib.MozillaCookieJar()
    #COOKIE = requests.cookies.RequestsCookieJar()
