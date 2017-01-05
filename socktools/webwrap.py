"""
Python Sock tools: webwrap.py - Wraps web.py inside of eventlet
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

Often it makes sense to run an internal webserver for administration purposes, it also makes sense to use the existing implementation.

This module provides a simple wrapper around web.py inside eventlet. The wrapper is intended to be used inside of daemon processses but is useful in other places too.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

from eventlet import wsgi
import socket
import web

def static_page(page_content,mime_type='text/html'):
    """ Generate and return a URL handler for static content

    This function uses a bit of metaprogramming black magic and returns a web.py URL handler for arbitrary static content

    Returns:
       object: the URL handler
    """
    class page:
       def GET(self):
           web.header('Content-Length', str(page.content_len))
           web.header('Content-Type',mime_type)
           return page_content
    page.content_len = len(page_content)
    return page

class WebWrap(object):
   """A light wrapper around web.py and eventlet.wsgi

   This class is intended for providing a simple embedded webserver inside of daemon processes (or elsewhere).

   After configuring URLs, simply run start_server() to start it up.
   
   Warning:
      You must not use a physical socket from one of the socktools classes here.

   Keyword args:
      urls (dict): Map URL paths to URL handlers, see web.py documentation
      physical_sock (socket.socket): If not None, the existing physical socket to listen on
      listen_on (tuple): A tuple of (interface_ip,port) that the webserver should listen on

   """
   def __init__(self,urls={},physical_sock=None,listen_on=('0.0.0.0',8080)):
       self.urls          = self.get_default_urls()
       self.urls.update(urls)

       if physical_sock is None:
          self.physical_sock = eventlet.listen(listen_on)
       else:
          self.physical_sock = physical_sock

       self.url_map = self.get_url_map()
       self.pool    = eventlet.GreenPool(10) # we don't technically NEED this, but it makes things more uniform
       self.web_app = None
   def get_wsgifunc(self):
       """ Return a WSGI-compatible function
       
       In the default implementation this returns the WSGI function from a web.py app

       """
       if self.web_app is None:
          self.web_app = web.application(self.url_map,globals())
       return self.web_app.wsgifunc()
   def get_default_urls(self):
       """ Return the default URL mappings

       Override this in your app. The default implementation returns a single URL for / which returns a bit of static text

       Returns:
          dict: a dict mapping web.py URLs to web.py URL handlers
       """
       return {'/':static_page('socktools webwrap.py seems to be working')}
   def get_url_map(self):
       """ Generates a URL map for this webserver
       
       To integrate better with the rest of socktools, WebWrap offers a get_default_urls() method that returns a dict.

       Unfortunately web.py requires a tuple, so this method generates that tuple.

       Returns:
          tuple: the web.py compatible URL map
       """
       retval = []
       for k,v in self.urls.items():
           retval.append(k)
           retval.append(v)
       return tuple(retval)
   def server_thread(self):
       """ Used internally - server greenlet
       """
       wsgi.server(self.physical_sock, self.get_wsgifunc())
   def start_server(self):
       """ Starts the webserver in a new greenlet

       Call this after setting up URLs etc and the webserver will start answering requests.
       """
       self.pool.spawn_n(self.server_thread)

