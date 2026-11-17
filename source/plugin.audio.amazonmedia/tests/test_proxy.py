"""The local proxy that hands the DASH manifest to inputstream.adaptive.

Kodi could not be quit while a connection to the proxy was still open: the
service waited for the handler thread, which sat in a read forever.
"""

import os
import socket
import threading
import time
import unittest

from .support import AddonTest, Kodi
from resources.lib.proxy import ProxyTCPD
from resources.lib.service import ServiceManager

MANIFEST = b'<?xml version="1.0"?><MPD/>'


def receive_all(sock, timeout=5):
    """Everything the server sends, and whether it closed the connection."""
    sock.settimeout(timeout)
    data = b''
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                return data, True
            data += chunk
    except socket.timeout:
        return data, False


class Manifest(AddonTest):
    def setUp(self):
        super().setUp()
        with open(os.path.join(Kodi.profile, 'song.mpd'), 'wb') as handle:
            handle.write(MANIFEST)
        self.proxy = ProxyTCPD()
        threading.Thread(target=self.proxy.serve_forever, daemon=True).start()

    def tearDown(self):
        self.proxy.shutdown()
        self.proxy.server_close()
        super().tearDown()

    def test_the_connection_is_closed_once_the_manifest_is_sent(self):
        client = socket.create_connection(('127.0.0.1', self.proxy.port))
        self.addCleanup(client.close)
        client.sendall(b'GET /mpd/song.mpd HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n')
        data, closed = receive_all(client)
        self.assertTrue(data.endswith(MANIFEST))
        self.assertTrue(closed, 'the proxy kept the connection open')

    def test_the_manifest_is_served_as_dash(self):
        client = socket.create_connection(('127.0.0.1', self.proxy.port))
        self.addCleanup(client.close)
        client.sendall(b'GET /mpd/song.mpd HTTP/1.0\r\n\r\n')
        headers = receive_all(client)[0].split(b'\r\n\r\n')[0].lower()
        self.assertIn(b'content-type: application/dash+xml', headers)


class Binding(AddonTest):
    def test_a_port_that_cannot_be_bound_is_reported_rather_than_retried_forever(self):
        self.patch(ProxyTCPD, 'server_bind', side_effect=OSError('no port'))
        raised = []

        def start():
            try:
                ProxyTCPD()
            except OSError as error:
                raised.append(error)

        starting = threading.Thread(target=start, daemon=True)
        starting.start()
        starting.join(2)
        self.assertFalse(starting.is_alive(), 'the proxy keeps trying to bind')
        self.assertEqual(len(raised), 1)


class Shutdown(AddonTest):
    def test_the_service_stops_while_a_client_is_still_connected(self):
        service = ServiceManager()
        idle = []

        def connect_and_say_nothing():
            idle.append(socket.create_connection(('127.0.0.1', service.proxy.port)))
            time.sleep(0.2)  # let the proxy accept it and start waiting for a request

        Kodi.on_wait_for_abort = connect_and_say_nothing
        running = threading.Thread(target=service.run, daemon=True)
        running.start()
        running.join(5)
        for client in idle:
            client.close()
        self.assertFalse(running.is_alive(), 'the service is still waiting for the idle client')


if __name__ == '__main__':
    unittest.main()
