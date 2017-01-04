"""
Python Sock tools: cron_timer.py - a cron-like timer for use in daemon processes
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

This module provides a cron-like timer intended for use in daemon processes. Essentially, it lets you schedule events for every X seconds.

A lot of emphasis is placed on trying to get timings as accurate as possible while still using greenlets instead of full size threads.

To use it, setup the CronTimer class and configure your timed events then in your main loop call start_timer() and end_timer() before and after your other code.
If you do not call end_timer() your scheduled events will not run.
"""
import eventlet
eventlet.monkey_patch()
import time

class CronTimer:
   """Cron-like timer for daemon processes
   
   This class implements the cron-like timer for daemon processes. Events are scheduled to occur at a set frequency by registering them along with the time delay between function invocations.

   In other words, if you wanted to schedule a function to run every hour you'd use a time delay of 3600.

   Keyword args:
      scheduled_events (dict): Maps time delays to functions
   """
   def __init__(self,scheduled_events={}):
       self.scheduled_events = self.get_default_events()
       self.scheduled_events.update(scheduled_events)
       self.delays             = self.get_sorted_delays()
       self.pool               = eventlet.GreenPool(1000)
       self.diff               = 0
       self.start_time         = time.time()
       self.end_time           = self.start_time
       self.last_delays        = {}
       self.update_events()
   def get_default_events(self):
       """Override this to add your own default events

       This method is provided for the use of child classes and simply returns an events dict mapping time delays to lists of functions.

       The default implementation returns an empty dict.

       Note that you should NOT put the same callback in 2 different delays.

       Returns:
          dict: maps time delays to lists of functions
       """
       return {}
   def get_sorted_delays(self):
       """Returns a sorted list of delays
       
       This method sorts the current scheduled events and returns them in a list starting with smallest first.

       Returns:
          list: list of time delays starting from the smallest first
       """
       delays = self.scheduled_events.keys()
       delays.sort()
       return delays
   def update_events(self):
       """Updates all internal state

       Call this method after updating the scheduled_events dict
       """
       self.delays       = self.get_sorted_delays()
       for d in self.delays:
           self.last_delays[d] = self.start_time
   def start_timer(self):
       """Starts the main loop timer

       To keep the timing accurate the main loop iterations are timed and the actual delay is calculated taking the main loop time into account

       """

       self.start_time = time.time()
   def end_timer(self):
       """Ends the main loop timer and runs scheduled events
       
       This method should be called at the end of your main loop in order to run the scheduled events.
       """
       self.end_time = time.time()
       self.diff     = self.end_time - self.start_time

       for delay in self.delays:
           if (self.end_time - self.last_delays[delay]) >= delay:
              for cb in self.scheduled_events[delay]:
                  cb()
              self.last_delays[delay] = time.time()

if __name__=='__main__':
   import random
   def five_a():
       print 'Every 5 seconds: A, time is %s' % time.ctime()
   def five_b():
       print 'Every 5 seconds: B, time is %s' % time.ctime()
   def fifteen():
       print 'Every fifteen seconds! time is %s' % time.ctime()

   # a simple test
   cron = CronTimer(scheduled_events={5:[five_a,five_b],15:[fifteen]})
   while True:
      cron.start_timer()
      eventlet.greenthread.sleep(random.randint(1,10)/10.0) # simulate doing stuff with variable timeframes
      cron.end_timer()
