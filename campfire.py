#!/usr/bin/env python

"""
Class to notify user of updates in campfire
"""
import pinder
import time
import socket
import httplib2
from threading import Thread
from optparse import OptionParser


class CampfireRoomMonitor(Thread):
  """
  Class for monitoring and notifing the user of new messages in campfire.
  """
  
  class NoSuchRoomException(Exception): pass
  class WrongUsernameOrPassword(Exception): pass
  
  def __init__(self, subdomain, username, password, room, interval, *args, **kwargs):
    Thread.__init__(self, *args, **kwargs)
    self._campfire = pinder.Campfire(subdomain)
    if not self._campfire.login(username, password):
      raise self.WrongUsernameOrPassword("The password or username was incorrect.")
    
    self._room = self._campfire.find_room_by_name(room)
    self._interval = interval
    if not isinstance(self._room, pinder.Room):
      raise self.NoSuchRoomException("%s does not exist, check the spelling of the room name" % room)
      
    
    self._transcripts_ids = [] # Stores last transcript, used for diffing 
    
  def run(self):
    while True:
      try:
        # Check transcript, if new message exist notifiy user
        last_date = self._room.transcripts()[0] # Get Last transcript date
        
        for new_msg in self.get_new_messages(self._room.transcript(last_date)):
          self.notify(new_msg)

        time.sleep(self._interval)
      except socket.timeout:
        print "Connection timed out"

  def notify(self, msg):
    """
    Creates notification to display to the user
    """
    import pynotify
    if not pynotify.is_initted():
      if not pynotify.init("campfire-notifications"):
        sys.exit(1) # Error
      
    self.push_notification("%s in %s" % (msg['person'], self._room.name), msg['message']) 
  
  def push_notification(self, title, body):
    """
    Addes a message to user notification
    """
    import pynotify
    import gtk
    n = pynotify.Notification (title, body);
    n.set_icon_from_pixbuf(gtk.gdk.pixbuf_new_from_file("campfire-logo.png"))
    n.show ()
  
  def get_new_messages(self, transcripts):
    """
    Yields new messages that have not yet been sent
    """
    if len(self._transcripts_ids) == 0:
      for msg in transcripts:
        self._transcripts_ids.append(msg["id"])
    else:
      for msg in transcripts:
        if not msg["id"] in self._transcripts_ids:
          self._transcripts_ids.append(msg["id"])
          if not msg['user_id'] == None:
            yield msg

class CampfireMonitor(object):
  def __init__(self, subdomain, username, password, rooms, interval):
    self._rooms = {}
    
    for room in rooms:
      self._rooms[room] = CampfireRoomMonitor(subdomain, username, password, room, interval)
      self._rooms[room].start()
    
    for room, rThread in self._rooms.items():
      rThread.join()

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-s", "--subdomain", dest="subdomain", help="The subdomain that is used to connect to campfire")
  parser.add_option("-u", "--username", dest="username", help="Username to login in to campfire")
  parser.add_option("-p", "--password", dest="password", help="Password to login in to campfire")
  parser.add_option("-r", "--room", action="append", dest="rooms", help="Room to monitor, this can repeat to monitor more then one room")
  parser.add_option("-i", "--interval", type="int", dest="interval", default=5, help="Number of seconds beetween checks")
  
  (options, args) = parser.parse_args()
  CampfireMonitor(options.subdomain, options.username, options.password, options.rooms, options.interval)

