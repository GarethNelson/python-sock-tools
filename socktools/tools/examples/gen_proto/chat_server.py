"""
Python Sock tools: chat_server.py - A chat server based on chat_protocol.json
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

Note:
  This example requires you to first build the chat_protocol.json file using gen_proto.
"""

import eventlet
import generated
import json
from socktools import tcp_sock

class ChatHandlers(generated.ChatProtocol):
   """ Server implementation for the chat protocol

   This class inherits from the generated protocol class rendered by gen_proto and adds handlers. Note that there is no need to do anything beyond adding a handle_MSGTYPE method to the class.
   Adding handlers to the handlers dict of the parent is done automatically, take a look at gen_proto's output to see the generated stubs.
   """
   def handle_ping(self,from_addr,ping_id=None):
       """Handle ping packets
       
       The first message type handler in this example demonstrates making use of the keyword arguments sent to it by the generated class.
       Ping packets contain a ping_id field which can be used to acknowledge the packet in a PONG packet sent back to the remote peer.

       Args:
         from_addr (tuple): Represents the TCP/IP endpoint the message came from in (address,port) format

       Keyword args:
         ping_id (int): In a "real" server this would be the ping ID that needs to be acknowledged with a corresponding PONG message back.
       
       """
       pong_data = json.dumps([1,{'ping_id':ping_id}])
       self.send_raw(tcp_sock.encode_str(pong_data),to_peer = from_addr)

   def handle_msg(self,from_addr,msg_text=None):
       """Handle chat messages

       This is the only handler in this example that does useful work (since ping/pong are not actually used for timeouts directly). The incoming message text is simply broadcast to all other peers.

       Args:
         from_addr (tuple): Represents the TCP/IP endpoint the message came from in (address,port) format

       Keyword args:
         msg_text (str): The text of the message
       """
       msg_data = json.dumps([2,{'msg_text':'<%s:%s> %s' % (from_addr[0],from_addr[1],msg_text)}])
       self.send_raw(tcp_sock.encode_str(msg_data))

if __name__=='__main__':
   chat = ChatHandlers(bind=('127.0.0.1',31337))
   print 'Starting server...'
   chat.start_server()
   print 'Hit ctrl-c to quit'
   while True: eventlet.greenthread.sleep(30)
