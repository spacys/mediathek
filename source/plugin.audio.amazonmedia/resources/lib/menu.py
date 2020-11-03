#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .singleton import Singleton

class MainMenu(Singleton):
    """
    Amazon Media Main Menu Entries
        'txt'    - String ID for translation
        'fct'    - Function to call
        'img'    - Folder/Background image
        'search' - last searched items
    """
    def __init__(self,Settings):
        self.s = Settings # settings
    def menuHome(self):
        return [{'txt':30023,'fct':'menuPlaylists',         'img':'img_playlists'},
                {'txt':30024,'fct':'menuAlbums',            'img':'img_albums'},
                {'txt':30022,'fct':'menuSongs',             'img':'img_songs'},
                {'txt':30008,'fct':'menuStations',          'img':'img_stations'},
                {'txt':30015,'fct':'getGenres',             'img':'img_genres'},
                {'txt':30027,'fct':'menuArtists',           'img':'img_artists'},
                {'txt':30041,'fct':'getNewRecom',           'img':'img_newrecom'},
                {'txt':30035,'fct':'menuSoccer',            'img':'img_soccer'}]
    def menuPlaylists(self):
        return [{'txt':30013,'fct':'searchPlayLists',       'img':'img_search'},
                {'txt':30032,'fct':'search1PlayLists',      'img':'img_search','search':self.s.sPlayLists[0]},
                {'txt':30033,'fct':'search2PlayLists',      'img':'img_search','search':self.s.sPlayLists[1]},
                {'txt':30034,'fct':'search3PlayLists',      'img':'img_search','search':self.s.sPlayLists[2]},
                {'txt':30003,'fct':'getRecomPlayLists',     'img':'img_playlists'},
                {'txt':30002,'fct':'getNewPlayLists',       'img':'img_playlists'},
                {'txt':30001,'fct':'getPopularPlayLists',   'img':'img_playlists'},
                {'txt':30018,'fct':'getFollowedPlayLists',  'img':'img_playlists'},
                {'txt':30019,'fct':'getOwnedPlaylists',     'img':'img_playlists'}]
    def menuAlbums(self):
        return [{'txt':30010,'fct':'searchAlbums',          'img':'img_search'},
                {'txt':30032,'fct':'search1Albums',         'img':'img_search','search':self.s.sAlbums[0]},
                {'txt':30033,'fct':'search2Albums',         'img':'img_search','search':self.s.sAlbums[1]},
                {'txt':30034,'fct':'search3Albums',         'img':'img_search','search':self.s.sAlbums[2]},
                {'txt':30004,'fct':'getRecomAlbums',        'img':'img_albums'},
                {'txt':30012,'fct':'getPurAlbums',          'img':'img_albums'},
                {'txt':30007,'fct':'getAllAlbums',          'img':'img_albums'}]
    def menuSongs(self):
        return [{'txt':30011,'fct':'searchSongs',           'img':'img_search'},
                {'txt':30032,'fct':'search1Songs',          'img':'img_search','search':self.s.sSongs[0]},
                {'txt':30033,'fct':'search2Songs',          'img':'img_search','search':self.s.sSongs[1]},
                {'txt':30034,'fct':'search3Songs',          'img':'img_search','search':self.s.sSongs[2]},
                {'txt':30009,'fct':'getPurSongs',           'img':'img_songs'},
                {'txt':30006,'fct':'getAllSongs',           'img':'img_songs'},
                {'txt':30017,'fct':'getRecentlyPlayed',     'img':'img_songs'},
                {'txt':30021,'fct':'getRecentlyAddedSongs', 'img':'img_songs'}]
    def menuStations(self):
        return [{'txt':30016,'fct':'searchStations',        'img':'img_search'},
                {'txt':30032,'fct':'search1Stations',       'img':'img_search','search':self.s.sStations[0]},
                {'txt':30033,'fct':'search2Stations',       'img':'img_search','search':self.s.sStations[1]},
                {'txt':30034,'fct':'search3Stations',       'img':'img_search','search':self.s.sStations[2]},
                {'txt':30005,'fct':'getRecomStations',      'img':'img_stations'},
                {'txt':30026,'fct':'getStations',           'img':'img_stations'},
                {'txt':30025,'fct':'getAllArtistsStations', 'img':'img_stations'}]
    def menuArtists(self):
        return [{'txt':30014,'fct':'searchArtist',          'img':'img_search'},
                {'txt':30032,'fct':'search1Artists',        'img':'img_search','search':self.s.sArtists[0]},
                {'txt':30033,'fct':'search2Artists',        'img':'img_search','search':self.s.sArtists[1]},
                {'txt':30034,'fct':'search3Artists',        'img':'img_search','search':self.s.sArtists[2]}]
    def menuSoccer(self):
        return [{'txt':30036,'fct':'soccerBUND',            'img':'img_sBUND'},
                {'txt':30037,'fct':'soccerBUND2',           'img':'img_sBUND2'},
                {'txt':30038,'fct':'soccerDFBPOKAL',        'img':'img_sDFBPOKAL'},
                {'txt':30039,'fct':'soccerCHAMP',           'img':'img_sCHAMP'},
                {'txt':30040,'fct':'soccerSUPR',            'img':'img_sSUPR'}]
