"""
Python Sock tools: tcp_linemode_mixin.py - mixin to add line-by-line support to TCP sockets
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

This module enables reading from TCP sockets line by line, it is used by the example simple_chat.py

"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

class TCPLinemodeMixin(object):
   """A mixin for implementing line protocols

   When implementing line-based protocols over TCP, use this mixin

   """
   def encode_msg(self,data):
       """Identity function

       Since we don't need a length prefix when in line-by-line mode this method is just an identity function

       Args:
          data (str): The raw message

       Returns:
          str: The raw message
       """
       return data
   def do_real_read(self,s):
       """Read messages from a socket by reading lines
       
       Args:
          s (socket.socket): the underlying physical socket to read from
       
       Returns:
          str: a single line read from that socket
       """
       addr = s.getpeername()
       if not self.known_peers[addr].has_key('fd'):
          self.known_peers[addr]['fd'] = s.makefile()
       return self.known_peers[addr]['fd'].readline()
