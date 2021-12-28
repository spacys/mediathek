#!/usr/bin/env python
# -*- coding: utf-8 -*-

from resources.lib.singleton import Singleton
from resources.lib.tools import AMtools
import xbmcgui
import xbmcplugin

class AMmenu(Singleton):
    def __init__(self):
        self._t = AMtools()
    """
        Amazon Media Main Menu Entries
            'txt'    - String ID for translation
            'fct'    - Function to call
            'img'    - Folder/Background image
            'search' - last searched items
    """
    def menuHome(self):
        return [{'txt':30023,'fct':'menuPlaylists',         'img':'img_playlists'},
                {'txt':30024,'fct':'menuAlbums',            'img':'img_albums'},
                {'txt':30022,'fct':'menuSongs',             'img':'img_songs'},
                {'txt':30008,'fct':'menuStations',          'img':'img_stations'},
                {'txt':30015,'fct':'getGenres',             'img':'img_genres'},
                {'txt':30027,'fct':'menuArtists',           'img':'img_artists'},
                {'txt':30041,'fct':'getNewRecom',           'img':'img_newrecom'}#,
                #{'txt':30035,'fct':'menuSoccer',            'img':'img_soccer'}
                ]
    def menuPlaylists(self):
        return [{'txt':30013,'fct':'searchPlayLists',       'img':'img_search'},
                {'txt':30032,'fct':'search1PlayLists',      'img':'img_search','search':'search1PlayLists'},
                {'txt':30033,'fct':'search2PlayLists',      'img':'img_search','search':'search2PlayLists'},
                {'txt':30034,'fct':'search3PlayLists',      'img':'img_search','search':'search3PlayLists'},
                {'txt':30003,'fct':'getRecomPlayLists',     'img':'img_playlists'},
                {'txt':30002,'fct':'getNewPlayLists',       'img':'img_playlists'},
                {'txt':30001,'fct':'getPopularPlayLists',   'img':'img_playlists'},
                {'txt':30018,'fct':'getFollowedPlayLists',  'img':'img_playlists'},
                {'txt':30019,'fct':'getOwnedPlaylists',     'img':'img_playlists'} #,
                # {'txt':30019,'fct':'showLibraryPlaylists',  'img':'img_soccer'}, # TEST ONLY - playlsit new
                # {'txt':30019,'fct':'getPodcasts',  'img':'img_soccer'}
                ]
    def menuAlbums(self):
        return [{'txt':30010,'fct':'searchAlbums',          'img':'img_search'},
                {'txt':30032,'fct':'search1Albums',         'img':'img_search','search':'search1Albums'},
                {'txt':30033,'fct':'search2Albums',         'img':'img_search','search':'search2Albums'},
                {'txt':30034,'fct':'search3Albums',         'img':'img_search','search':'search3Albums'},
                {'txt':30004,'fct':'getRecomAlbums',        'img':'img_albums'},
                {'txt':30012,'fct':'getPurAlbums',          'img':'img_albums'},
                {'txt':30007,'fct':'getAllAlbums',          'img':'img_albums'}]
    def menuSongs(self):
        return [{'txt':30011,'fct':'searchSongs',           'img':'img_search'},
                {'txt':30032,'fct':'search1Songs',          'img':'img_search','search':'search1Songs'},
                {'txt':30033,'fct':'search2Songs',          'img':'img_search','search':'search2Songs'},
                {'txt':30034,'fct':'search3Songs',          'img':'img_search','search':'search3Songs'},
                {'txt':30009,'fct':'getPurSongs',           'img':'img_songs'},
                {'txt':30006,'fct':'getAllSongs',           'img':'img_songs'},
                {'txt':30017,'fct':'getRecentlyPlayed',     'img':'img_songs'},
                {'txt':30021,'fct':'getRecentlyAddedSongs', 'img':'img_songs'}]
    def menuStations(self):
        return [{'txt':30016,'fct':'searchStations',        'img':'img_search'},
                {'txt':30032,'fct':'search1Stations',       'img':'img_search','search':'search1Stations'},
                {'txt':30033,'fct':'search2Stations',       'img':'img_search','search':'search2Stations'},
                {'txt':30034,'fct':'search3Stations',       'img':'img_search','search':'search3Stations'},
                {'txt':30005,'fct':'getRecomStations',      'img':'img_stations'},
                {'txt':30026,'fct':'getStations',           'img':'img_stations'},
                {'txt':30025,'fct':'getAllArtistsStations', 'img':'img_stations'}]
    def menuArtists(self):
        return [{'txt':30014,'fct':'searchArtist',          'img':'img_search'},
                {'txt':30032,'fct':'search1Artists',        'img':'img_search','search':'search1Artists'},
                {'txt':30033,'fct':'search2Artists',        'img':'img_search','search':'search2Artists'},
                {'txt':30034,'fct':'search3Artists',        'img':'img_search','search':'search3Artists'}]
    def menuSoccer(self):
        return [{'txt':30036,'fct':'soccerBUND',            'img':'img_sBUND'},
                {'txt':30037,'fct':'soccerBUND2',           'img':'img_sBUND2'},
                {'txt':30038,'fct':'soccerDFBPOKAL',        'img':'img_sDFBPOKAL'},
                {'txt':30039,'fct':'soccerCHAMP',           'img':'img_sCHAMP'},
                {'txt':30040,'fct':'soccerSUPR',            'img':'img_sSUPR'}]

    def createList(self,data,dynentry=False,soccer=False):
        """ Create list entries for Kodi menu """
        itemlist = []
        url = None
        for item in data:
            #self._t.log(item)
            isFolder = True
            if dynentry and 'search' in item and self._t.getSetting(item['search']) == '':
                continue
            # if soccer:
            if soccer or ('special' in item and item['special'] == 'newrecom'):
                title = item['txt']
            else:
                title = self._t.getTranslation(item['txt'])

            if dynentry and 'search' in item:
                title += self._t.getSetting(item['search'])
            li = xbmcgui.ListItem(label=title)
            li.setInfo(type="music", infoLabels={"title": title})
            if 'img' in item:
                if 'http' in item['img']:
                    url = item['img']
                else:
                    url = '{}/resources/images/{}'.format(self._t.addonFolder, self._t.getSetting(item['img']) )
                li.setArt({'icon':url,'thumb':url,'fanart':url,'poster':url,'banner':url,'landscape':url})
            url = '{}?mode={}'.format(self._t.addonBaseUrl,str(item['fct']))
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
        self.finalizeContent(itemlist,'albums')

    def finalizeContent(self,itemlist,ctype):
        """ finalization of all list items """
        xbmcplugin.addDirectoryItems(self._t.addonHandle, itemlist, len(itemlist))
        xbmcplugin.setContent(self._t.addonHandle, ctype)
        xbmcplugin.endOfDirectory(self._t.addonHandle)