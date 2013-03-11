import time, os
import logging

from django.conf import settings
import MDSplus
from celery.decorators import task
from h1ds_core.signals import h1ds_signal

logger = logging.getLogger(__name__)

@task(track_started=True)
def mds_event_listener(server, event_name, h1ds_signal_instance):
    class LocalMDSEvent(MDSplus.Event):
        def run(self):
            h1ds_signal.send(sender=self, h1ds_sig=h1ds_signal_instance, value=None)
    os.environ['mds_event_server'] = server
    event_instance = LocalMDSEvent(event_name)    
    while True:
        time.sleep(10)


def do_ping_shot_tracker():
    t =  MDSplus.Tree()
    current_shot = t.getCurrent(settings.DEFAULT_MDS_TREE)
    class NewShotEvent(object):
        def __init__(self, shot_number):
            self.shot_number = shot_number
        def send_event(self):
            h1ds_signal(sender=self, h1ds_signal="new_shot", value=self.shot_number)
    while True:
        time.sleep(settings.SHOT_TRACKER_PING_INTERVAL)
        new_shot_number = t.getCurrent(settings.DEFAULT_MDS_TREE)
        if new_shot_number != current_shot:
            new_shot_event = NewShotEvent(new_shot_number)
            new_shot_event.send_event()
            current_shot = new_shot_number
            logger.debug("NEW SHOT: {}".format(current_shot))
            


@task(track_started=True)
def track_latest_shot():
    if not hasattr(settings, "SHOT_TRACKER"):
        return
    if settings.SHOT_TRACKER == "ping":
        do_ping_shot_tracker()
