"""Asynchronous listener for emitting MDS signals to H1DS"""
import time, os
from celery.decorators import task
import MDSplus
from h1ds_core.signals import h1ds_signal

@task(track_started=True)
def mds_event_listener(server, event_name, h1ds_signal_instance):
    class LocalMDSEvent(MDSplus.Event):
        def run(self):
            h1ds_signal.send(sender=self,
                h1ds_sig=h1ds_signal_instance, value=None)
    os.environ['mds_event_server'] = server
    event_instance = LocalMDSEvent(event_name)
    while True:
        time.sleep(10)
