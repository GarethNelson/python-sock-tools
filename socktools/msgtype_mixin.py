"""
Python Sock tools: msgtype_mixin.py - mixins to make dealing with message types simpler
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

This module implements a mixin that allows you to reference message types as strings. Higher-level protocols can make use of it to offer a more convenient API.

Normally you'd use this to represent message types as integers, but you can also remap message types to other strings here too.

Additionally, this module has another mixin that adds send_MSGTYPE methods to the socket object for each message type.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

class MsgtypeStrMixin(object):
   """A mixin for referencing message types as strings

   This class should be used together with UDPSock, TCPSock or a child of one of those classes::
   
       class MyClass(MsgtypeStrMixin,UDPSock):
          pass

   If you do not add an actual socket, this class does nothing, it's a mixin.
   
   Keyword args:
      msg_types (dict): maps message types as strings to message type integers (or any other arbitrary object)

   Attributes:
      msg_types (dict): maps message types as strings to message type integers (or any other arbitrary object)
   """
   def __init__(self,msg_types={},**kwargs):
       self.msg_types = self.get_default_msg_types()
       self.msg_types.update(msg_types)
       super(MsgtypeStrMixin,self).__init__(**kwargs)
   def child_setup(self):
       """Setup this mixin

       This method configures the handlers by remapping them to appropriate values from the msg_types variable, saving an extra lookup at runtime.

       Should a handler be specified directly as an integer or a handler be specified for a message type that does not exist, it will be left as-is.
       """
       new_handlers = {}
       for k,v in self.handlers.items():
           if self.msg_types.has_key(k):
              new_handlers[self.msg_types[k]] = v
           else:
              new_handlers[k] = v
       self.handlers = new_handlers
       super(MsgtypeStrMixin,self).child_setup()
   def add_handler(self,msg_type,handler,exclusive=False):
       """See base_sock.py for full details
       
       The mixin adds a msg_types lookup and uses the value from msg_types if found. Otherwise this method is identical to the default add_handler().
       """
       if self.msg_types.has_key[msg_type]: msg_type=msg_types[msg_type]
       super(MsgtypeStrMixin,self).add_handler(msg_type,handler,exclusive=exclusive)
   def get_default_msg_types(self):
       """Get a default msg_types dict
       
       When inheriting from this class you should override this method and setup appropriate message types. Like get_default_handlers() children should always call this method.
       
       The default implementation returns an empty dict

       Returns:
          dict: a dict mapping message type strings to any other data type (integer is usual)
       """
       return {}

class _msgtype_sender:
   def __init__(self,msg_type,sock):
       self.msg_type = msg_type
       self.sock     = sock
   def __call__(self,*args,**kwargs):
       to_peer = None
       if kwargs.has_key('to_peer'):
          to_peer = kwargs['to_peer']
       if len(args)>0:
          self.sock.send_msg(self.msg_type,args,to_peer=to_peer)
          return
       self.sock.send_msg(self.msg_type,kwargs,to_peer=to_peer)

class MsgtypeSendMixin(object):
   """A mixin that adds send_MSGTYPE methods to the socket
   
   This MUST be used with MsgtypeStrMixin first otherwise it will not work::
       
       class MyClass(MsgtypeSendMixin,MsgtypeStrMixin,UDPSock):
             pass
   
   You will of course also need to setup your message types by passing an appropriate dict to the constructor or by overriding get_default_msg_types().
   
   If everything works the object will magically acquire a bunch of send_MSGTYPE methods: 1 per msg_types entry. Note that for performance reasons this is NOT dynamic.

   The send_MSGTYPE methods will pass all of their arguments to send_msg()

   """
   def child_setup(self):
       """Setup this mixin
       
       This is where the black magic happens.
   
       """
       for k,v in self.msg_types.items():
           setattr(self,'send_%s' % k,_msgtype_sender(v,self))
       super(MsgtypeSendMixin,self).child_setup()


