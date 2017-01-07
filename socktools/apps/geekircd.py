"""
Python Sock tools: main.py - entry point for the GeekIRC app
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

This module is the entry point for the GeekIRC app.

The basic architecture of the app is quite simple: a meta socket is used to receive messages from all users on either the websocket interface or IRC. Messages are then rebroadcast as appropriate.

GeekIRC is a daemon so control must be done via the web interface or via base_daemon's rc interface.
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

import os

import socktools
from socktools.daemon import base_daemon

from geekirc import meta_chat
from geekirc import irc_sock

class GeekIRCDaemon(base_daemon.BaseDaemon):
   """ The GeekIRC daemon, also known as geekircd
   
   This is the "meat" of the GeekIRC app, a daemon that provides a web interface with websockets and IRC.

   """
   def do_reload(self):
       self.get_logger().info('Reload requested')
   def run(self):
       self.get_logger().info('Starting geekircd')
       self.chat = meta_chat.MetaChat(logger=self.get_logger())

       self.irc_listener = irc_sock.IRCSock(bind=('0.0.0.0',6667),meta_sock=self.chat,logger=self.get_logger())
       self.irc_listener.start_server()


       self.get_logger().info('Bound IRC socket')

       while self.active:
          eventlet.greenthread.sleep(3600)

if __name__ == '__main__':
    pidfile_path = os.path.join(os.path.expanduser('~'),'.geekircd.pid')
    geekircd = GeekIRCDaemon(pidfile=pidfile_path)
    geekircd.handle_rc()
