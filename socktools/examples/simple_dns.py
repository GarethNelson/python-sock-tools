"""
Python Sock tools: simple_dns.py - a simplistic DNS server example
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

This module implements a simple toy DNS server using dnslib to encode/decode packets. To test it, run this module as a script and then query it on port 31337.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

import dnslib
from socktools.msgtype_mixin import MsgtypeSendMixin
from socktools.msgtype_mixin import MsgtypeStrMixin
from socktools.udp_sock import UDPSock

class DNSProtocol(MsgtypeSendMixin,MsgtypeStrMixin,UDPSock):
   """DNS protocol implementation
   
   This class implements the world's worst DNS server: all hostnames return NXDOMAIN

   """
   def get_default_handlers(self):
       """See base_sock.py
       """
       handlers = {}
       handlers['QUERY'] = [self.handle_query]
       return handlers
   def get_default_msg_types(self):
       return dnslib.OPCODE.reverse # if future versions of dnslib change this, it'll break
       # TODO: make sure it doesn't break
   def handle_query(self,from_addr,msg_type,msg_data):
       """ Responds to DNS queries

       This is a crappy DNS server, so we simply dump the request to stdout and then respond with a standard response
       """
       print 'DNS Request:\n %s\n' % msg_data
       a = msg_data.reply()
       a.header.rcode = dnslib.RCODE.NXDOMAIN
       self.send_raw(a.pack(),to_peer=from_addr)
   def parse_msg(self,data):
       """Parse a raw packet using dnslib
       """
       msg_data = dnslib.DNSRecord.parse(data)
       msg_type = msg_data.header.opcode
       return msg_type,msg_data

if __name__=='__main__':
   import sys
   server = DNSProtocol(bind=('127.0.0.1',31337))
   print 'Hit ctrl-c to quit'
   while True: eventlet.greenthread.sleep(30)
