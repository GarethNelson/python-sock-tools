"""
Python Sock tools: simple_chat.py - multiuser "chat" implementation
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

This module implements a toy multiuser chat server, clients can connect using standard tools like netcat and telnet and chat to other clients.

If you want to test it, simply run it as a normal python script and then connect to localhost on port 31337.

Note: this is provided as an example only, it is highly recommended that you do NOT try to run a production server on this code as-is.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

from socktools import tcp_sock
from socktools import tcp_linemode_mixin

MSGTYPE_LINE = 0

class ChatProtocol(tcp_linemode_mixin.TCPLinemodeMixin,tcp_sock.TCPSock):
   """Multiuser chat implementation
   
   Protocols in socktools are either classes that inherit from a socket or mixins that can be added to another application-specific class later along with the socket.
   
   For the multiuser chat protocol we only want TCP, messages are simply newline terminated.
   
   Homework exercise: implement message types and use them to specify IRC-style channels, or outright implement IRC. Hint: you need handlers and a modified parser.
   """
   def get_default_handlers(self):
       """ We setup handlers here
       
       In this example, there's only a single message type (0) - also known as the default message type
       
       Returns:
          dict: the message handlers dict, updated to configure message type 0 so it calls handle_msg
       """
       handlers = super(ChatProtocol,self).get_default_handlers() # it's good practice to add the default handlers from upstream, even though it's pointless in this particular example
       handlers[MSGTYPE_LINE] = [self.handle_msg]
       return handlers
   def handle_msg(self,from_addr,msg_type,msg_data):
       """ Handler for message type 0

       By default, this is the only message handler used, others can of course be setup and should be done in get_default_handlers().

       This method is also gloriously simple - it just broadcasts msg_data to all other connected clients.
       """
       self.send_msg(MSGTYPE_LINE,msg_data)

       
   def handle_all(self,from_addr,msg_type,msg_data):
       """All messages get transformed to show other users where they came from.

       See base_sock.py for information on this method. Note that it is generally not good style to use this method for doing actual application logic, it should only transform.
       
       Homework exercise: make users pseudo-anonymous by hashing their IP address and add in IRC-like ops with /kick and /ban functionality
       """
       new_data = '<%s:%s> %s' % (from_addr[0],from_addr[1],msg_data)
       return (from_addr,msg_type,new_data)




if __name__=='__main__':
   import sys
   chat = ChatProtocol(bind=('127.0.0.1',31337))
   print 'Starting server...'
   chat.start_server()
   print 'Hit ctrl-c to quit'
   while True: eventlet.greenthread.sleep(30)
