#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

class API():
    """ Amazon Media APIs """
    def __init__(self):
        """
        Amazon API definitions
        amzUrl      = AmazonBaseUrl + region + /api/ + path
        amzTarget   = target
        """
        self.base = 'com.amazon.musicensembleservice.MusicEnsembleService.'
        self.getBrowseRecommendations = {
            'path':   'muse/legacy/getBrowseRecommendations',
            'target': '{}{}'.format(self.base,'getBrowseRecommendations')
        }
        self.lookup = {
            'path':   'muse/legacy/lookup',
            'target': '{}lookup'.format(self.base)
        }
        self.getAddToLibraryRecommendations = {
            'path':   'muse/legacy/getAddToLibraryRecommendations',
            'target': '{}getAddToLibraryRecommendations'.format(self.base)
        }
        self.getSimilarityRecommendations = {
            'path':   'muse/legacy/getSimilarityRecommendations',
            'target': '{}getSimilarityRecommendations'.format(self.base)
        }
        self.getMusicStoreRecommendations = {
            'path':   'muse/legacy/getMusicStoreRecommendations',
            'target': '{}getMusicStoreRecommendations'.format(self.base)
        }
        self.artistDetailCatalog = {
            'path':   'muse/artistDetailCatalog',
            'target': '{}artistDetailCatalog'.format(self.base),
            'method': 'POST'
        }
        self.getStationSections = {
            'path':   'muse/stations/getStationSections',
            'target': '{}getStationSectionsGet'.format(self.base),
            'method': 'GET'
        }
        self.artistDetailsMetadata = {
            'path':   'muse/artistDetailsMetadata',
            'target': '{}artistDetailsMetadata'.format(self.base)
        }
        self.getTopMusicEntities = { # playlists
            'path':   'muse/getTopMusicEntities',
            'target': '{}getTopMusicEntities'.format(self.base)
        }
        self.browseHierarchyV2 = {
            'path':   'muse/browseHierarchyV2',
            'target': '{}browseHierarchyV2'.format(self.base)
        }
        self.seeMore = {
            'path':   'muse/seeMore',
            'target': '{}seeMore'.format(self.base)
        }
        # new
        self.getHome = {
            'path':   'muse/getHome',
            'target': '{}getHome'.format(self.base)
        }
        # new end
        self.lookupStationsByStationKeys = {
            'path':   'muse/stations/lookupStationsByStationKeys',
            'target': '{}lookupStationsByStationKeys'.format(self.base)
        }
        self.base = 'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.'
        self.createQueue = { # genres
            'path':   'mpqs/voiceenabled/createQueue',
            'target': '{}createQueue'.format(self.base)
        }
        self.QueueGetNextTracks = { # genres
            'path':   'mpqs/voiceenabled/getNextTracks',
            'target': '{}getNextTracks'.format(self.base)
        }
        # get streaming url
        self.base = 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.'
        self.stream  = { # ASIN / COID
            'path':   'dmls/',
            'target': '{}getRestrictedStreamingURL'.format(self.base)
        }
        self.streamHLS = { # ASIN (hlsVersion:V3)
            'path':   'dmls/',
            'target': '{}getHLSManifest'.format(self.base)
        }
        self.streamDash = { # ASIN (musicDashVersionList: ["V1", "V2"])
            'path':   'dmls/',
            'target': '{}getDashManifestsV2'.format(self.base)
        }
        self.LicenseForPlaybackV2 = {
            'path':   'dmls/',
            'target': '{}getLicenseForPlaybackV2'.format(self.base)
        }
        self.getStreamingURLsWithFirstChunkV2 = { # HD playback?
            'path':   'dmls/',
            'target': '{}getStreamingURLsWithFirstChunkV2'.format(self.base)
        }
        self.search = {
            'path':   'textsearch/search/v1_1/',
            'target': 'com.amazon.tenzing.textsearch.v1_1.TenzingTextSearchServiceExternalV1_1.search'
        }
        # cirrus
        self.base = 'com.amazon.cirrus.libraryservice.'
        self.cirrus   = {
            'path'  : 'cirrus/',
            'target': None
        }
        self.cirrusV1 = {
            'path':   'cirrus/',
            'target': '{}CirrusLibraryServiceExternal.'.format(self.base)
        }
        self.cirrusV2 = {
            'path':   'cirrus/2011-06-01/',
            'target': '{}v2.CirrusLibraryServiceExternalV2.'.format(self.base)
        }
        self.cirrusV3 = {
            'path':   'cirrus/v3/',
            'target': '{}v3.CirrusLibraryServiceExternalV3.'.format(self.base)
        }
        self.V3getTracksByAsin = {
            'path':   'cirrus/v3/',
            'target': '{}getTracksByAsin'.format(self.cirrusV3['target'])
        }
        self.V3getTracks = {
            'path':   'cirrus/v3/',
            'target': '{}getTracks'.format(self.cirrusV3['target']),
            'operation': 'getTracks'
        }
        self.V3getTracksById = {
            'path':   'cirrus/v3/',
            'target': '{}getTracksById'.format(self.cirrusV3['target']),
            'operation': 'getTracksById'
        }
        # default
        self.base = 'com.amazon.musicplaylist.model.MusicPlaylistService.'
        self.getPlaylistsByIdV2 = {
            'path':   'playlists/',
            'target': '{}getPlaylistsByIdV2'.format(self.base)
        }
        self.getPubliclyAvailablePlaylistsById = {
            'path':   'playlists/',
            'target': '{}getPubliclyAvailablePlaylistsById'.format(self.base)
        }
        self.sociallySharePlaylist = {
            'path':   'playlists/',
            'target': '{}sociallySharePlaylist'.format(self.base)
        }
        self.getConfigurationV2 = {
            'path':   'playlists/',
            'target': '{}getConfigurationV2'.format(self.base)
        }
        self.getFollowedPlaylistsInLibrary = {
            'path':   'playlists/',
            'target': '{}getFollowedPlaylistsInLibrary'.format(self.base)
        }
        self.getOwnedPlaylistsInLibrary = {
            'path':   'playlists/',
            'target': '{}getOwnedPlaylistsInLibrary'.format(self.base)
        }
        self.base = 'com.amazon.nimblymusicservice.NimblyMusicService.'
        self.GetRecentTrackActivity = {
            'path':   'nimbly/',
            'target': '{}GetRecentTrackActivity'.format(self.base)
        }
        self.GetRecentActivity = {
            'path':   'nimbly/',
            'target': '{}GetRecentActivity'.format(self.base)
        }
        # soccer live
        self.base = 'com.amazon.eventvendingservice.EventVendingService.getProgramDetails'
        self.GetSoccerMain = {
            'path':   'eve/getPrograms',
            'target': self.base
        }
        self.GetSoccerProgramDetails = {
            'path':   'eve/getProgramDetails',
            'target': self.base
        }
        self.GetSoccerLiveURLs = {
            'path':   'amals/getLiveStreamingUrls',
            'target': 'com.amazon.amazonmusicaudiolocatorservice.model.AmazonMusicAudioLocatorServiceExternal.GetLiveStreamingURLs'
        }
        self.GetSoccerOnDemandURLs = {
            'path':   'amals/getOnDemandStreamingURLs',
            'target': 'com.amazon.amazonmusicaudiolocatorservice.model.AmazonMusicAudioLocatorServiceExternal.GetOnDemandStreamingURLs'
        }
        # podcasts
        # api/podcast
        # https://music-uk-dub.dub.proxy.amazon.com/EU/api/podcast/ " + t + "/visual"
        # https://music.amazon.com/" + e + "/api/podcast/" + t + "/visual"
        self.GetPodcast = {
            'path':   'podcast',
            'target': 'Podcast.Web.WidgetsInterface.LibraryShowsWidgetElement'
        }
        # "/podcasts/" + e.podcastId + "/" + encodeURI(e.podcastTitle),
        # "/podcasts/" + e.podcastId + "/episodes/" + e.episodeId + "/" + a,
        # "/podcasts/" + e.podcastId + "/" + encodeURI(e.podcastTitle),
        # preset: '{"podcastId":"' + e.podcastId + '","startAtEpisodeId":"' + e.episodeId + '"}',
        # e.PODCAST_LIBRARY_RECENTS_WIDGET = "Podcast.Web.WidgetsInterface.BookmarkedEpisodesWidgetElement",
        # e.PODCAST_LIBRARY_PLAYLIST_WIDGET = "Podcast.Web.WidgetsInterface.LibraryPlaylistWidgetElement",
        # e.PODCAST_LIBRARY_SHOWS_WIDGET = "Podcast.Web.WidgetsInterface.LibraryShowsWidgetElement"