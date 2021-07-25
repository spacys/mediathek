#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import threading
from time import time
import xbmc
from resources.lib.proxy import ProxyTCPD
from resources.lib.settings import Settings

class ServiceManager():
    def __init__(self):
        self.proxy  = ProxyTCPD()
        self.s      = Settings()
        self.s.log('Proxy Bound to 127.0.0.1:{}'.format(self.proxy.port))
        self.proxy_thread = threading.Thread(target=self.proxy.serve_forever)
        self.s.setSetting('proxy','127.0.0.1:{}'.format(self.proxy.port))
        self.monitor = xbmc.Monitor()

    def run(self):
        def _start_servers():
            self.proxy.server_activate()
            self.proxy.timeout = 1
            self.proxy_thread.start()
            self.s.log('Proxy Server started')

        def _stop_servers():
            self.proxy.server_close()
            self.proxy.shutdown()
            self.proxy_thread.join()
            self.s.setSetting('proxy','')
            self.s.log('Proxy Server stopped')
        
        #monitor = xbmc.Monitor()

        _start_servers()

        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(1):
                break

        _stop_servers()

if __name__ == '__main__':
    ServiceManager().run()
