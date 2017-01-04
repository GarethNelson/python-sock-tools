"""
Python Sock tools: chat_client.py - Simple client for chat_server.py
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

To run this, make sure chat_server.py is running first, it will bind to port 31337 by default.

Note:
  This example requires you to first build the chat_protocol.json file using gen_proto.
"""

import eventlet
eventlet.monkey_patch()

import sys
import select
import generated
import json
import time

from socktools import tcp_sock

class ChatHandlers(generated.ChatProtocol):
   """ Client implementation for the chat protocol

   Similar to the server implementation, this class simply inherits and adds handlers
   """
   def do_ping(self):
       """Sends ping packets to the server

       To make things simpler, we send ping packets out but we don't bother tracking them - they exist only to keep the connection alive.
       ping_id is simply int(time.time())
       """
       ping_data = tcp_sock.encode_str(json.dumps([0,{'ping_id':int(time.time())}]))
       self.send_raw(ping_data) # broadcast, since we only have 1 peer (the server), no need to specify the address twice
   def pinger_thread(self):
       while not self.active: eventlet.greenthread.sleep(0) # wait until the socket goes active
       while self.active:
          eventlet.greenthread.sleep(self.timeout-1)
          self.do_ping()
   def child_setup(self):
       """Hook on child_setup so we can spawn the pinger thread
       """
       self.pool.spawn_n(self.pinger_thread)
       super(ChatHandlers,self).child_setup()
   def handle_ping(self,from_addr,ping_id=None):
       """Handle ping packets

       Identical to the one in chat_server.py

       Args:
         from_addr (tuple): Represents the TCP/IP endpoint the message came from in (address,port) format

       Keyword args:
         ping_id (int): In a "real" server this would be the ping ID that needs to be acknowledged with a corresponding PONG message back.
       
       """
       pong_data = tcp_sock.encode_str(json.dumps([1,{'ping_id':ping_id}]))
       self.send_raw(pong_data,to_peer = from_addr)

   def handle_msg(self,from_addr,msg_text=None):
       """Handle chat messages

       Since this is the client, we dump messages to stdout

       Args:
         from_addr (tuple): Represents the TCP/IP endpoint the message came from in (address,port) format

       Keyword args:
         msg_text (str): The text of the message
       """
       print msg_text

if __name__=='__main__':
   chat = ChatHandlers(connect=('127.0.0.1',31337))
   print 'Hit ctrl-c to quit'
   while True:
      eventlet.greenthread.sleep(0)
      if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
         in_line = sys.stdin.readline().strip('\n')
         msg_data = json.dumps([2,{'msg_text':in_line}])
         chat.send_raw(tcp_sock.encode_str(msg_data))
