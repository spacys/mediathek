#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingTCPServer
from io import BytesIO
from gzip import GzipFile
import re, os, requests
from urllib.parse import urlparse, parse_qsl

import xbmc, xbmcvfs, xbmcaddon

class ProxyHTTPD(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'  # Allow keep-alive
    server_version = 'AmazonMadia/0.1'
    sessions = {}  # Keep-Alive sessions
    _purgeHeaders = [  # List of headers not to forward to the client
        'Transfer-Encoding',
        'Content-Encoding',
        'Content-Length',
        'Server',
        'Date'
    ]

    def log_message(self, *args):
        """Disable the BaseHTTPServer Log"""
        pass

    def log(self, msg, level=xbmc.LOGINFO):
        log_message = '[{}] {}'.format('AM Proxy', msg)
        xbmc.log(log_message, level)

    def _AdjustLocale(self, langCode, count=2, separator='-'):
        """Locale conversion helper"""

        try:
            p1, p2 = langCode.split('-')
        except:
            p1 = langCode
            p2 = langCode
        if 1 == count:
            return p1.lower()
        localeConversionTable = {
            'ar' + separator + '001': 'ar',
            'cmn' + separator + 'HANS': 'zh' + separator + 'HANS',
            'cmn' + separator + 'HANT': 'zh' + separator + 'HANT',
            'fr' + separator + 'CA': 'fr' + separator + 'Canada',
            'da' + separator + 'DK': 'da',
            'en' + separator + 'GB': 'en',
            'es' + separator + '419': 'es' + separator + 'Latinoamerica',
            'ja' + separator + 'JP': 'ja',
            'ko' + separator + 'KR': 'ko',
            'nb' + separator + 'NO': 'nb',
            'sv' + separator + 'SE': 'sv',
            'pt' + separator + 'BR': 'pt' + separator + 'Brazil'
        }
        new_lang = p1.lower() + ('' if p1 == p2 else separator + p2.upper())
        new_lang = new_lang if new_lang not in localeConversionTable.keys() else localeConversionTable[new_lang]
        return new_lang

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

    def _ForwardRequest(self, method, endpoint, headers, data, stream=False):
        """Forwards the request to the proper target"""
        # from resources.lib.network import MechanizeLogin
        # Create sessions for keep-alives and connection pooling
        self.log('_ForwardRequest')
        host = re.search('://([^/]+)/', endpoint)  # Try to extract the host from the URL
        if None is not host:
            host = host.group(1)
            if host not in self.sessions:
                self.sessions[host] = requests.Session()
            session = self.sessions[host]
        else:
            session = requests.Session()
        
        # cookie = MechanizeLogin()
        cookie = None
        if not cookie:
            self.log('[PS] Not logged in')
            self.send_error(440)
            return (None, None, None)

        if 'Host' in headers: del headers['Host']  # Forcibly strip the host (py3 compliance)
        self.log('[PS] Forwarding the {} request towards {}'.format(method.upper(), endpoint))
        r = session.request(method, endpoint, data=data, headers=headers, cookies=cookie, stream=stream, verify=self.server._s.verifySsl)
        return (r.status_code, r.headers, r if stream else r.content.decode('utf-8'))

    def _gzip(self, data=None, stream=False):
        """Compress the output data"""
        self.log('_gzip')
        out = BytesIO()
        f = GzipFile(fileobj=out, mode='w', compresslevel=5)
        if not stream:
            f.write(data)
            f.close()
            return out.getvalue()
        return (f, out)

    def _SendHeaders(self, code, headers):
        self.log('_SendHeaders')
        self.send_response(code)
        for k in headers:
            self.send_header(k, headers[k])
        self.end_headers()

    def _SendResponse(self, code, headers, data, gzip=False):
        """Send a response to the caller"""
        self.log('_SendResponse')
        # We don't use chunked or gunzipped transfers locally, so we removed the relative headers and
        # attach the contact length, before returning the response
        headers = {k: headers[k] for k in headers if k not in self._purgeHeaders}
        headers['Connection'] = 'Keep-Alive'
        data = data.encode('utf-8') if data else b''
        if gzip:
            data = self._gzip(data)
            headers['Content-Encoding'] = 'gzip'
        headers['Content-Length'] = len(data)

        self._SendHeaders(code, headers)
        self.wfile.write(data)

    @contextmanager
    def _PrepareChunkedResponse(self, code, headers):
        """Prep the stream for gzipped chunked transfers"""
        self.log('_PrepareChunkedResponse')
        self.log('[PS] Chunked transfer: prepping')
        headers = {k: headers[k] for k in headers if k not in self._purgeHeaders}
        headers['Connection'] = 'Keep-Alive'
        headers['Transfer-Encoding'] = 'chunked'
        headers['Content-Encoding'] = 'gzip'

        self._SendHeaders(code, headers)
        gzstream = self._gzip(stream=True)

        try:
            yield gzstream
        finally:
            gzstream[0].close()
            gzstream[1].close()

    def _SendChunk(self, gzstream, data=None):
        """Send a gzipped chunk"""
        self.log('_SendChunk')
        # Log('[PS] Chunked transfer: sending chunk', Log.DEBUG)
        if None is not data:
            gzstream[0].write(data.encode('utf-8'))
            gzstream[0].flush()
        chunk = gzstream[1].getvalue()
        gzstream[1].seek(0)
        gzstream[1].truncate()

        if 0 == len(chunk):
            return

        data = b'%s\r\n%s\r\n' % (hex(len(chunk))[2:].upper().encode(), chunk)
        self.wfile.write(data)

    def _EndChunkedTransfer(self, gzstream):
        """Terminate the transfer"""
        self.log('_EndChunkedTransfer')
        self.log('[PS] Chunked transfer: last chunks')
        gzstream[0].flush()
        gzstream[0].close()
        self._SendChunk(gzstream)
        gzstream[1].close()
        self.wfile.write(b'0\r\n\r\n')

    def do_POST(self):
        """Respond to POST requests"""
        self.log('do post')
        path, headers, data = self._ParseBaseRequest('POST')
        if None is path: return
        if ('gpr' == path[0]) and (2 == len(path)):
            return
            #self._AlterGPR(unquote(path[1]), headers, data)
        else:
            self.log('[PS] Invalid request received')
            self.send_error(501, 'Invalid request')

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
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-Length', str(size))
            self.end_headers()

            self.wfile.write(song.readBytes())
            song.close()
            #self._EndChunkedTransfer(gzstream)

        else:
            self.log('[PS] Invalid request received')
            self.send_error(501, 'Invalid request')

    def _AlterMPD(self, endpoint, headers, data):
        """ MPD alteration for better language parsing """

        # Extrapolate the base CDN url to avoid proxying data we don't need to
        url_parts = urlparse(endpoint)
        # baseurl = url_parts.scheme + '://' + url_parts.netloc + re.sub(r'[^/]+$', '', url_parts.path)

        # def _rebase(data):
        #     data = data.replace('<BaseURL>', '<BaseURL>' + baseurl)
        #     data = re.sub(r'(<SegmentTemplate\s+[^>]*?\s*media=")', r'\1' + baseurl, data)
        #     data = re.sub(r'(<SegmentTemplate\s+[^>]*?\s*initialization=")', r'\1' + baseurl, data)
        #     return data

        # # Start the chunked reception
        # status_code, headers, r = self._ForwardRequest('get', endpoint, headers, data, True)

        # with self._PrepareChunkedResponse(status_code, headers) as gzstream:
        #     if r.encoding is None:
        #         r.encoding = 'utf-8'
        #     buffer = ''
        #     bPeriod = False
        #     self.log('[PS] Loading MPD and rebasing as {}'.format(baseurl))
        #     for chunk in r.iter_content(chunk_size=1048576, decode_unicode=True):
        #         buffer += py2_decode(chunk)

        #         # Flush everything up to audio AdaptationSets as fast as possible
        #         pos = re.search(r'(<AdaptationSet[^>]*contentType="video"[^>]*>.*?</AdaptationSet>\s*)' if bPeriod else r'(<Period[^>]*>\s*)', buffer, flags=re.DOTALL)
        #         if pos:
        #             if 0 < pos.start(1):
        #                 self._SendChunk(gzstream, buffer[0:pos.start(1)])
        #             if not bPeriod:
        #                 bPeriod = True
        #                 self._SendChunk(gzstream, buffer[pos.start(1):pos.end(1)])
        #             else:
        #                 self._SendChunk(gzstream, _rebase(buffer[pos.start(1):pos.end(1)]))
        #             buffer = buffer[pos.end(1):]

        #     # Count the number of duplicates with the same ISO 639-1 codes
        #     self.log('[PS] Parsing languages')
        #     languages = []
        #     langCount = {}
        #     for lang in re.findall(r'<AdaptationSet[^>]*audioTrackId="([^"]+)"[^>]*>', buffer):
        #         if lang not in languages:
        #             languages.append(lang)
        #     for lang in languages:
        #         lang = lang[0:2]
        #         if lang not in langCount:
        #             langCount[lang] = 0
        #         langCount[lang] += 1

        #     # Send corrected AdaptationSets, one at a time through chunked transfer
        #     self.log('[PS] Altering <AdaptationSet>s')
        #     while True:
        #         pos = re.search(r'(<AdaptationSet[^>]*>)(.*?</AdaptationSet>)', buffer, flags=re.DOTALL)
        #         if None is pos:
        #             break
        #         # Log('[PS] AdaptationSet position: ([{}:{}], [{}:{}])'.format(pos.start(1), pos.end(1), pos.start(2), pos.end(2)))
        #         setTag = buffer[pos.start(1):pos.end(1)]
        #         self._SendChunk(gzstream, setTag)
        #         self._SendChunk(gzstream, _rebase(buffer[pos.start(2):pos.end(2)]))
        #         buffer = buffer[pos.end(2):]

        #     # Send the rest and signal EOT
        #     if 0 < len(buffer):
        #         self._SendChunk(gzstream, buffer)
        #     self._EndChunkedTransfer(gzstream)

class ProxyTCPD(ThreadingTCPServer):
    def __init__(self):
        """ Initialisation of the Proxy TCP server """
        from socket import socket, AF_INET, SOCK_STREAM
        sock = socket(AF_INET, SOCK_STREAM)

        while True:
            try:
                sock.bind(('127.0.0.1', 0))
                _, port = sock.getsockname()
                sock.close()
                ThreadingTCPServer.__init__(self, ('127.0.0.1', port), ProxyHTTPD)
                self.port = port  # Save the current binded port
                break
            except:
                pass
