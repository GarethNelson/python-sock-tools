import eventlet
eventlet.monkey_patch()

import socket

class base_sock:
   def __init__(self,bind=None,connect=None):
       """ 
       Base socket type used by udp_sock and tcp_sock

       Keyword arguments:
         bind    -- if not None, specifies a TCP/IP endpoint to bind to and listen on
         connect -- if not None, specifies a TCP/IP endpoint to connect to
       """
