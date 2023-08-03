#!/usr/bin/env python
# -*- coding: utf-8 -*-

class AMmenu():
    """
    Amazon Media Main Menu Entries
        'txt'    - String ID for translation
        'fct'    - Function to call
        'img'    - Folder/Background image
        'search' - last searched items
    """
    @staticmethod
    def menuHome():
        return [{'txt':30023,'fct':'menuPlaylists',         'img':'playlists.jpg'},
                {'txt':30024,'fct':'menuAlbums',            'img':'albums.jpg'},
                {'txt':30022,'fct':'menuSongs',             'img':'songs.jpg'},
                {'txt':30008,'fct':'menuStations',          'img':'stations.jpg'},
                {'txt':30015,'fct':'getGenres',             'img':'genres.jpg'},
                {'txt':30027,'fct':'menuArtists',           'img':'artists.jpg'},
                {'txt':30041,'fct':'getNewRecom',           'img':'newrecom.jpg'},
                {'txt':30039,'fct':'testplaylist',          'img':'newrecom.jpg'}]

    @staticmethod
    def menuPlaylists():
        return [{'txt':30013,'fct':'searchPlayLists',       'img':'search.png'},
                {'txt':30032,'fct':'search1PlayLists',      'img':'search.png','search':'search1PlayLists'},
                {'txt':30033,'fct':'search2PlayLists',      'img':'search.png','search':'search2PlayLists'},
                {'txt':30034,'fct':'search3PlayLists',      'img':'search.png','search':'search3PlayLists'},
                {'txt':30003,'fct':'getRecomPlayLists',     'img':'playlists.jpg'},
                {'txt':30002,'fct':'getNewPlayLists',       'img':'playlists.jpg'},
                {'txt':30001,'fct':'getPopularPlayLists',   'img':'playlists.jpg'},
                {'txt':30018,'fct':'getFollowedPlayLists',  'img':'playlists.jpg'},
                {'txt':30019,'fct':'getOwnedPlaylists',     'img':'playlists.jpg'}]

    @staticmethod
    def menuAlbums():
        return [{'txt':30010,'fct':'searchAlbums',          'img':'search.png'},
                {'txt':30032,'fct':'search1Albums',         'img':'search.png','search':'search1Albums'},
                {'txt':30033,'fct':'search2Albums',         'img':'search.png','search':'search2Albums'},
                {'txt':30034,'fct':'search3Albums',         'img':'search.png','search':'search3Albums'},
                {'txt':30004,'fct':'getRecomAlbums',        'img':'albums.jpg'},
                {'txt':30012,'fct':'getPurAlbums',          'img':'albums.jpg'},
                {'txt':30007,'fct':'getAllAlbums',          'img':'albums.jpg'}]

    @staticmethod
    def menuSongs():
        return [{'txt':30011,'fct':'searchSongs',           'img':'search.png'},
                {'txt':30032,'fct':'search1Songs',          'img':'search.png','search':'search1Songs'},
                {'txt':30033,'fct':'search2Songs',          'img':'search.png','search':'search2Songs'},
                {'txt':30034,'fct':'search3Songs',          'img':'search.png','search':'search3Songs'},
                {'txt':30009,'fct':'getPurSongs',           'img':'songs.jpg'},
                {'txt':30006,'fct':'getAllSongs',           'img':'songs.jpg'},
                {'txt':30017,'fct':'getRecentlyPlayed',     'img':'songs.jpg'},
                {'txt':30021,'fct':'getRecentlyAddedSongs', 'img':'songs.jpg'}]

    @staticmethod
    def menuStations():
        return [{'txt':30016,'fct':'searchStations',        'img':'search.png'},
                {'txt':30032,'fct':'search1Stations',       'img':'search.png','search':'search1Stations'},
                {'txt':30033,'fct':'search2Stations',       'img':'search.png','search':'search2Stations'},
                {'txt':30034,'fct':'search3Stations',       'img':'search.png','search':'search3Stations'},
                {'txt':30005,'fct':'getRecomStations',      'img':'stations.jpg'},
                {'txt':30026,'fct':'getStations',           'img':'stations.jpg'},
                {'txt':30025,'fct':'getAllArtistsStations', 'img':'stations.jpg'}]

    @staticmethod
    def menuArtists():
        return [{'txt':30014,'fct':'searchArtist',          'img':'search.png'},
                {'txt':30032,'fct':'search1Artists',        'img':'search.png','search':'search1Artists'},
                {'txt':30033,'fct':'search2Artists',        'img':'search.png','search':'search2Artists'},
                {'txt':30034,'fct':'search3Artists',        'img':'search.png','search':'search3Artists'}]
