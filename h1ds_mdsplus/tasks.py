import time, os
import logging

from django.conf import settings
import MDSplus
from celery.decorators import task
from h1ds_core.signals import h1ds_signal, NewShotEvent
from h1ds_core.models import H1DSSignal

logger = logging.getLogger("default")

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


def do_ping_shot_tracker():
    t =  MDSplus.Tree(settings.DEFAULT_TREE, 0, 'READONLY')
    current_shot = t.getCurrent(settings.DEFAULT_TREE)
    #class NewShotEvent(object):
    #    def __init__(self, shot_number):
    #        self.shot_number = shot_number
    #    def send_event(self):
    #        h1ds_signal.send(sender=self,
    #                         h1ds_sig=new_shot_signal, value=self.shot_number)
    while True:
        time.sleep(settings.SHOT_TRACKER_PING_INTERVAL)
        new_shot_number = t.getCurrent(settings.DEFAULT_TREE)
        if new_shot_number != current_shot:
            new_shot_event = NewShotEvent(new_shot_number)
            new_shot_event.send_event()
            current_shot = new_shot_number
            logger.debug("NEW SHOT: {}".format(current_shot))
            


@task(track_started=True)
def track_latest_shot():
    if not hasattr(settings, "SHOT_TRACKER"):
        return
    # if there is no new_shot instance of H1DSSignal, create it.
    #new_shot_inst, c = H1DSSignal.objects.get_or_create(name="new_shot",
    # description="New Shot")
    #logger.debug("new_shot_instance: {}".format(str(new_shot_inst)))

    if settings.SHOT_TRACKER == "ping":
        #do_ping_shot_tracker(new_shot_inst)
        do_ping_shot_tracker()
