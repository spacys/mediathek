#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import threading
#from time import time
import xbmc
import xbmcaddon
import sys
from resources.lib.proxy import ProxyTCPD

class ServiceManager():
    def __init__(self):
        self.addon      = xbmcaddon.Addon()
        self.addonName  = self.addon.getAddonInfo('name')
        self.proxy      = ProxyTCPD()
        self.log('Proxy Bound to 127.0.0.1:{}'.format(self.proxy.port))
        self.proxy_thread = threading.Thread(target=self.proxy.serve_forever)
        self.setSetting('proxy','127.0.0.1:{}'.format(self.proxy.port))

    def setSetting(self,oProp,val):
        self.addon.setSetting(oProp,val)

    def log(self, msg=None, level=xbmc.LOGINFO):
        fct_name  = sys._getframe(1).f_code.co_name
        lin_nmbr  = sys._getframe(1).f_lineno
        if msg:
            msg = '\n{}'.format(msg)
        else:
            msg = ''
        log_message = '[{}] {} : {}{}'.format(self.addonName, fct_name, lin_nmbr,msg)
        xbmc.log(log_message, level)

    def run(self):
        def _start_servers():
            self.proxy.server_activate()
            self.proxy.timeout = 1
            self.proxy_thread.start()
            self.monitor = xbmc.Monitor()
            self.log('Proxy Server started')

        def _stop_servers():
            self.proxy.server_close()
            self.proxy.shutdown()
            self.proxy_thread.join()
            self.setSetting('proxy','')
            self.log('Proxy Server stopped')
        
        _start_servers()

        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(1):
                break

        _stop_servers()

if __name__ == '__main__':
    ServiceManager().run()
