"""
Python Sock tools: wsgi_websocket_sock.py - websocket implementation for server side
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

This module contains a simple wrapper around the websocket server support in eventlet, giving the same uniform API as the rest of socktools.

Once started, messages are read one by one from the socket, it is advised to use JSON for encoding and decoding.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

from eventlet import wsgi, websocket

import base_sock
import socket

class WSGIWebsocketSock(base_sock.BaseSock):
   """ Simple implementation of a WSGI websocket server.

   This class implements a websocket server that can be used with any WSGI-compatible httpd.
   Call start_server() to startup the basic infrastructure and then get_wsgi_func() to get a WSGI function that can be used in your httpd.
   """
   def create_socket(self):
       """ Does nothing

       There is no concept of creating a physical socket for websockets, so this method does nothing.
   
       """
       pass

   def read_raw(self):
       """ Reads the next available raw packet from any client
       
       In this implementation, that simply means grabbing from recv_q and returning
       
       Returns:
          tuple: (data, from_addr) - data is a string, from_addr is the remote peer's TCP/IP endpoint
       """
       return self.recv_q.get()
   
   def send_raw(self,data,to_peer=None):
       """ Send a single raw packet to a specified peer (or to all connected peers)
       
       This method essentially just dumps stuff into the specified peer's sendq, or alternatively into every connected peer's sendq.
       
       It is then up to the handle_client_send thread to actually transmit the data
       
       Args:
         data (str): The raw data to send - must be already encoded including the length prefix
       
       Keyword args:
         to_peer(tuple): The TCP/IP endpoint as a (host,ip) tuple, if set to None all connected peers will get the packet

       """
       if to_peer is None: # broadcast
          for k,v in self.known_peers.items():
              try:
                 v['sendq'].put(data)
              except Exception,e:
                 self.log_error('Error doing send_raw() to %s:%s' % k, exc=e)
       else:
         self.known_peers[to_peer]['sendq'].put(data)

   def ws_sender_thread(self,ws):
       """Used internally - sends messages to websocket clients
       
       Args:
         ws (websocket.WebSocket): the websocket object representing the client connection
       """
       environ  = ws.environ
       endpoint = (ws.environ['REMOTE_ADDR'],int(ws.environ['REMOTE_PORT']))
       while self.active and self.known_peers.has_key(endpoint):
          try:
             msg_data = self.known_peers[endpoint]['sendq'].get()
             ws.send(msg_data)
          except Exception,e:
             self.log_error('Error sending',exc=e)
   def wsgi_func(self,ws):
       """ WSGI handler function
       
       This is the WSGI handler function for websocket clients, it should not be invoked directly - use get_wsgi_func() and then pass that value to your httpd.

       Args:
          ws (websocket.WebSocket): the websocket object representing the client connection
       """
       environ  = ws.environ
       endpoint = (ws.environ['REMOTE_ADDR'],int(ws.environ['REMOTE_PORT']))
       self.known_peers[endpoint] = {}
       self.known_peers[endpoint]['sendq'] = eventlet.queue.LightQueue()
       self.pool.spawn_n(self.ws_sender_thread,ws)
       while self.active:
          eventlet.greenthread.sleep(0)
          in_msg = ws.wait()
          if in_msg is None:
             del self.known_peers[endpoint]
             return
          else:
             self.recv_q.put((in_msg,endpoint))

   def get_wsgi_func(self):
       """Get a WSGI function

       Use this instead of directly referencing wsgi_func, directly referencing it will break subclasses that wrap the socket

       Returns:
          function: the WSGI function that can be passed to an appropriate server
       """
       return websocket.WebSocketWSGI(self.wsgi_func)

   def start_server(self):
       """ Start the basic infrastructure so new clients can be accepted.
           
       This method sets up the infrastructure needed to pass clients off to greenlets, it is then up to the user application to use get_wsgi_func() to do stuff with those clients.

       Warning:
          Calling this twice is beyond idiotic, and not checked for - if you do that, it's on you
       """
       self.recv_q = eventlet.queue.LightQueue(100) # packets read from clients go here, read_raw() returns them
