#!/usr/bin/env python
"""
Listen to incoming MDS events and forward signals to webserver
"""


import os, datetime, MDSplus, urllib, urllib2, time, sys

#os.environ['mds_event_server'] = 'prl60.anu.edu.au:8501'
os.environ['mds_event_server'] = 'h1data.anu.edu.au:8000'

event_name = sys.argv[1]

def send_to_url(mdsevent):
    url = 'http://h1svr.anu.edu.au/mdsplus/event/%s/' %mdsevent.getName()
    data = unicode(mdsevent.getData())
    params = urllib.urlencode({'data':data})
    f = urllib2.urlopen(url,params)

class MDSEvent(MDSplus.Event):
    def run(self):
        print self.getName()
        send_to_url(self)

event_instance = MDSEvent(event_name)

while True:
    time.sleep(10)
