"""
Python Sock tools: base_sock.py - implementation of the base socket classes
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

This module provides the base classes used in the other modules, you should probably ignore it unless you plan to implement a new socket type.

"""
import eventlet
eventlet.monkey_patch()

import socket
import traceback
import time

class DummySocket(socket.socket):
   """ A socket object that does nothing
   """
   def __init__(self,sock_family=socket.AF_INET,sock_type=socket.SOCK_DGRAM,proto=0):
       """ Hackish constructor for the dummy socket

       Accepts same params as socket.socket but does nothing with them
       In case you're curious though, the default arguments are (socket.AF_INET,socket.SOCK_DGRAM,0)

       Keyword args:
          sock_family (int): not used at all, seriously!
          sock_type (int):   also not used
          proto (int):       spotting a pattern yet?
       
       Note:
          You should NOT inherit from this class normally, instead override the create_socket() method of BaseSock and return a socket.socket
       """
       pass
   def recvfrom(self,buflen=8192,flags=0):
       """ Dummy implementation of socket.recvfrom()
       
       This method simply returns a null-length string coming from address ('127.0.0.1',1337)
       """
       return ('',('127.0.0.1',1337))

class BaseSock(object):
   """The base class from which specific socket classes inherit
   
   This class is the base socket class which handles queuing of messages and the main event loop.
   It should not be used directly but rather subclassed or one of the existing child classes used.
   
   Keyword Args:
      bind (tuple):         if not None, specifies a TCP/IP endpoint as (ip,port) to bind to and listen on
      connect (tuple):      if not None, specifies a TCP/IP endpoint as (ip,port) to connect to
      handlers (dict):      maps message types to message handler functions
      timeout (int):        time in seconds before a peer is considered to have timed out
      tick_interval (int):  time in seconds to wait between ticks
      sock (socket.socket): if not None, specifies a socket object to be used - should be used only for testing

   Attributes:
      known_peers (dict):                  all currently connected peers have an entry in this dict, the contents of the dict are another dict with metadata
      pool (eventlet.GreenPool):           all greenlets spawned by the socket belong to this pool, with a default concurrency of 1000
      parse_q (eventlet.queue.LightQueue): raw packet data is added to this queue before being parsed, each item is a tuple of (data,addr)
      in_q (eventlet.queue.LightQueue):    parsed messages are added to this queue after being parsed
      timeout (int):                       the timeout interval in seconds - peers must talk to us on a regular basis to avoid being timed out
      tick_interval (int):                 the tick interval - what exactly a tick does is up to the application
      handlers (dict):                     maps message types to message handler functions
      sock:                                arbitrary object representing the physical socket, defaults to an instance of DummySocket
      active (bool):                       indicates whether this socket is active and working
   """
   def __init__(self,bind=None,connect=None,handlers={},timeout=10,tick_interval=0.25,sock=None):
       self.known_peers = {}
       self.pool        = eventlet.GreenPool(1000)
       if not (sock is None):
          self.sock = sock
       else:
          self.sock        = self.create_socket()
       self.handlers       = self.get_default_handlers()
       self.handlers.update(handlers)
       self.parse_q       = eventlet.queue.LightQueue(100) # raw packets ready to be parsed
       self.in_q          = eventlet.queue.LightQueue(100) # parsed packets ready to be handled
       self.timeout       = timeout
       self.tick_interval = tick_interval
       if not (bind is None):    self.sock.bind(bind)
       if not (connect is None): self.connect_to(connect)
       self.active = True
       for x in xrange(10): self.pool.spawn_n(self.parser_thread)
       for x in xrange(10): self.pool.spawn_n(self.handler_thread)
       self.pool.spawn_n(self.recv_thread)
       self.pool.spawn_n(self.timeout_thread)
   def get_default_handlers(self):
       """Get a default handlers dict
       
       When inheriting from this class you should setup default handlers needed by the protocol by overriding this method. Additionally, children should always call the parent for this method.
       
       Returns:
          dict: a dict mapping message types to handlers, can be 0-length but must be a dict
       """
       return {}
   def timeout_thread(self):
       """Used internally - removes peers from the known_peers dict if they haven't sent us a packet within the last timeout interval

       Warning:
          This method must not be called from anywhere except inside the class, and only one instance should run at a time
       """
       while self.active:
          if len(self.known_peers)==0:
             eventlet.greenthread.sleep(0)
          else:
             eventlet.greenthread.sleep(self.timeout / len(self.known_peers))
          cur_time = time.time()
          for k,v in self.known_peers.items():
              if not v.has_key('last'): v['last'] = time.time()
              if (cur_time - v['last']) >= self.timeout:
                 self.log_debug('%s:%s timed out' % k)
                 self.close_peer(k)
   def tick(self):
       """Perform application-specific tick
       
       The default implementation does absolutely nothing, you should override this if you want tick functionality
       While debugging it may be helpful to insert a sleep in here to see what happens when you miss ticks

       Args:
          diff (int): the recorded time in seconds the last tick took to run, 0 on the first iteration

       """
       pass
   def tick_thread(self):
       """Used internally to call the tick() method in a loop with accurate timing

       Many network protocols, 3D gaming ones in particular, require a fixed frequency "tick", that's what is implemented here.
       This thread runs tick() in a loop and measures the time it took, adjusting the delay to compensate

       Note:
          This code makes no guarantees at all that the specified tick interval is actually achievable - if you get missed ticks, optimise your tick() to be more async
       """
       diff = 0
       while self.active:
          start_time = time.time()
          self.tick(diff)
          end_time = time.time()
          diff = end_time-start_time
          if diff >= self.tick_interval:
             eventlet.greenthread.sleep(self.tick_interval - diff)
          else:
             eventlet.greenthread.sleep(0)

   def close_peer(self,peer):
       """Removes a peer from the known_peers list and does any required cleanup

       Args:
          peer (tuple): the peer to close as a TCP/IP endpoint tuple, i.e (ip,port)
       
       Notes:
          The default implementation simply removes the peer from the known_peers list, any child class should do the same when overriding this method
       """
       if self.known_peers.has_key(peer): del self.known_peers[peer]
   def recv_thread(self):
       """Used internally - reads from the socket and puts the raw packets into parse_q

       Warning:
          This method absolutely must not be called from anywhere except inside the class or bad things will happen
       """
       while self.active:
          eventlet.greenthread.sleep(0)
          data,addr = None,None
          while (data is None) and self.active:
             eventlet.greenthread.sleep(0)
             try:
                data,addr = self.read_raw()
             except Exception,e:
                self.log_error('Error reading from socket',exc=e)
             if not (data is None):
                if (len(data)>0) and self.good_peer(addr):
                   if self.known_peers.has_key(addr):
                      self.known_peers[addr]['last'] = time.time()
                   self.log_debug('Got raw data: %s' % str(data))
                   self.parse_q.put((data,addr))
   def handler_thread(self):
       """Used internally - reads from in_q and passes to the appropriate handler

       Note:
          This method should only be run from inside the class and inside a greenthread
       """
       while self.active:
          eventlet.greenthread.sleep(0)
          addr,msg_type,msg_data = None,None,None
          while ((msg_data is None) and self.active):
            eventlet.greenthread.sleep(0)
            addr,msg_type,msg_data = self.in_q.get()
            if self.handlers.has_key(msg_type):
               self.pool.spawn_n(self.handler_wrapper,self.handlers[msg_type],addr,msg_type,msg_data)
   def handler_wrapper(self,handler,addr,msg_type,msg_data):
       """Invokes the specified handler while catching exceptions

       This method invokes a handler function while catching and logging any exceptions.
       If an exception is raised by the handler, BaseSock.log_error() is called to notify the end user
       
       Args:
           handler (function): a function accepting params (addr,msg_type,msg_data)
           addr (tuple):       TCP/IP endpoint for the peer that originated the message
           msg_type:           the message type - this depends on the application but usually an int
           msg_data:           the message data - this depends on the application but usually a tuple or dict
       """
       try:
          handler(addr,msg_type,msg_data)
       except Exception,e:
          self.log_error('Handler for message type %s failed' % msg_type,exc=e)
   def log_debug(self,msg):
       """Logs debug info - if debug mode is off, this method should do nothing

       The default implementation prints the message to stdout

       Args:
         msg (str): message to log
       """
       print msg
   def log_error(self,msg,exc=None):
       """Log an error with exception data

       This method logs errors and should be overridden to use whatever logging mechanism is appropriate in the end user application.

       The default implementation simply prints the message and exception data to stdout
       
       Args:
         msg (str): error message
       Keyword args
         exc (Exception): a python exception related to the error
       """
       if exc is None:
          print 'Error: %s' % msg
       else:
          print 'Error: %s, Exception: %s' % (msg,traceback.format_exc(exc))
       
   def parser_thread(self):
       """Used internally - reads from parse_q and puts parsed messages into in_q
       
       Note:
          This method should only be run from inside the class and inside a greenthread
       """
       while self.active:
         addr,data,msg_type,msg_data = None,None,None,None
         eventlet.greenthread.sleep(0)
         addr,data = self.parse_q.get()
         try:
            msg_type,msg_data = self.parse_msg(data)
         except Exception,e:
            self.log_error('Error parsing packet from %s:%s' % addr,exc=e)
         addr,msg_type,msg_data = self.handle_all(addr,msg_type,msg_data)
         self.log_debug('Putting parsed message type %s from %s:%s on queue: %s' % (str(msg_type),str(addr[0]),str(addr[1]),str(msg_data)))
         self.in_q.put((addr,msg_type,msg_data))
   def add_handler(self,msg_type,handler,exclusive=False):
       """Add a handler for the specified message type
       
       This method adds message handlers to the socket after it has been setup, allowing dynamic handlers.

       It is preferable to use static handlers whenever possible
       
       Args:
         msg_type: the message type the handler is for, this depends on application but is usually an int
         handler:  the handler function to add, must accept params (addr,msg_type,msg_data)

       Keyword args:
         exclusive (bool): if True, deletes all previously set handlers for this message type
       """
       if not self.handlers.has_key(msg_type): self.handlers[msg_type] = []
       if exclusive: self.handlers[msg_type] = []
       self.handlers[msg_type].append(handler)
   def parse_msg(self,data):
       """Parse a raw message into a format usable by the application
       
       This method should be overridden by the application as appropriate and handles message parsing from raw packets.
       
       Args:
         data (str): the raw packet to be parsed, this should be one whole message

       Returns:
         tuple of (msg_type,msg_data) - the specific types of msg_type and msg_data depend on the application
       
       Note:
         If not overridden, by default this method returns a message of type 0 and the raw data as msg_data.
         Please also note that this method should NOT implement anything beyond parsing, see good_peer() and handle_all() for higher level logic.
       """
       return (0,str(data))
   def good_peer(self,peer):
       """Check if the specified peer is one we want to talk to

       If this method returns False for a peer as it sends us a message, that message will be dropped and not parsed.
       The default implementation returns True for every peer

       Args:
          peer (tuple): the TCP/IP endpoint of the peer as an (ip,port) tuple

       Returns:
          bool: True if the peer is good, otherwise False
       """
       return True
   def handle_all(self,from_addr,msg_type,msg_data):
       """Called before doing anything with a decoded/parsed packet before all other handlers
       
       This can be used as a hook to implement whatever you want with decoded packets - stuff like encryption and compression though belongs in parse_msg().

       After being parsed all messages pass through this method and any transformations required can be applied.
       Most applications will not need this and the default implementation (which is a simple identity function) will work fine.

       One application where this may be of use is to send "unknown peer" type messages if the address is not in the known peers dict.

       Args:
           from_addr (tuple): The remote peer's TCP/IP endpoint as an (ip,port) tuple
           msg_type: The message type, what this is depends on the application but is usually an int
           msg_data: The message data, what this is depends on the application

       Returns:
           tuple: (from_addr,msg_type,msg_data) - the message, modified or not, by default this is identical to the params unless overridden
       """
       return (from_addr,msg_type,msg_data)

   def read_raw(self):
       """Read a single raw packet from the socket or sockets
       
       If the underlying physical socket is UDP, this method should simply read from it and return as quickly as possible.

       If the underlying physical socket is a TCP socket connected to one single peer, this method should read from it and return as quickly as possible.

       If the underlying physical socket is a TCP server, this method should return a raw packet from the next available client.

       In all cases, this method should return a raw packet without parsing of any kind beyond size checking.

       If no data is available, this method should block using eventlet.greenthread.sleep(0) or equivalent until data is available.

       Note:
          The default implementation together with DummySocket always returns a null-length string from localhost:1337
          Using the default implementation with another physical socket type probably won't work

       Warning:
          this method must NOT block except via eventlet, failure to heed this warning will result in crippled performance

       Returns:
          tuple: (data,from_addr) - data should be a string or byte buffer, from_addr should be a TCP/IP endpoint tuple in the form (ip,port)
       
       """
       return self.sock.recvfrom(8192)

   def send_raw(self,data,to_peer=None):
       """Send a single raw packet from the socket to the specified peer

       This method sends a single raw packet (already encoded as appropriate) to the specified peer, or optionally to all connected peers.

       The whole packet must be transmitted before this method returns and it must block if required via eventlet.greenthread.sleep(0) or equivalent

       Args:
         data(str): the raw data to send, this must already be encoded and ready for transmission on the physical socket - including length if required
       
       Keyword args:
         to_peer(tuple): the TCP/IP endpoint as a (host,ip) tuple to transmit to, if this is set to None then all peers will be sent the packet

       Note:
         The default implementation together with DummySocket will result in printing a hex dump of the packet to stdout

       Warnings:
         This method must NOT block except via eventlet, failure to heed this warning will result in crippled performance.
         Further, it is vitally important to wrap the actual transmission in an appropriate try/catch block when broadcasting so that a failure to transmit to one client does not result in failing to transmit to others

       """
       if to_peer is None: # broadcast
          for k,v in self.known_peers.items():
              try:
                 self.sock.sendto(data,k)
              except Exception,e:
                 self.log_error('Error transmitting to %s:%s' % k,exc=e)
       else:
          self.sock.sendto(data,to_peer)

   def create_socket(self):
       """Create the physical socket object
       
       To be of any practical use, this should be overridden
       
       Returns:
          socket.socket: The physical socket object, in the default implementation this is a DummySocket instance
       """
       return DummySocket()
   def connect_to(self,endpoint):
       """Connect to a specified endpoint

       This method should be overridden and used to implement any authentication etc before adding the specified endpoint to the known peers list
       In the default implementation nothing is done here except adding the peer to the known peers list

       Arg:
         endpoint (tuple): the TCP/IP endpoint as (ip,port)
       """
       self.known_peers[endpoint] = {}
