#!/usr/bin/env python
# -*- coding: utf-8 -*-

class AMmenu():
    """
    Amazon Media Main Menu Entries
        'txt'     - String ID for translation
        'fct'     - Function to call
        'img'     - Folder/Background image
        'fanart'  - Background image, if it differs from 'img'
        'history' - search history, the entry is left out while it is empty
    """
    @staticmethod
    def menuHome():
        return [{'txt':30023,'fct':'menuPlaylists',         'img':'playlists.jpg'},
                {'txt':30024,'fct':'menuAlbums',            'img':'albums.jpg'},
                {'txt':30022,'fct':'menuSongs',             'img':'songs.jpg'},
                {'txt':30027,'fct':'menuArtists',           'img':'artists.jpg'},
                {'txt':30028,'fct':'getGenres',             'img':'genres.jpg'},
                {'txt':30029,'fct':'getStations',           'img':'stations.jpg'}]

    @staticmethod
    def menuPlaylists():
        return [{'txt':30042,'fct':'searchPlayLists',       'img':'search.png'},
                {'txt':30043,'fct':'searchHistoryPlayLists','img':'search.png','history':'PlayLists'},
                {'txt':30003,'fct':'getRecomPlayLists',     'img':'playlists.jpg'},
                {'txt':30002,'fct':'getNewPlayLists',       'img':'playlists.jpg'},
                {'txt':30001,'fct':'getPopularPlayLists',   'img':'playlists.jpg'},
                {'txt':30018,'fct':'getFollowedPlayLists',  'img':'playlists.jpg'},
                {'txt':30019,'fct':'getOwnedPlaylists',     'img':'playlists.jpg'}]

    @staticmethod
    def menuAlbums():
        return [{'txt':30042,'fct':'searchAlbums',          'img':'search.png'},
                {'txt':30043,'fct':'searchHistoryAlbums',  'img':'search.png','history':'Albums'},
                {'txt':30004,'fct':'getRecomAlbums',        'img':'albums.jpg'},
                {'txt':30002,'fct':'getNewAlbums',          'img':'albums.jpg'},
                {'txt':30001,'fct':'getPopularAlbums',      'img':'albums.jpg'},
                {'txt':30012,'fct':'getPurAlbums',          'img':'albums.jpg'},
                {'txt':30007,'fct':'getAllAlbums',          'img':'albums.jpg'}]

    @staticmethod
    def menuSongs():
        return [{'txt':30042,'fct':'searchSongs',           'img':'search.png'},
                {'txt':30043,'fct':'searchHistorySongs',   'img':'search.png','history':'Songs'},
                {'txt':30009,'fct':'getPurSongs',           'img':'songs.jpg'},
                {'txt':30006,'fct':'getAllSongs',           'img':'songs.jpg'},
                {'txt':30021,'fct':'getRecentlyAddedSongs', 'img':'songs.jpg'}]

    @staticmethod
    def menuArtists():
        return [{'txt':30042,'fct':'searchArtist',          'img':'search.png'},
                {'txt':30043,'fct':'searchHistoryArtists', 'img':'search.png','history':'Artists'},
                {'txt':30006,'fct':'getLibraryArtists',     'img':'artists.jpg'}]
