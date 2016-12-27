import eventlet
eventlet.monkey_patch()

import socket

class DummySocket:
   pass

class base_sock:
   def __init__(self,bind=None,connect=None,handlers={},timeout=2,tick_interval=0.25):
       """
       Keyword Args:
           bind (tuple):        if not None, specifies a TCP/IP endpoint as (ip,port) to bind to and listen on
           connect (tuple):     if not None, specifies a TCP/IP endpoint as (ip,port) to connect to
           handlers (dict):     maps message types to message handler functions
           timeout (int):       time in seconds before a peer is considered to have timed out
           tick_interval (int): time in seconds to wait between ticks
       """
       self.known_peers = {}
       self.pool        = eventlet.GreenPool(1000)
       self.sock        = self.create_socket()
       self.handlers    = {}
       self.handlers.update(handlers)
       self.parse_q     = eventlet.queue.LightQueue(100) # raw packets ready to be parsed
       self.in_q        = eventlet.queue.LightQueue(100) # parsed packets ready to be handled
       if not (bind is None):    self.sock.bind(bind)
       if not (connect is None): self.connect_to(connect)
       self.active = True
       for x in xrange(10): self.pool.spawn_n(self.parser_thread)
       for x in xrange(10): self.pool.spawn_n(self.handler_thread)
   def handler_thread(self):
       """
       Used internally as a greenthread that handles passing parsed messages off to the relevant handler in a new greenlet
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
       """
       Invokes the specified handler while catching exceptions so we don't kill the handler_thread greenlet
       
       :param handler:  A function that accepts the params (addr,msg_type,msg_data)
       :param addr:     TCP/IP endpoint from the original packet
       :param msg_type: The message type - what this is depends on the application, usually an int
       :param msg_data: Message data - what this is depends on the application
       """
       try:
          handler(addr,msg_type,msg_data)
       except Exception,e:
          self.log_error('Handler for message type %s failed' % msg_type,exc=e)
   def log_error(self,msg,exc=None):
       """
       Log the specified error in whatever way is appropriate for the application
       Default implementation simply prints to stdout
       
       Arguments:
         msg -- string containing the error message
       Keyword arguments:
         exc -- if not None, contains a python exception related to the error
       """
       print 'Error: %s, Exception: %s' % (msg,exc)
       
   def parser_thread(self):
       """
       Used internally as a greenthread that handles message parsing
       """
       while self.active:
         eventlet.greenthread.sleep(0)
         data,addr = None,None
         while ((data is None) and self.active):
           eventlet.greenthread.sleep(0)
           if not (data is None):
              data,addr         = self.parse_q.get()
              try:
                 msg_type,msg_data = self.parse_msg(data)
              except Exception,e:
                 self.log_error('Error parsing packet from %s:%s' % addr,exc=e)
              self.in_q.put((addr,msg_type,msg_data))
   def add_handler(self,msg_type,handler,exclusive=False):
       """
       Add a handler for the specified message type

       Arguments:
         msg_type  -- the message type this handler is for
         handler   -- a function that takes the params (from_peer,msg_type,msg_data) where from_peer is a TCP/IP endpoint

       Keyword arguments:
         exclusive -- if True, deletes all previously set handlers for this message type
       """
       if not self.handlers.has_key(msg_type): self.handlers[msg_type] = []
       if exclusive: self.handlers[msg_type] = []
       self.handlers[msg_type].append(handler)
   def parse_msg(self,data):
       """
       Parse the message provided in "data" and return a tuple of (msg_type,msg_data) usable by the end application
       The default implementation returns (0,{}), this method should be overridden
       
       Arguments:
         data -- the raw data to be parsed
       """
       return (0,{})
   def read_raw(self):
       """
       Read a single raw packet from the socket, this should be as fast as possible
       
       Return value should be a tuple of (data,addr) where data is a string or byte buffer and addr is the endpoint
       If there is >1 peer it is up to the child class to handle scheduling - just use eventlet fools

       Default implementation returns a null-length string from ('127.0.0.1',1337)
       """
       return ('',('127.0.0.1',1337))

   def send_raw(self,data,to_peer=None):
       """
       Send a single raw packet from the socket to the address specified
       If to_peer is None and it makes sense to do so, this method should broadcast the packet to all connected peers
       The default implementation does nothing

       Arguments:
         data    -- the raw data to be sent

       Keyword arguments:
         to_peer -- the peer to send to, all peers are specified as TCP/IP endpoints
       """
       pass
   def create_socket(self):
       """
       Create the socket - this should be overridden, the default implementation returns a special DummySocket class
       """
       return DummySocket()
   def connect_to(self,endpoint):
       """
       Connect to the specified TCP/IP endpoint as (ip,port), this adds it to the known peers list and performs any authentication.
       The default implementation does nothing beyond adding it to the known peers list.
       When overriding, please make sure to use super() to call the original method.
       If the peer is already connected, this is essentially a NOP.

       Arguments:
         endpoint -- the TCP/IP endpoint as (ip,port)
       """
       self.known_peers[endpoint] = {}
