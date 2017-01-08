"""
Python Sock tools: irc_sock.py - implements IRC server socket
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

This module provides an implementation of an IRC server socket with appropriate encoding/decoding

"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

import os

from socktools import tcp_sock
from socktools import tcp_linemode_mixin


class IRCSock(tcp_linemode_mixin.TCPLinemodeMixin,tcp_sock.TCPSock):
   """An IRC socket for use by servers

   This class implements the basics of the IRC protocol: just encoding and decoding messages and handles for a few lowlevel messages.

   Messages are encoded like so:
      :Source MsgType Target :Text

   Or at least they are for PRIVMSG, IRC is a messy protocol sometimes. Note that hashing of client hostnames must be handled by the caller.

   """
   def get_default_handlers(self):
       """Return the default handlers for IRC sockets
       
       Note that PRIVMSG and friends are not handled here, only the lowlevel basics such as PING
       """
       return {'PING':[self.handle_ping]}
   def handle_ping(self,from_addr,msg_type,msg_data):
       """Handle PING messages from peers
       
       Note that this is probably not really appropriate if we're a server, but it's included for completeness

       """
       self.send_msg('PONG',msg_data,to_peer=from_addr)
   def serialise_msg(self,msg_type,msg_data):
       """Serialise a message in IRC format

       The exact format of the message depends on the type, and so do the required params in msg_data.
       You are advised to read the code for a list of required params.

       If the msg_type is unknown or unimplemented, this method will return a null-length string.

       Args:
          msg_type (str): One of the IRC message types
          msg_data (dict): A dict of message params, specific params depends on the message type

       Returns:
          str: The serialised IRC message

       """
       if msg_type=='PRIVMSG':
          MsgSource = msg_data['source']
          MsgTarget = msg_data['target']
          MsgText   = msg_data['msgtext']
          return ':%s PRIVMSG %s :%s' % (MsgSource,MsgTarget,MsgText)
       return ''
   def parse_msg(self,data):
       """Parse a raw IRC message

       This is where we parse IRC messages from clients, or attempt to.

       Args:
          data (str): The raw packet to parse
       
       Returns:
          tuple: a tuple of (msg_type,msg_data)

       """
       line       = data.strip('\r\n')
       split_line = line.split(':')
       if line.startswith(':'):
          source,msg_type,target = split_line[1].split(' ')
          msgparams              = split_line[2:]
       else:
          source = ''
          split_first            = split_line[0].split(' ')
          msg_type,target        = split_first[0],split_first[1]
          msgparams              = split_line[1:]
       retval = {}
       retval['source'] = source
       retval['target'] = target
       retval['params'] = msgparams
       if msg_type=='PRIVMSG':
          retval['msgtext'] = msgparams[0]
       return (msg_type,retval)





