"""
Python Sock tools: example_chat.py - builds an example chat server implementation using gen_proto
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
"""

import eventlet
import os
from socktools.tools import gen_proto

if __name__=='__main__':
   my_path       = os.path.dirname(os.path.abspath(__file__))
   template_path = gen_proto.get_default_template_path()
   specfile_path = os.path.join(my_path,'chat_protocol.json')
   output_path   = os.path.join(my_path,'generated.py')
   print 'Rendering generated protocol module to %s' % output_path
   gen_proto.render_module(specfile_path,template_path,output_path)

   print 'You should now be able to run the chatserver example by doing the following:'
   print '\t python -m socktools.tools.examples.gen_proto.chat_server'
   
   print 'Then start 2 instances of the client to test it all out:'
   print '\t python -m socktools.tools.examples.gen_proto.chat_client'
   
