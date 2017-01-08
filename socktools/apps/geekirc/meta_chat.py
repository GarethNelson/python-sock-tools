"""
Python Sock tools: meta_chat.py - meta socket for IRC and similar chat protocols
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

This module provides an implementation of a meta socket designed for handling IRC and similar chat protocols.

"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

import os

from socktools import meta_sock

class MetaChat(meta_sock.MetaSock):
   """A meta socket for chat

   This meta socket handles rebroadcasting of messages to interested parties across multiple protocols.

   Each underlying child socket must support the PRIVMSG message type and be able to handle it appropriately. The message is assumed to be a dict as seen in irc_sock.py

   No security checks are done, which means anyone can send a message to any channel on IRC.
   """

   def child_setup(self):
       """ Setup infrastructure needed here
       
       This method configures the targets dict and other infrastructure

       """
       self.targets = {} # maps IRC-format targets to sets of (client_sock,peer_addr) tuples
   def handle_privmsg(self,child_sock,addr,msg_type,msg_data):
       """Handle the PRIVMSG messages

       We simply rebroadcast to the target set

       """
       self.log_debug('Got a PRIVMSG: %s' % msg_data)
       source  = msg_data['source']
       target  = msg_data['target']
       msgtext = msg_data['msgtext']
       if self.targets.has_key(target):
          for t in self.targets[target]:
              t_sock,t_addr = t
              outdata = (source,target,msgtext)
              t_sock.send_msg('PRIVMSG',outdata,to_peer = t_addr)
   def get_default_handlers(self):
       return {'PRIVMSG':[self.handle_privmsg]}
