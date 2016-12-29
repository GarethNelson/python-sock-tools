Basic overview
==============

How socktools is organised
--------------------------

socktools is organised into a set of basic classes that handle spawning of eventlet greenthreads and the low-level communication via socket.socket objects. On top of these basic classes applications are built 
by inheriting from the base classes and implementing appropriate handlers for different message types.

To provide nonblocking I/O socktools currently makes use of eventlet and seperates message encoding and decoding, application logic and low-level primitives into different greenthreads.

.. toctree::
   :maxdepth: 4

