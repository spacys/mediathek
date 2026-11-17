"""Stand-ins for the Kodi modules, so that the add-on can run outside Kodi.

They record what the add-on asks Kodi to do. That record is what the tests
look at, rather than the add-on's internals.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ElementTree
from unittest import mock
from urllib.parse import parse_qsl, quote, urlencode, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ADDON_ID = 'plugin.audio.amazonmedia'
BASE_URL = 'plugin://{}/'.format(ADDON_ID)
HANDLE = 1

# The add-on does not ship Kodi's own strings; the few it uses are named here.
KODI_STRINGS = {257: 'Error', 19033: 'Information'}

LANGUAGE_FOLDER = os.path.join(ROOT, 'resources', 'language')
SOURCE_LANGUAGE = 'en_gb'
# Every language the add-on ships, as the language folder holds them.
LANGUAGES = sorted(name[len('resource.language.'):] for name in os.listdir(LANGUAGE_FOLDER)
                   if name.startswith('resource.language.'))
TRANSLATIONS = [language for language in LANGUAGES if language != SOURCE_LANGUAGE]
# Had nothing been found, the tests that go through the languages would pass without looking at one.
assert SOURCE_LANGUAGE in LANGUAGES and TRANSLATIONS, LANGUAGES


def _english():
    path = os.path.join(LANGUAGE_FOLDER, 'resource.language.%s' % SOURCE_LANGUAGE, 'strings.po')
    with open(path, encoding='utf-8') as handle:
        return {int(number): text
                for number, text in re.findall(r'msgctxt "#(\d+)"\nmsgid "(.*)"', handle.read())}


ENGLISH = _english()


def text(number):
    """What Kodi shows for one of the add-on's strings."""
    return ENGLISH[number]


def _defaults():
    """The settings as Kodi sets them up from settings.xml for a new install."""
    settings = ElementTree.parse(os.path.join(ROOT, 'resources', 'settings.xml')).getroot()
    return {setting.get('id'): setting.findtext('default') or '' for setting in settings.iter('setting') if setting.get('id')}


DEFAULTS = _defaults()


class Kodi:
    """Everything the add-on asked of Kodi since the last reset."""
    settings = {}
    profile = None
    log = []
    builtins = []
    notifications = []
    progress = []
    directories = []
    items = []
    category = None
    content = None
    typed = ''
    headings = []
    on_wait_for_abort = None
    build_version = '22.0'


# xbmc
xbmc = types.ModuleType('xbmc')
xbmc.LOGDEBUG, xbmc.LOGINFO, xbmc.LOGWARNING, xbmc.LOGERROR = 0, 1, 2, 4
xbmc.log = lambda msg, level=xbmc.LOGDEBUG: Kodi.log.append((level, msg))
xbmc.executebuiltin = lambda command, wait=False: Kodi.builtins.append(command)
xbmc.sleep = lambda milliseconds: None
xbmc.getLocalizedString = lambda number: KODI_STRINGS.get(number, '')
xbmc.getInfoLabel = lambda label: {'System.BuildVersion': Kodi.build_version}.get(label, '')
xbmc.getCondVisibility = lambda condition: condition in Kodi.conditions


class _Monitor:
    def abortRequested(self):
        return False

    def waitForAbort(self, timeout=0):
        if Kodi.on_wait_for_abort:
            Kodi.on_wait_for_abort()
        return True


class _PlayList:
    def __init__(self, kind):
        pass

    def clear(self):
        pass


class _Player:
    def stop(self):
        pass


class _Keyboard:
    """Confirms with whatever the test put into Kodi.typed."""

    def __init__(self, *args):
        pass

    def setHeading(self, heading):
        Kodi.headings.append(heading)

    def setDefault(self, text):
        pass

    def setHiddenInput(self, hidden):
        pass

    def doModal(self):
        pass

    def isConfirmed(self):
        return True

    def getText(self):
        return Kodi.typed


xbmc.Monitor, xbmc.PlayList, xbmc.Player, xbmc.Keyboard = _Monitor, _PlayList, _Player, _Keyboard

# xbmcgui
xbmcgui = types.ModuleType('xbmcgui')
xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR = 'info', 'warning', 'error'


class _Dialog:
    def yesnocustom(self, *args, **kwargs):
        return 1

    def notification(self, heading, message, icon='info', time=5000, sound=True):
        Kodi.notifications.append({'heading': heading, 'message': message, 'icon': icon})


class _DialogProgress:
    def create(self, heading, message=''):
        Kodi.progress.append(message)

    def iscanceled(self):
        return False

    def close(self):
        pass


class _ListItem:
    def __init__(self, label='', **kwargs):
        self.label = label
        self.path = kwargs.get('path')
        self.properties = {}
        self.art = {}
        self.info = {}

    def setArt(self, art):
        # Kodi refuses anything but text with a TypeError.
        if not all(isinstance(value, str) for value in art.values()):
            raise TypeError('setArt takes text only')
        self.art.update(art)

    def setProperty(self, key, value):
        self.properties[key] = value

    def getMusicInfoTag(self):
        return types.SimpleNamespace(setTitle=lambda title: None)

    def setContentLookup(self, enable):
        pass

    def setMimeType(self, mimetype):
        pass

    def addContextMenuItems(self, items):
        self.context_menu = list(items)


xbmcgui.Dialog, xbmcgui.DialogProgress, xbmcgui.ListItem = _Dialog, _DialogProgress, _ListItem

# xbmcaddon
xbmcaddon = types.ModuleType('xbmcaddon')


class _Addon:
    def __init__(self, addon_id=None):
        pass

    def getSetting(self, key):
        return Kodi.settings.get(key, '')

    def setSetting(self, key, value):
        Kodi.settings[key] = value

    def getAddonInfo(self, key):
        return {'id': ADDON_ID, 'name': 'Amazon Media', 'path': ROOT}[key]

    def getLocalizedString(self, number):
        return ENGLISH.get(number, '')


xbmcaddon.Addon = _Addon

# xbmcplugin
xbmcplugin = types.ModuleType('xbmcplugin')
xbmcplugin.endOfDirectory = lambda handle, succeeded=True, *args, **kwargs: \
    Kodi.directories.append((handle, succeeded))
xbmcplugin.addDirectoryItems = lambda handle, items, total=0: Kodi.items.extend(items)
xbmcplugin.setContent = lambda handle, content: setattr(Kodi, 'content', content)
xbmcplugin.setPluginCategory = lambda handle, category: setattr(Kodi, 'category', category)
xbmcplugin.setResolvedUrl = lambda handle, succeeded, item: None

# xbmcvfs
xbmcvfs = types.ModuleType('xbmcvfs')


def _translate_path(path):
    path = path.replace('special://profile/addon_data/{}'.format(ADDON_ID), Kodi.profile)
    return path.replace('special://home/addons/{}'.format(ADDON_ID), ROOT)


class _File:
    def __init__(self, path):
        with open(path, 'rb') as handle:
            self._data = handle.read()

    def size(self):
        return len(self._data)

    def readBytes(self):
        return self._data

    def close(self):
        pass


xbmcvfs.translatePath, xbmcvfs.File = _translate_path, _File

# infotagger, a script module from the Kodi repository
infotagger = types.ModuleType('infotagger')
infotagger_listitem = types.ModuleType('infotagger.listitem')


class _ListItemInfoTag:
    def __init__(self, listitem, tag_type='music'):
        self.listitem = listitem
        listitem.tag_type = tag_type

    def set_info(self, info):
        self.listitem.info = {key: value for key, value in info.items() if value is not None}


infotagger_listitem.ListItemInfoTag = _ListItemInfoTag
infotagger.listitem = infotagger_listitem

sys.modules.update({'xbmc': xbmc, 'xbmcgui': xbmcgui, 'xbmcaddon': xbmcaddon,
                    'xbmcplugin': xbmcplugin, 'xbmcvfs': xbmcvfs,
                    'infotagger': infotagger, 'infotagger.listitem': infotagger_listitem})

from resources.lib.singleton import _Singleton  # noqa: E402  (needs the modules above)


def invoke(query=''):
    """Start a new plugin call with the arguments Kodi hands it, e.g. invoke('mode=getPurAlbums').

    Kodi runs every call in a fresh interpreter, so nothing the add-on built
    for an earlier call may carry over.
    """
    _Singleton._instances.clear()
    sys.argv = [BASE_URL, str(HANDLE), '?' + query]


def clicked(url):
    """The query Kodi hands the plugin when a listed URL is opened.

    Kodi keeps the options of a plugin URL in a std::map: one value per key,
    sorted by key, and encodes them anew.
    """
    options = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    return urlencode(sorted(options.items()), quote_via=quote)


def signed_in(credentials, tier='PRIME'):
    """Fill the credentials as a successful sign-in on amazon.de leaves them."""
    credentials.ACCESSTOKEN = 'Bearer access-token'
    credentials.CSRF_TOKEN, credentials.CSRF_TS, credentials.CSRF_RND = 'csrf', '1', '2'
    credentials.DEVICEID, credentials.DEVICETYPE = 'device-id', 'device-type'
    credentials.CUSTOMERID, credentials.MARKETPLACEID = 'customer-id', 'marketplace-id'
    credentials.MUSICTERRITORY, credentials.CUSTOMERLANG = 'DE', 'de'
    credentials.LOCALE, credentials.REGION, credentials.USERTLD = 'de_DE', 'EU', 'de'
    credentials.ACCESSTYPE = tier
    return credentials


class Response:
    """A requests response, as far as the add-on reads it."""

    def __init__(self, body, status=200):
        self.text = body if isinstance(body, str) else json.dumps(body)
        self.status_code = status
        self.reason = 'OK' if status == 200 else 'Error'

    def json(self):
        return json.loads(self.text)


class AddonTest(unittest.TestCase):
    """Starts every test as a fresh plugin call with the default settings."""

    def setUp(self):
        Kodi.profile = tempfile.mkdtemp()
        Kodi.settings = dict(DEFAULTS)
        for record in (Kodi.log, Kodi.builtins, Kodi.notifications, Kodi.progress,
                       Kodi.directories, Kodi.items):
            del record[:]
        Kodi.typed = ''
        del Kodi.headings[:]
        Kodi.category = None
        Kodi.content = None
        Kodi.on_wait_for_abort = None
        Kodi.build_version = '22.0'
        Kodi.conditions = {'System.Platform.Android'}
        invoke()
        # The GraphQL interface is asked first; a test of the older interfaces has it fail.
        from resources.lib import gql
        self.gql = self.patch(gql.AMgql, 'query', side_effect=gql.GqlError('not asked in this test'))

    def tearDown(self):
        shutil.rmtree(Kodi.profile, ignore_errors=True)

    def patch(self, target, attribute, *args, **kwargs):
        """mock.patch.object for the rest of the test."""
        patcher = mock.patch.object(target, attribute, *args, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()
