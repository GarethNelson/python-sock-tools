gen_proto.py - generate a protocol from a specification
=======================================================

Overview
--------

The gen_proto.py script takes a JSON document specifying your protocol and combines it with a template to produce a custom python module implementing your protocol.

You simply specify the message types, message type IDs and the expected fields for each message type.

Usage
-----

.. argparse::
   :module: socktools.tools.gen_proto
   :func: get_parser
   :prog: gen_proto.py

JSON specification format
-------------------------

gen_proto.py builds modules from JSON specifications files, for examples see tools/examples/ where you will find a small selection of example protocols.

Each specification file consists of a JSON dictionary containing the following fields:

=============== ========== ============================================================
 Field name      Data type  Description
=============== ========== ============================================================
 protocol_name   string     The name for your protocol
 imports         list       List of python modules to import into the generated module
 protocol_sock   string     Full name of the socket class to base your protocol on
 named_fields    boolean    If true, the handler methods expect a dict
 mixins          list       List of other classes to inherit from (i.e mixins)
 messages        list       List of dictionary objects, see below
=============== ========== ============================================================

Within the messages field you must provide a list of dictionary objects with the following fields:

=============== ========== =======================================================================
 Field name      Data type  Description
=============== ========== =======================================================================
 msg_type_str    string     A string representing this message type, will become python identifier
 msg_type_int    integer    Numeric ID of this message type
 fields          list       A list of strings giving field names in this message type
=============== ========== =======================================================================

After generating your module, you can import it and subclass it to implement the handlers, each handler function will be passed the fields from the message.

It is then up to you to either implement parse_msg() or add one of the mixins and finish off your protocol.

Examples
--------

These examples can be run from the command line:

.. code-block:: shell

    python -m socktools.tools.examples.gen_proto.build_example_chat

.. toctree::
   socktools.tools.examples.gen_proto.build_example_chat
   socktools.tools.examples.gen_proto.chat_server
   socktools.tools.examples.gen_proto.chat_client

Python API
----------

.. automodule:: socktools.tools.gen_proto
    :members:
    :undoc-members:
    :show-inheritance:


.. toctree::
   :maxdepth: 4

