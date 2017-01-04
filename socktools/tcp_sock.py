"""
Python Sock tools: tcp_sock.py - simple TCP implementation
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

This module contains an implementation of P2P TCP messaging - that is, you can use it to implement either client or server, servers may connect to clients and clients may turn into servers.

For most applications you'll want to just pass the TCPSock class a bunch of handlers then start it as a server, and then do the same in your client and pass the connect param in.

In terms of actual protocol, since this module is intended for message-based protocols a line by line mode is NOT available by default. Instead, every socket is a stream of message lengths and binary blob messages.

The message length is an unsigned integer in big endian (also known as the standard network order). Python treats this datatype as having 4 bytes.

If you have messages over 4,294,967,296 bytes long you're a liar because nobody does that - if you do however happen to have a 4GB long piece of data to send (really?) consider rethinking your protocol (and your life).
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

import base_sock
import socket
import struct

class TCPSock(base_sock.BaseSock):
   """ Simple TCP implementation - both client and server

   This class implements TCP based messaging on both the client and server side.
   In order to use it as a server, make sure you pass the appropriate endpoint to the bind param in the constructor
   and then call start_server().
   Without calling start_server() or connecting somewhere with connect_to() this class will do nothing at all.
   """
   def create_socket(self,no_reuse=False):
       """ Creates the physical socket object
   
       Since it makes no sense to create a TCP socket without binding it, you should not call this method directly.
       Instead, pass a valid bind param to __init__ and leave the socket param as None
       This method should only really be used by servers

       Keyword args:
          no_reuse (bool): if True, the socket will NOT have SO_REUSEADDR set
           
       Note:
         The socket sets SO_REUSEADDR by default, this saves a LOT of time in testing your code, but if you don't
         want this behaviour you can configure it using the no_reuse param
           
       Returns:
         socket.socket: the physical socket object for inbound connections
       """
       s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       if not no_reuse:
          s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       return s

   def handle_client_send(self,addr,client_sock):
       """Used internally - sends messages to clients
       
       Although send_raw() could in theory just send direct to the socket, that'd be a bad idea.
       So instead we use a queue, this thread grabs messages from that queue and sends them off.
       
       Note:
          This method will return silently if called on a peer address that does not exist

       Warnings:
           Starting this twice will probably result in corrupted connection state, don't start it at all outside the class

       Args:
           addr (tuple): TCP/IP endpoint of the client in (ip,port) format
           client_sock (socket.socket): The physical socket
       """
       
       while self.active:
          eventlet.greenthread.sleep(0)
          if not self.known_peers.has_key(addr): return
          try:
             next_msg = self.known_peers[addr]['sendq'].get()
             client_sock.sendall(next_msg)
          except Exception,e:
             self.log_error('Failed transmitting to %s:%s' % addr,exc=e)
             return

   def do_real_read(self,s):
       """ Used to perform the actual read from a socket
       
       This by default reads the message length prefix first and then the message. If your application needs a different scheme it should implement it here in a child class.
       
       If there is no data to read, this method should block (via eventlet) until sufficient data is available to read a whole message.
       
       The default implementation reads a big-endian unsigned 32-bit integer from the socket specifying the message length and then reads the message.
       
       In the default implementation, the message length prefix is NOT returned.

       Args:
          s (socket.socket): The socket we're trying to read from

       Returns:
          str: the data read from the socket.
       
       """
       msg_len_s = s.recv(4)
       msg_len   = struct.unpack('>I',msg_len_s)[0]
       msg_data  = s.recv(msg_len)
       return msg_data

   def encode_msg(self,data):
       """Used to encode the length prefix in messages

       This should be overridden if you override do_real_read() and/or decode_msg().

       In the default implementation, a 32-bit unsigned integer representing the data length is prefixed

       Args:
          data (str): the data to encode

       Returns:
          str: the data with a length prefix
       """
       data_len      = len(data)
       len_prefix = struct.pack('>I',data_len)
       return '%s%s' % (len_prefix,data)


   def handle_client(self,client_addr,client_sock):
       """Used internally - reads messages from clients and passes them off to be read

       Since the entire point of socktools is to turn all sockets into message-orientated connections this method simply reads
       messages and queues them up.
         
       Note:
          It's probably a bad idea to call this directly, but some weird and possibly cool things could be done if you do
       """
       self.log_debug('Starting handle_client() greenlet for %s:%s' % client_addr)
       if not self.known_peers.has_key(client_addr):
          self.known_peers[client_addr] = {}
       self.known_peers[client_addr]['sock']  = client_sock
       self.known_peers[client_addr]['sendq'] = eventlet.queue.LightQueue(100)
       self.pool.spawn_n(self.handle_client_send,client_addr,client_sock)
       while self.active:
          eventlet.greenthread.sleep(0)
          try:
             msg_data = None
             with eventlet.timeout.Timeout(self.timeout,False):
                try:
                   msg_data    = self.do_real_read(client_sock)
                except Exception,e:
                   pass
                if msg_data is None:
                   try:
                      client_sock.close()
                   except:
                      pass
                   try:
                      del self.known_peers[client_addr]
                   except:
                      pass
                else:
                   self.recv_q.put((msg_data,client_addr))
          except Exception,e:
             errmsg = 'Failed reading message from %s:%s' % (client_addr[0],client_addr[1])
             self.log_error(errmsg, exc=e)
             return

   def read_raw(self):
       """ Reads the next available raw packet from any client
       
       In this implementation, that simply means grabbing from recv_q and returning
       
       Returns:
          tuple: (data, from_addr) - data is a string, from_addr is the remote peer's TCP/IP endpoint
       """
       return self.recv_q.get()
   
   def send_raw(self,data,to_peer=None):
       """ Send a single raw packet to a specified peer (or to all connected peers)
       
       This method essentially just dumps stuff into the specified peer's sendq, or alternatively into every connected peer's sendq
       
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

   
   def server_thread(self):
       """Used internally - accepts new clients and gives them a nice shiny new greenlet

       Every client attempting to connect must first be "blessed" by good_peer(), otherwise the connection is silently dropped
       A future version of this code should probably add a callback or something here

       Warning:
          This method must not be called from outside the class or bad things will happen
       """
       while self.active:
          eventlet.greenthread.sleep(0)
          client_sock,client_addr = self.sock.accept()
          if self.good_peer(client_addr):
             self.pool.spawn_n(self.handle_client,client_addr,client_sock)
          else:
             client_sock.close()

   def connect_to(self,endpoint):
       """ Connect to the specified endpoint
       
       When overriding in childclasses you should call the parent first to setup the actual connection.
       Confusingly, after connecting outwards, the peer is handled by the handle_client thread - feel free to send a pull request if that bugs you
       
       Arg:
         endpoint (tuple): the TCP/IP endpoint as (ip,port)
       """
       
       self.recv_q = eventlet.queue.LightQueue(100)
       s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       s.connect(endpoint)
       self.pool.spawn_n(self.handle_client,endpoint,s)

   def start_server(self,bind=None,backlog=1):
       """ Start listening for clients in a new greenlet
           
       This method sets up the infrastructure needed to pass clients off to greenlets and then does listen() on the socket.
           
       You should generally only use this method when creating a pure server - call it after your application is ready to accept clients.
       If you must use it after passing a connect param to __init__() then it might work, or it might fail horribly.
       Instead, to implement a P2P node, pass a bind param to __init__() and then use connect_to() to connect remote peers.

       Keyword args:
          bind (tuple): if the socket did not have an appropriate bind param passed to __init__ you can pass it here
          backlog (int): the number of clients to have in the queue awaiting an accept() call - generally the default is ok here
           
       Warning:
          If you pass the bind param here when the socket was already bound in the constructor, this will fail.

       Warning:
          Calling this twice is beyond idiotic, and not checked for - if you do that, it's on you
       """
       if not (bind is None): self.sock.bind(bind)
       self.sock.listen(backlog)
       self.recv_q = eventlet.queue.LightQueue(100) # packets read from clients go here, read_raw() returns them
       self.pool.spawn_n(self.server_thread)
