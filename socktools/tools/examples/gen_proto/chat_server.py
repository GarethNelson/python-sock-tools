import eventlet
import generated
import json

class ChatHandlers(generated.ChatProtocol):
   def handle_ping(self,from_addr,ping_id=None):
       pong_data = json.dumps([1,{'ping_id':ping_id}])
       self.send_raw(pong_data,to_peer = from_addr)
   def handle_msg(self,from_addr,msg_text=None):
       msg_data = json.dumps([2,{'msg_text':'%s said %s ' % (from_addr,msg_text)}])
       self.send_raw(msg_data)

if __name__=='__main__':
   chat = ChatHandlers(bind=('127.0.0.1',31337))
   print 'Starting server...'
   chat.start_server()
   print 'Hit ctrl-c to quit'
   while True: eventlet.greenthread.sleep(30)
