import time, os
import MDSplus
from celery.decorators import task
from h1ds_core.signals import h1ds_signal

@task(track_started=True)
def mds_event_listener(server, event_name, signal_name):
    class LocalMDSEvent(MDSplus.Event):
        def run(self):
            h1ds_signal.send(sender=self, name=signal_name)
            print 'a', self.getName()
    os.environ['mds_event_server'] = server
    event_instance = LocalMDSEvent(event_name)    
    while True:
        time.sleep(10)
