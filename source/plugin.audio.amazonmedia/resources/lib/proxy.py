#!/usr/bin/env python
# -*- coding: utf-8 -*-
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingTCPServer
import json, os, re, time
from urllib.parse import urlparse, parse_qsl

import requests
import xbmc, xbmcgui, xbmcvfs, xbmcaddon

class ProxyHTTPD(BaseHTTPRequestHandler):
    # HTTP/1.0, so the client closes the connection after the manifest it asked
    # for. Kept open, the handler thread would sit in a read until Kodi exits.
    protocol_version = 'HTTP/1.0'
    server_version = 'AmazonMedia/0.1'

    def log_message(self, *args):
        """Disable the BaseHTTPServer Log"""
        pass

    def log(self, msg, level=xbmc.LOGINFO):
        log_message = '[{}] {}'.format('AM Proxy', msg)
        xbmc.log(log_message, level)

    def _ParseBaseRequest(self, method):
        """Return path, headers and post data commonly required by all methods"""
        # self.log('_ParseBaseRequest')
        # path = py2_decode(urlparse(self.path).path[1:])  # Get URI without the trailing slash
        path = urlparse(self.path).path[1:]  # Get URI without the trailing slash
        path = path.split('/')  # license/<asin>/<ATV endpoint>
        # self.log('[PS] Requested {} path {}'.format(method, path))
        # Retrieve headers and data
        headers = {k: self.headers[k] for k in self.headers if k not in ['host', 'content-length']}
        data_length = self.headers.get('content-length')
        data = {k: v for k, v in parse_qsl(self.rfile.read(int(data_length)))} if data_length else None
        return (path, headers, data)

    def do_GET(self):
        """Respond to GET requests"""
        # self.log('do get')
        path, head, data = self._ParseBaseRequest('GET')
        if path is None:
            return
        # self.log(path[0])
        # self.log(head)

        if (path[0] == 'mpd') and (2 == len(path)):
            #self._AlterMPD(unquote(path[1]), head, data)
            
            _addonUDatFo = xbmcvfs.translatePath('special://profile/addon_data/{}'.format(xbmcaddon.Addon().getAddonInfo('id')))
            song = '{}{}song.mpd'.format(_addonUDatFo,os.sep)
            # song = xbmcvfs.translatePath(song).decode('utf-8')
            song = xbmcvfs.File(song)
            size = song.size()
            # self.log('Song size: ' + str(size))

            self.send_response(200)
            self.send_header('Content-type', 'application/dash+xml')
            self.send_header('Content-Length', str(size))
            self.end_headers()

            self.wfile.write(song.readBytes())
            song.close()
            #self._EndChunkedTransfer(gzstream)

        else:
            self.log('[PS] Invalid request received')
            self.send_error(501, 'Invalid request')

    # Only Amazon Music is passed on to, whatever a local client asks for.
    LICENSE_HOST = re.compile(r'^music\.amazon\.[a-z]{2,3}(\.[a-z]{2})?$')
    # Headers of the hop to the proxy, which requests sets anew for the hop to Amazon.
    HOP_HEADERS = ('host', 'content-length', 'connection', 'accept-encoding', 'transfer-encoding')
    VMP_FLAG = 'vmp-unverified'

    def do_POST(self):
        """
        Pass the license request of inputstream.adaptive on to Amazon unchanged. \n
        inputstream.adaptive does not tell why a license was refused. The web player reads the
        reason: after VMP_VALIDATION_FAILED it asks for its manifests as an unverified client.
        """
        parsed = urlparse(self.path)
        target = dict(parse_qsl(parsed.query)).get('url', '')
        host = urlparse(target)
        if parsed.path != '/license' or host.scheme != 'https' or not self.LICENSE_HOST.match(host.hostname or ''):
            self.log('[PS] Invalid request received')
            self.send_error(501, 'Invalid request')
            return

        length = int(self.headers.get('content-length') or 0)
        body = self.rfile.read(length) if length else b''
        headers = {k: self.headers[k] for k in self.headers if k.lower() not in self.HOP_HEADERS}
        try:
            resp = requests.post(target, headers=headers, data=body, timeout=30)
        except requests.RequestException as error:
            self.log('[PS] License request failed: {}'.format(error), xbmc.LOGERROR)
            self.send_error(502, 'License request failed')
            return

        if resp.status_code != 200:
            self._licenseRefused(resp)

        self.send_response(resp.status_code)
        self.send_header('Content-type', resp.headers.get('Content-Type', 'application/json'))
        self.send_header('Content-Length', str(len(resp.content)))
        self.end_headers()
        self.wfile.write(resp.content)

    # When the user was last told about a refusal; every song of a playlist is refused alike.
    lastTold = 0

    def _licenseRefused(self, resp):
        """Log why Amazon refused the license, tell the user and remember a missing Verified Media Path"""
        try:
            reason = json.loads(resp.text).get('denialReason')
        except (ValueError, AttributeError):
            reason = None
        self.log('[PS] License refused: {} {}'.format(resp.status_code, reason or resp.text[:300]), xbmc.LOGWARNING)
        addon = xbmcaddon.Addon()
        if reason == 'VMP_VALIDATION_FAILED':
            folder = xbmcvfs.translatePath('special://profile/addon_data/{}'.format(addon.getAddonInfo('id')))
            flag = os.path.join(folder, self.VMP_FLAG)
            told = '{}\n{}'.format(reason, self.headers.get('User-Agent', ''))
            try:
                with open(flag) as handle:
                    if handle.read() == told:
                        return
            except (IOError, OSError):
                pass
            with open(flag, 'w') as handle:
                handle.write(told)
            # The song that is playing was asked for as a verified client; the next one is not.
            message = addon.getLocalizedString(30080)
        elif reason == 'UNTRUSTED_DEVICE_CERTIFICATE':
            # Amazon does not trust the Widevine library Kodi uses, an outdated one for instance.
            message = addon.getLocalizedString(30082)
        else:
            message = addon.getLocalizedString(30081).format(reason or resp.status_code)
        # The unencrypted start of a song still plays, so without a word the song just seems to stop.
        if time.time() - ProxyHTTPD.lastTold > 60:
            ProxyHTTPD.lastTold = time.time()
            xbmcgui.Dialog().notification(addon.getAddonInfo('name'), message, xbmcgui.NOTIFICATION_ERROR, 15000)

class ProxyTCPD(ThreadingTCPServer):
    # As ThreadingHTTPServer does it: server_close() waits for every handler
    # thread otherwise, which holds up the shutdown of Kodi.
    daemon_threads = True

    def __init__(self):
        """ Initialisation of the Proxy TCP server on a free port """
        ThreadingTCPServer.__init__(self, ('127.0.0.1', 0), ProxyHTTPD)
        self.port = self.server_address[1]
