"""
Python Sock tools: simple_http.py - a simple webserver
Copyright (C) 2016 GarethNelson

This file is part of python-sock-tools

python-sock-tools is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

python-sock-tools is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with python-sock-tools.  If not, see <http://www.gnu.org/licenses/>.

This module implements a toy http webserver where every URL returns a small HTML page.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

from socktools import tcp_sock
from socktools import http_mixin

static_page = """
<html>
<body>
Hello, this is a socktools webserver, yay!
</body>
</html>
"""

class MyServer(http_mixin.HTTPMixin,tcp_sock.TCPSock):
   """Simple http server

   This class implements a trivial http server with some static content.
   
   Note that unlike other protocols and sockets, when dealing with HTTP the msg_data object has a reply() method that must be used.

   """
   def handle_get(self,from_addr,msg_type,msg_data):
       """Handle HTTP GET requests
       
       The HTTP mixin represents requests as a special object with a reply() method that can be used to send a response.

       """
       http_req = msg_data
       path     = http_req.path
       http_req.reply(body=static_page)

   def get_default_handlers(self):
       handlers        = super(MyServer,self).get_default_handlers()
       handlers['GET'] = [self.handle_get]
       return handlers



if __name__=='__main__':
   import sys
   s = MyServer(bind=('127.0.0.1',31337))
   print 'Starting server...'
   s.start_server()
   print 'Hit ctrl-c to quit, hit http://localhost:31337 in a browser to test'
   while True: eventlet.greenthread.sleep(30)
