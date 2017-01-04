"""
Python Sock tools: meta_sock.py - one socket to rule them all
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

This module provides one socket class to rule them all, one socket class to bring them all and in the meta socket bind them.

Tolkien aside, a meta socket is just a socket class that can add other sockets and respond to messages from all the added sockets in one place.

Each individual socket will also respond to the individual messages unless the meta socket is in override mode.

If you're feeling crazy you can also nest meta sockets inside other meta sockets.

The intended application of this module is enabling things like UDP+TCP at the same time, or websocket+IRC etc.

"""
import eventlet
eventlet.monkey_patch()

import base_sock

class MetaSock(base_sock.BaseSock):
   """ One socket to rule them all

   A meta socket is a socket object that has a collection of child sockets from which it receives messages in pre-parsed format.

   Keyword args:
      override_mode (bool): if True, the child sockets will not process messages and instead defer to the meta socket
   """
   def __init__(self,override_mode=False,**kwargs):
       self.override_mode = override_mode
       super(MetaSock,self).__init__(**kwargs)
   def parser_thread(self):
       """ We do nothing here, nothing at all
       """
       pass
   def recv_thread(self):
       """ We also do nothing here
       """
       pass
   def timeout_thread(self):
       """ Does nothing

       In the meta socket there is no concept of known_peers so this also does nothing.
       Child sockets should implement timeouts as appropriate.
       """
       pass
   def handler_wrapper(self,handler,child_sock,addr,msg_type,msg_data):
       """Invokes the specified handler while catching exceptions
       
       Copied straight from base_sock.BaseSock, does the same except for adding the child_sock param

       Args:
           handler (function):               a function accepting params (addr,msg_type,msg_data)
           child_sock (base_sock.BaseSock):  the child socket this message originated from
           addr (tuple):                     TCP/IP endpoint for the peer that originated the message
           msg_type:                         the message type - this depends on the application but usually an int
           msg_data:                         the message data - this depends on the application but usually a tuple or dict
       """
       try:
          handler(child_sock,addr,msg_type,msg_data)
       except Exception,e:
          self.log_error('Handler for message type %s failed' % msg_type,exc=e)
   def handler_thread(self):
       """ Async invoke handlers - used internally
       
       This is near identical to the implementation in base_sock.BaseSock() except that handlers accept a child_sock param, so we need to account for that.

       Todo:
          refactor this so we're not duplicating code
       """
       while self.active:
         eventlet.greenthread.sleep(0)
         child_sock,addr,msg_type,msg_data = None,None,None,None
         while ((msg_data is None) and self.active):
           eventlet.greenthread.sleep(0)
           addr,msg_type,msg_data = self.in_q.get()
           if not (self.meta_sock is None): # yes, we can nest meta sockets in meta sockets
              self.meta_sock.add_msg(self,addr,msg_type,msg_data)
              if self.meta_sock.override_mode:
                 continue
           if self.handlers.has_key(msg_type):
              for handler in self.handlers[msg_type]:
                  self.pool.spawn_n(self.handler_wrapper,handler,child_sock,addr,msg_type,msg_data)

   def add_msg(self,child_sock,from_addr,msg_type,msg_data):
       """ Add a message to in_q
       
       The child sockets call this to add messages to the meta socket's in_q for handling.

       Args:
          child_sock (base_sock.BaseSock): the child socket this message came from - useful if we need to reply to the message
          from_addr (tuple): the TCP/IP endpoint as seen by the child socket
          msg_type: the message type
          msg_data: the actual message data
       """
       if self.handlers.has_key(msg_type):
          self.in_q.put((child_sock,from_addr,msg_type,msg_data))
          

