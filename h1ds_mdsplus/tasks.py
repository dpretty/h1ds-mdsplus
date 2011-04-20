import time, os
import MDSplus
from celery.decorators import task

@task(track_started=True)
def mds_event_listener(server, event_name):
    class LocalMDSEvent(MDSplus.Event):
        def run(self):
            print self.getName()
    os.environ['mds_event_server'] = server
    event_instance = LocalMDSEvent(event_name)    
    while True:
        time.sleep(10)
