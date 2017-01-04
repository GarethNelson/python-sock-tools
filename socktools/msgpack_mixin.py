"""
Python Sock tools: msgpack_mixin.py - mixin to handle msgpack decoding
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

This module implements a mixin that implements the parse_msg() method using msgpack - see http://www.msgpack.org for details on the msgpack format.

"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case
import msgpack
import gc

class MsgpackParseMixin(object):
   """A mixin for parsing msgpack messages
   
   See http://msgpack.org/ for details
   """
   def serialise_msg(self,msg_type,msg_data):
       """Serialise a msgpack message

       Similar to the JSON mixin, this method serialises messages as msgpack lists of (msg_type,msg_data)

       Args:
          msg_type (int): the message type as an integer
          msg_data (dict): usually a dict, the actual message contents

       Returns:
          str: the msgpack encoded message
       """
       pack_data   = (msg_type,msg_data)
       encoded_msg = msgpack.packb(pack_data)
       return str(encoded_msg)
   def parse_msg(self,data):
       """Parse a raw msgpack message

       This method assumes the message is encoded as a list or tuple of (msg_type,msg_data).

       For performance reasons garbage collection is turned off while parsing. Should an exception occur while parsing, self.log_debug() is invoked.
       
       If an exception does occur, this method might return None.

       Args:
         data (str): The raw packet to parse

       Returns:
         tuple: a tuple of (msg_type,msg_data)
       """
       msg_type,msg_data = None,None
       gc.disable()
       try:
         decoded_msg = msgpack.unpackb(data)
         msg_type    = decoded_msg[0]
         msg_data    = decoded_msg[1]
       except Exception,e:
          self.log_debug('Error during msgpack decoding',exc=e) 
       gc.enable()
       return (msg_type,msg_data)

