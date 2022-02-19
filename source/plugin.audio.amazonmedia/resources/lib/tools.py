#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, pickle
import urllib.parse as urlparse
import xbmc, xbmcgui, xbmcaddon, xbmcvfs, xbmcplugin
from resources.lib.access import AMaccess
from resources.lib.singleton import Singleton

class AMtools( Singleton ):
    """ Allow the usage of dot notation for data inside the g dictionary, without explicit function call """
    G = {}
    def __init__( self ):
        self.setVariables()

    def setVariables( self ):
        """ initialize global addon variables """
        self.musicURL           = 'https://music.amazon.{}'
        self.userAgent          = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36'

        self.G['addonBaseUrl']  = sys.argv[0]
        self.G['addonHandle']   = int(sys.argv[1])
        self.G['addonArgs']     = urlparse.parse_qs(sys.argv[2][1:])
        self.G['addonMode']     = self.G['addonArgs'].get('mode', None)
        self.G['addonFolder']   = xbmcvfs.translatePath( 'special://home/addons/{}'.format( self.getInfo('id') ) )
        self.G['addonUDatFo']   = xbmcvfs.translatePath( 'special://profile/addon_data/{}'.format( self.getInfo('id') ) )

        self.G['TLDlist']       = ['de', 'fr', 'co.uk', 'it', 'es']

        self.credentials        = AMaccess()
        self.credentials.USERTLD = self.G['TLDlist'][int(self.getSetting('userTLD'))]

        self.G['audioQuality']  = 'HIGH'
        self.G['maxResults']    = 100
        self.G['logging']       = self.getSetting('logging')
        self.G['showcolentr']   = self.getSetting('showcolentr')
        self.G['showimages']    = self.getSetting('showimages')

    @staticmethod
    def getInfo( oProp ):
        """
        Provide addon properties.
        :param str oProp:   The requested property
        """
        return xbmcaddon.Addon().getAddonInfo(oProp)

    @staticmethod
    def getMode():
        """
        Current addon runmode
        """
        return urlparse.parse_qs(sys.argv[2][1:]).get('mode', [None])[0]

    def getSetting( self, oProp ):
        """
        Provide the current setting
        :param str oProp:   key of the setting
        """
        prop = xbmcaddon.Addon().getSetting(oProp)
        if (str.lower(prop) == 'true' or
            str.lower(prop) == 'false'):
            prop = self.toBool(prop)
        return prop

    @staticmethod
    def setSetting( oProp, val ):
        """
        Save the given setting
        :param str oProp:   key of the setting
        :param str val:     value of the setting
        """
        xbmcaddon.Addon().setSetting(oProp,val)

    @staticmethod
    def getTranslation( oId ):
        """
        Provide the translation of oID
        :param int oId: string ID
        """
        return xbmcaddon.Addon().getLocalizedString(oId)

    @staticmethod
    def toBool( s ):
        """
        Convert the given string to bool
        :param str s: string to convert
        """
        if s == 'True' or s == 'true':
             return True
        else:
             return False

    @staticmethod
    def log( msg=None, level=xbmc.LOGINFO ):
        """
        Write some log data
        :param str msg:     log information
        :param str level:   level of logging
        """
        fct_name  = sys._getframe(1).f_code.co_name
        lin_nmbr  = sys._getframe(1).f_lineno
        if msg:
            msg = '{}{}'.format(os.linesep,msg)
        else:
            msg = ''
        log_message = '[{}] {} : {}{}'.format(xbmcaddon.Addon().getAddonInfo('name'), fct_name, lin_nmbr, msg)
        xbmc.log(log_message, level)

    def setSearch( self, q, query ):
        """
        Store the last three search entries and keep the most recent on the 1st position
        :param str q:       search category
        :param str query:   user query string
        """
        update = True
        for i in q:
            if self.getSetting(i) == query:
                update = False
                break
        if update:
            self.setSetting(q[2],self.getSetting(q[1]))
            self.setSetting(q[1],self.getSetting(q[0]))
            self.setSetting(q[0],query)

    def load( self ):
        """
        Load data from a file in addon_data folder.
        :return: a data object
        """
        oPath = xbmcvfs.translatePath(
            'special://profile/addon_data/{}/data.obj'.format(
                xbmcaddon.Addon().getAddonInfo('id')
            )
        )
        with open(oPath, 'rb') as file:
            self.credentials = pickle.load(file)
        
        self.credentials.COOKIE.load(
            os.path.join(
                xbmcvfs.translatePath('special://profile/addon_data/{}'.format(
                    xbmcaddon.Addon().getAddonInfo('id'))
                ), 'cookie'
            ),
            ignore_discard=True,
            ignore_expires=True
        )
        return self.credentials
    
    @staticmethod
    def save( obj ):
        """
        Save the object data to a file in addon_data folder.
        """
        path = '{}{}{}'.format(
            xbmcvfs.translatePath('special://profile/addon_data/{}'.format(
                xbmcaddon.Addon().getAddonInfo('id'))
            ),
            os.sep,
            'data.obj'
        )
        with open(path, 'wb') as file:
            pickle.dump(obj, file, pickle.HIGHEST_PROTOCOL)
            file.close()

    @staticmethod
    def saveCookie( obj ):
        """
        Save the cookie data to a file in addon_data folder.
        :param cookie_object obj: CookieJar object
        """
        obj.save(
            os.path.join(
                xbmcvfs.translatePath('special://profile/addon_data/{}'.format(
                    xbmcaddon.Addon().getAddonInfo('id'))
                ), 'cookie'
            ),
            ignore_discard=True,
            ignore_expires=True
        )

    @staticmethod
    def delFile( delFile ):
        """
        Remove the given file
        :param str delFile: path + file name to be removed
        """
        try:
            if os.path.exists(delFile):
                os.remove(delFile)
        except:
            pass

    @staticmethod
    def getUserInput( title, txt, hidden=False, uni=False ):
        """
        Generic user input
        :param str title:   title of the dialog
        :param str txt:     content of the dialog
        :param bool hidden: user input visible / unvisible
        :param bool uni:    unicode encoding active / inactive
        """
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

    @staticmethod
    def checkUserTLD( userTLD, domainList ):
        """
        Validate the received user top level domain, returns the index of domain array
        :param str   userTLD: The users top level domain
        :param array domainList: List of supported domains
        """
        if userTLD in domainList:
            x = 0
            for i in domainList:
                if userTLD == i:
                    return str(x)
                else:
                    x+=1
        else:
            return '0'

    def set_userTLD( self, userTLD ):
        """
        Set user top level domain.
        :param int userTLD: Index of user domain to be set
        """
        self.credentials.USERTLD = self.G['TLDlist'][int(userTLD)]

    def resetAddon( self ):
        """
        Remove Cookie and Setting, initilialize the variables to defaults
        """
        data = {
            'userTLD': '0',
            'logging': 'false',
            'showimages': 'true',
            'showUnplayableSongs': 'false',
            'showcolentr': 'true',
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
            self.setSetting( key, value )
        self.resetCredentials()

    def resetCredentials( self ):
        """
        Remove Cookie and data object files
        """
        # remove cookie
        # path = xbmcvfs.translatePath('special://profile/addon_data/{}'.format(
        #     xbmcaddon.Addon().getAddonInfo('id'))
        # )
        files = { 'cookie', 'data.obj' }
        for f in files:
            file = '{}{}{}'.format( self.G['addonUDatFo'], os.sep, f )
            self.delFile( file )
        # remove data object
        # file = '{}{}{}'.format( self.G['addonUDatFo'], os.sep, 'data.obj' )
        # self.delFile( file )
        #xbmc.sleep(randint(750,1500))
        # self.setVariables()

    def createList( self, data, dynentry=False, soccer=False ):
        """
        Create list entries for Kodi menu
        :param array data:      content of Kodi menu
        :param bool dynentry:   flag for dynamic content (e.g. search items)
        """
        itemlist = []
        url = None
        for item in data:
            #self.log(item)
            isFolder = True
            if dynentry and 'search' in item and self.getSetting(item['search']) == '':
                continue
            # if soccer:
            if soccer or ('special' in item and item['special'] == 'newrecom'):
                title = item['txt']
            else:
                title = self.getTranslation(item['txt'])

            if dynentry and 'search' in item:
                title += self.getSetting(item['search'])
            li = xbmcgui.ListItem(label=title)
            li.setInfo(type="music", infoLabels={"title": title})
            if 'img' in item:
                if 'http' in item['img']:
                    url = item['img']
                else:
                    url = '{}/resources/images/{}'.format( self.G['addonFolder'], item['img'] )
                li.setArt({
                    'icon':url,
                    'thumb':url,
                    'fanart':url,
                    'poster':url,
                    'banner':url,
                    'landscape':url
                })
            url = '{}?mode={}'.format( self.G['addonBaseUrl'], str(item['fct']) )
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
        self.finalizeContent( self.G['addonHandle'], itemlist, 'albums' )

    @staticmethod
    def finalizeContent( addonHandle, itemlist, ctype ):
        """
        Finalization of Kodi list items
        :param str addonHandle: Kodi addon handle
        :param array itemlist:  Array of list items
        :param str ctype:       Content type ( songs / albums )
        """
        xbmcplugin.addDirectoryItems(addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(addonHandle, ctype)
        xbmcplugin.endOfDirectory(addonHandle)

    def prepReqHeader( self, amzTarget ):
        """
        Request header preparation
        :param str amzTarget: API endpoint
        """
        head = { 'Accept' : 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding' : 'gzip, deflate', #,br
                'Accept-Language' : '{},en-US,en;q=0.9'.format( self.credentials.USERTLD ),
                'csrf-token' :      self.credentials.CSRF_TOKEN,
                'csrf-rnd' :        self.credentials.CSRF_RND,
                'csrf-ts' :         self.credentials.CSRF_TS,
                'Host' :            'music.amazon.{}'.format( self.credentials.USERTLD ),
                'Origin' :          self.musicURL.format( self.credentials.USERTLD ),
                'User-Agent' :      self.userAgent,
                'X-Requested-With' : 'XMLHttpRequest'
        }

        if amzTarget is not None:
            head['Content-Encoding'] = 'amz-1.0'
            head['Content-Type'] = 'application/json'
            head['X-Amz-Target'] = amzTarget

        return head