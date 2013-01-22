import time, os
import MDSplus
from celery.decorators import task
from h1ds_core.signals import h1ds_signal

@task(track_started=True)
def mds_event_listener(server, event_name, h1ds_signal_instance):
    class LocalMDSEvent(MDSplus.Event):
        def run(self):
            h1ds_signal.send(sender=self, h1ds_sig=h1ds_signal_instance)
    os.environ['mds_event_server'] = server
    event_instance = LocalMDSEvent(event_name)    
    while True:
        time.sleep(10)


@task(track_started=True)
def track_latest_shot():
    pass
