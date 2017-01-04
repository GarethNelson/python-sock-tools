The files in this directory are examples for the gen_proto tool.

At present only one such example exists: a JSON-based chat protocol.

To build it do the following:

    $ python -m socktools.tools.examples.gen_proto.build_example_chat

You may then run the chat server or chat client. For the server use the following command:

    $ python -m socktools.tools.examples.gen_proto.chat_server

To test the chat server start 1 or more instances of the client:

    $ python -m socktools.tools.examples.gen_proto.chat_client

