"""
Python Sock tools: json_mixin.py - mixins to handle JSON encoding/decoding
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

This module implements a mixin that implements the parse_msg() method using JSON. Messages are assumed to be JSON lists of (msg_type,msg_data).

You may send JSON messages using send_msg().

"""

import eventlet
import json
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

class JSONParseMixin(object):
   """A mixin for parsing JSON messages

   This class is most suited to the websocket server:

.. code-block:: python

    class MyClass(JSONParseMixIn,WSGIWebsocketSock):
          pass
   
   """
   def serialise_msg(self,msg_type,msg_data):
       """Serialise a message in JSON format

       This method serialises msg_data (which should be a dict or sequence) into a JSON list object of (msg_type,msg_data).

       Args:
          msg_type (int): the message type as an integer
          msg_data (dict): usually a dict, the actual message contents
       """
       msg_data  = [msg_type,msg_data]
       json_data = json.dumps(msg_data)
       return json_data

   def parse_msg(self,data):
       """Parse a raw message in JSON format

       This method assumes the message is encoded as a JSON list object of (msg_type,msg_data).
       
       Warning:
          Catching exceptions for malformed packets is left up to caller - ultimately this means your application code.

       Args:
         data (str): The raw packet to parse

       Returns:
         tuple: a tuple of (msg_type,msg_data)
       """
       json_data = json.loads(data)
       msg_type  = json_data[0] # in theory we could just pass json_data as-is, but that makes silly assumptions
       msg_data  = json_data[1]
       return (msg_type,msg_data)

