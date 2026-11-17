#!/usr/bin/env python
# -*- coding: utf-8 -*-

class AMapi():
    """
    Amazon Media API definitions \n
    amzUrl      = AmazonBaseUrl + region + /api/ + path \n
    amzTarget   = target
    """
    @staticmethod
    def getAPI( amapi ):
        """
        Provides Amazon URL and Service endpoint
        :param str amapi: the requested API
        """
        if  amapi == 'APIlookup':
            s = {   'path':   'muse/legacy/lookup',
                    'target': 'com.amazon.musicensembleservice.MusicEnsembleService.lookup'
            }
        # get streaming url
        elif amapi == 'APIstreamDash': # ASIN (musicDashVersionList: ["V1", "V2"])
            s = {   'path':   'dmls/',
                    'target': 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getDashManifestsV2'
            }
        elif amapi == 'APIstreamCoid': # COID, the object id of a song in the personal library
            s = {   'path':   'dmls/',
                    'target': 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getStreamingURLs'
            }
        elif amapi == 'APILicenseForPlaybackV2':
            s = {   'path':   'dmls/',
                    'target': 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getLicenseForPlaybackV2'
            }
        elif amapi == 'APIV3getTracks':
            s = {   'path':   'cirrus/v3/',
                    'target': 'com.amazon.cirrus.libraryservice.v3.CirrusLibraryServiceExternalV3.getTracks'
            }
        elif amapi == 'APIV3getAlbums':
            s = {   'path':   'cirrus/v3/',
                    'target': 'com.amazon.cirrus.libraryservice.v3.CirrusLibraryServiceExternalV3.getAlbums'
            }
        else:
            raise Exception("No API provided!")

        return s
