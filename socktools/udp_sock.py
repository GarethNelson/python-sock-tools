"""
Python Sock tools: udp_sock.py - simple UDP implementation
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

This module contains the class you probably want most of the time: it implements P2P UDP.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

import base_sock
import socket
import struct

class UDPSock(base_sock.BaseSock):
   """ Simple UDP implementation - both client and server
   
   Read the code to see just HOW trivially simple this is, application logic belongs elsewhere

   """
   def create_socket(self,no_reuse=False):
       """ Creates the physical socket object
           
       Note:
         The socket sets SO_REUSEADDR by default, this saves a LOT of time in testing your code, but if you don't want this behaviour turn it off in child_setup()

       Returns:
         socket.socket: the physical socket object for inbound connections
       """
       s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       return s

