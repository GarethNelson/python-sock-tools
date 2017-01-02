"""
Python Sock tools: ws_dumper.py - dumps messages from a websocket to stdout
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

To test this, connect with wscat to localhost and send properly formatted JSON messages.

By default, this example binds to localhost on port 31337 and uses json_mixin to parse messages.

I suggest using wscat to test it, open 2 terminals and copy the below:

.. code-block:: shell

    $ python -m socktools.examples.ws_dumper
    hit ctrl-c to quit
    (18720) wsgi starting up on http://127.0.0.1:31337


After running the server, use wscat to send a test message:

.. code-block:: shell

    $ wscat -c ws://localhost:31337
    connected (press CTRL+C to quit)
    > [0, "test"]    

You should see the message dumped by the server:

.. code-block:: shell

    (18720) accepted ('127.0.0.1', 45150)
    Got raw data: [0, "test"]
    Got message type 0 from 127.0.0.1:45150: test
    Putting parsed message type 0 from 127.0.0.1:45150 on queue: test

Note:
  This example uses eventlet's WSGI server, this is fine for testing but should NOT be used for production
"""

import eventlet
eventlet.monkey_patch() # this should be done in all modules that use eventlet as the first import, just in case

from socktools.wsgi_websocket_sock import WSGIWebsocketSock
from socktools.json_mixin import JSONParseMixin

class WSDumperProtocol(JSONParseMixin,WSGIWebsocketSock):
   """Websocket dumper

   Simply dumps every received message to stdout, messages are JSON lists of (msg_type,msg_data).
   """
   def handle_all(self,from_addr,msg_type,msg_data):
       print 'Got message type %s from %s:%s: %s' % (msg_type,from_addr[0],from_addr[1],str(msg_data))
       return (from_addr,msg_type,msg_data)

if __name__=='__main__':
   from eventlet import wsgi
   ws = WSDumperProtocol()

   ws.start_server()
   print 'hit ctrl-c to quit'
   server = wsgi.server(eventlet.listen(('127.0.0.1',31337)),ws.get_wsgi_func())
