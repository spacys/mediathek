#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, json
import urllib.parse as urlparse
import xbmc, xbmcgui, xbmcaddon, xbmcvfs, xbmcplugin
from resources.lib.access import AMaccess
from resources.lib.singleton import Singleton
from infotagger.listitem import ListItemInfoTag

class AMtools( Singleton ):
    """ Allow the usage of dot notation for data inside the g dictionary, without explicit function call """
    G = {}
    defaultUserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
    # Seconds to wait for Amazon: to connect, and for each piece of its answer. Without a limit a
    # request that gets no answer blocks the list or the song for good.
    TIMEOUT = (10, 30)
    # Kodi on a Linux desktop decrypts with the Widevine library of Chrome for Linux, so that is what it
    # says it is. Named as Chrome for Windows, Amazon expected a Verified Media Path, which Chrome has
    # on Windows and not on Linux, and refused every license with VMP_VALIDATION_FAILED.
    linuxUserAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
    # A history that never forgets can only be thinned out one entry at a time.
    SEARCH_HISTORY_SIZE = 25
    SEARCH_KINDS = ('PlayLists', 'Albums', 'Songs', 'Artists')

    def __init__( self ):
        self.setVariables()

    def setVariables( self ):
        """ initialize global addon variables """
        self.musicURL           = 'https://music.amazon.{}'
        self.userAgent          = self.getUserAgent()

        self.G['addonBaseUrl']  = sys.argv[0]
        self.G['addonHandle']   = int(sys.argv[1])
        self.G['addonArgs']     = urlparse.parse_qs(sys.argv[2][1:])
        self.G['addonMode']     = self.G['addonArgs'].get('mode', None)
        self.G['addonFolder']   = xbmcvfs.translatePath( 'special://home/addons/{}'.format( self.getInfo('id') ) )
        self.G['addonUDatFo']   = xbmcvfs.translatePath( 'special://profile/addon_data/{}'.format( self.getInfo('id') ) )

        self.G['TLDlist']       = ['de', 'fr', 'co.uk', 'it', 'es']
        # Amazon reports a country code as music territory, which differs from the top level domain
        self.G['territoryTLD']  = {'gb': 'co.uk'}

        self.credentials        = AMaccess()
        self.credentials.USERTLD = self.G['TLDlist'][int(self.getSetting('userTLD'))]

        self.G['maxResults']    = 100
        self.G['logging']       = self.getSetting('logging')

    # The web player takes the region of the API path from the music territory, not from the site region.
    API_REGIONS = dict(
        [(t, 'NA') for t in ('US', 'CA', 'MX', 'BR', 'AR', 'BO', 'CL', 'CO', 'CR', 'DO', 'EC', 'SV', 'GT', 'HN',
                             'NI', 'PA', 'PY', 'PE', 'UY')] +
        [(t, 'ZAZ') for t in ('GB', 'DE', 'CH', 'AT', 'FR', 'IT', 'ES', 'IN', 'AE', 'SA', 'EG', 'IE', 'BE', 'BG',
                              'CY', 'CZ', 'EE', 'FI', 'GR', 'HU', 'IS', 'LV', 'LI', 'LT', 'LU', 'MT', 'NL', 'PL',
                              'PT', 'SK', 'SE')] +
        [(t, 'FE') for t in ('JP', 'AU', 'NZ')]
    )

    @classmethod
    def apiRegion( cls, territory, siteRegion=None ):
        """
        Region part of the API path, https://music.amazon.<tld>/<region>/api/<service>/
        :param str territory:   music territory of the account, e.g. DE
        :param str siteRegion:  taken for a territory the web player does not list
        """
        return cls.API_REGIONS.get( (territory or '').upper(), siteRegion or 'NA' )

    def getUserAgent( self ):
        linux = xbmc.getCondVisibility('System.Platform.Linux') and not xbmc.getCondVisibility('System.Platform.Android')
        return self.getSetting('userAgent') or (self.linuxUserAgent if linux else self.defaultUserAgent)

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

    def searchHistory( self, kind ):
        """
        The terms searched for before, the most recent first
        :param str kind:    PlayLists, Albums, Songs or Artists
        """
        return self.loadSearchHistory().get(kind, [])

    def addSearch( self, kind, query ):
        """
        Put the given term first in the search history, once regardless of its case
        :param str kind:    PlayLists, Albums, Songs or Artists
        :param str query:   user query string
        """
        history = self.loadSearchHistory()
        others = [term for term in history.get(kind, []) if term.lower() != query.lower()]
        history[kind] = ([query] + others)[:self.SEARCH_HISTORY_SIZE]
        self.saveSearchHistory(history)

    def deleteSearch( self, kind, query ):
        """
        Remove the given term from the search history
        :param str kind:    PlayLists, Albums, Songs or Artists
        :param str query:   user query string
        """
        history = self.loadSearchHistory()
        history[kind] = [term for term in history.get(kind, []) if term.lower() != query.lower()]
        self.saveSearchHistory(history)

    def loadSearchHistory( self ):
        try:
            with open(self.dataFile('searches.json'), encoding='utf-8') as file:
                return json.load(file)
        except OSError:
            return self.importSearchHistory()
        except ValueError:
            return {}

    def saveSearchHistory( self, history ):
        with open(self.dataFile('searches.json'), 'w', encoding='utf-8') as file:
            json.dump(history, file)

    def importSearchHistory( self ):
        """
        Take over the last three searches per kind that version 2.1 and before kept in hidden settings
        """
        history = {}
        for kind in self.SEARCH_KINDS:
            # Read as they are: getSetting would turn a search for "true" into a bool.
            queries = [xbmcaddon.Addon().getSetting('search{}{}'.format(number, kind)) for number in (1, 2, 3)]
            history[kind] = [query for query in queries if query]
        self.clearOldSearches()
        self.saveSearchHistory(history)
        return history

    def clearOldSearches( self ):
        for kind in self.SEARCH_KINDS:
            for number in (1, 2, 3):
                self.setSetting('search{}{}'.format(number, kind), '')

    # Written by the proxy once Amazon refused a license with VMP_VALIDATION_FAILED.
    VMP_FLAG = 'vmp-unverified'

    def vmpFailed( self ):
        """
        Whether Amazon refused a license because Kodi has no Widevine Verified Media Path
        """
        try:
            with open( self.dataFile(self.VMP_FLAG) ) as flag:
                # A refusal Amazon gave to another browser name says nothing about this one.
                return flag.read().splitlines()[1:2] == [self.userAgent]
        except (IOError, OSError):
            return False

    def dataFile( self, name ):
        """
        Path of a file in the addon_data folder
        :param str name:    file name
        """
        return os.path.join( self.G['addonUDatFo'], name )

    def load( self ):
        """
        The sign-in kept in the addon_data folder: the cookies and what the web player was told
        about customer and device.
        :return: the credentials
        :raises IOError: nothing usable is kept, the user has to sign in
        """
        credentials = AMaccess()
        try:
            with open(self.dataFile('data.json'), encoding='utf-8') as file:
                kept = json.load(file)
        except ValueError:
            raise IOError('The stored sign-in cannot be read')
        except IOError:
            # Up to 2.2.3 the sign-in was kept as a pickled Python object. Reading such a file runs
            # whatever code it names, so it is not read any more: the cookies beside it are still
            # good, and with them Amazon tells the rest anew.
            if not os.path.isfile(self.dataFile('data.obj')):
                raise
            return self.restoreFromCookies( credentials )
        for name in AMaccess.STORED:
            setattr( credentials, name, kept.get(name) )
        credentials.COOKIE.load( self.dataFile('cookie'), ignore_discard=True, ignore_expires=True )
        self.credentials = credentials
        return credentials

    def restoreFromCookies( self, credentials ):
        """
        Take a sign-in of an earlier version over without reading its pickled file
        :raises IOError: the cookies are gone or no longer signed in
        """
        credentials.COOKIE.load( self.dataFile('cookie'), ignore_discard=True, ignore_expires=True )
        domains = sorted(c.domain for c in credentials.COOKIE if '.amazon.' in c.domain)
        if not domains:
            raise IOError('No Amazon cookies are stored')
        credentials.USERTLD = domains[0].split('.amazon.', 1)[1]
        from resources.lib.logon import AMlogon  # the sign-in itself builds on these tools
        logon = AMlogon()
        logon.credentials = credentials
        config = logon.fetchAppConfig()
        if not config or not config.get('customerId') or not config.get('accessToken'):
            raise IOError('The stored cookies are no longer signed in')
        logon._appConfig( config )
        self.credentials = credentials
        self.save( credentials )
        return credentials

    def save( self, obj ):
        """
        Keep the sign-in in the addon_data folder, as plain data
        """
        path = self.dataFile('data.json')
        with open(path, 'w', encoding='utf-8') as file:
            json.dump({name: getattr(obj, name, None) for name in AMaccess.STORED}, file)
        self.ownerOnly( path )
        self.delFile( self.dataFile('data.obj') )

    @staticmethod
    def ownerOnly( path ):
        """
        The file holds the tokens of the sign-in: where the system knows file permissions, other users cannot read it
        """
        try:
            os.chmod( path, 0o600 )
        except OSError:
            pass

    def saveCookie( self, obj ):
        """
        Save the cookie data to a file in addon_data folder.
        :param cookie_object obj: CookieJar object
        """
        obj.save( self.dataFile('cookie'), ignore_discard=True, ignore_expires=True )
        self.ownerOnly( self.dataFile('cookie') )

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
            'hideUnplayableSongs': 'true',
            'userAgent': ''
        }
        for key, value in data.items():
            self.setSetting( key, value )
        self.delFile( self.dataFile('searches.json') )
        self.clearOldSearches()
        self.resetCredentials()

    def resetCredentials( self ):
        """
        Remove Cookie and data object files
        """
        for name in ('cookie', 'data.json', 'data.obj', self.VMP_FLAG):
            self.delFile( self.dataFile(name) )

    def imageUrl( self, name ):
        """
        Path of an image the add-on brings along
        :param str name:    file name in resources/images
        """
        return '{}/resources/images/{}'.format( self.G['addonFolder'], name )

    def createList( self, data ):
        """
        Create list entries for Kodi menu
        :param array data:      content of Kodi menu
        """
        itemlist = []
        url = None
        for item in data:
            #self.log(item)
            isFolder = True
            if 'history' in item and not self.searchHistory(item['history']):
                continue
            title = self.getTranslation(item['txt'])
            li = xbmcgui.ListItem(label=title)
            linfo = li.getMusicInfoTag()
            linfo.setTitle(title)

            if 'img' in item:
                if 'http' in item['img']:
                    url = item['img']
                else:
                    url = self.imageUrl( item['img'] )
                li.setArt({
                    'icon':url,
                    'thumb':url,
                    'fanart':self.imageUrl(item['fanart']) if 'fanart' in item else url
                })
            url = '{}?mode={}'.format( self.G['addonBaseUrl'], str(item['fct']) )
            url += self.crumbsTo(title)
            itemlist.append((url, li, isFolder))
        # No content type: a menu holds no albums, and skins show the icon of such entries in the list.
        self.finalizeContent( self.G['addonHandle'], itemlist, '' )

    def setItemTags(self, listItem, tag_type:  str = 'music'):
        info_tag = ListItemInfoTag(listItem, tag_type)
        return info_tag

    def finalizeContent( self, addonHandle, itemlist, ctype ):
        """
        Finalization of Kodi list items
        :param str addonHandle: Kodi addon handle
        :param array itemlist:  Array of list items
        :param str ctype:       Content type ( songs / albums )
        """
        itemlist = [entry for entry in itemlist if entry]
        xbmcplugin.setPluginCategory(addonHandle, ' / '.join(self.crumbs()))
        xbmcplugin.addDirectoryItems(addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(addonHandle, ctype)
        xbmcplugin.endOfDirectory(addonHandle)

    def crumbs( self ):
        """
        The folders from the main menu down to the one being listed
        """
        return json.loads(self.G['addonArgs'].get('crumbs', ['[]'])[0])

    def crumbsTo( self, name=None ):
        """
        URL parameter that carries the path from the main menu into a folder
        :param str name:    label of the folder, None to stay in this one (next page)
        """
        crumbs = self.crumbs() + ([name] if name else [])
        # A single parameter, since Kodi keeps just one value per key of a plugin URL.
        return '&' + urlparse.urlencode({'crumbs': json.dumps(crumbs)}) if crumbs else ''

    def prepReqHeader( self, amzTarget ):
        """
        Request header preparation
        :param str amzTarget: API endpoint
        """
        head = {
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding' : 'gzip, deflate, br',
            'Accept-Language' : '{},en-US,en;q=0.8'.format( self.credentials.USERTLD ),
            'Accept-Charset'  : 'UTF-8,*;q=0.8',
            'X-Requested-With': 'XMLHttpRequest',
            'Host' :            'music.amazon.{}'.format( self.credentials.USERTLD ),
            'Origin' :          self.musicURL.format( self.credentials.USERTLD ),
            'csrf-token' :      self.credentials.CSRF_TOKEN,
            'csrf-rnd' :        self.credentials.CSRF_RND,
            'csrf-ts' :         self.credentials.CSRF_TS,
            'User-Agent' :      self.userAgent
        }
        # The web player sends its access token along with the CSRF tokens.
        if self.credentials.ACCESSTOKEN:
            head['Authorization'] = self.credentials.ACCESSTOKEN

        if amzTarget is not None:
            head['Content-Encoding'] = 'amz-1.0'
            head['Content-Type'] = 'application/json'
            head['X-Amz-Target'] = amzTarget

        return head