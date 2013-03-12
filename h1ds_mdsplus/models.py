from django.contrib.auth.models import User
from django.db import models
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from celery.task.control import inspect

import MDSplus
from MDSplus._treeshr import TreeException

from h1ds_core.models import H1DSSignal
from h1ds_core.signals import h1ds_signal, NewShotEvent
from h1ds_mdsplus.tasks import mds_event_listener

## test
import logging
import time
logger = logging.getLogger("default")
from django.dispatch import receiver

def new_shot_generator():
    _latest_shot = None
    
    @receiver(h1ds_signal, sender=NewShotEvent)
    def update_shot(sender, **kwargs):
        logger.debug("received signal from models.py")
        _latest_shot = int(kwargs['value'])
            
    tmp = _latest_shot
    while True:
        time.sleep(1)
        if tmp != _latest_shot:
            logger.debug("changed shot")
            tmp = _latest_shot
            yield "{}\n".format(_latest_shot)


        
#h1ds_signal.connect(update_shot)
## end test


class MDSEventListener(models.Model):
    """Listens for an MDSplus event from a specified server."""
    event_name = models.CharField(max_length=50)
    server = models.CharField(max_length=100)
    description = models.CharField(max_length = 500, blank=True)
    h1ds_signal = models.ManyToManyField(H1DSSignal, through='ListenerSignals')

    def __unicode__(self):
        return unicode("%s@%s" %(self.event_name, self.server))
    
    def start_listener(self):
        task_name = u'h1ds_mdsplus.tasks.mds_event_listener'
        signals = {}
        for s in self.h1ds_signal.all():
            signals[s.name] = {'active':False, 'class':s, 'args':u"(u'%s', u'%s', u'%s')" %(self.server, self.event_name, s.name)}
        active_workers = inspect().active()
        if active_workers != None:
            for worker in active_workers.keys():
                for active_task in active_workers[worker]:
                    for sig in signals.keys():
                        if active_task['name'] == task_name and active_task['args'] == signals[sig]['args']:
                            signals[sig]['active'] = True

        for sig in signals.keys():
            if not signals[sig]['active']:
                self.listener = mds_event_listener.delay(self.server, self.event_name, signals[sig]['class'])

    def save(self, *args, **kwargs):
        super(MDSEventListener, self).save(*args, **kwargs)
        self.start_listener()

class ListenerSignals(models.Model):
    signal = models.ForeignKey(H1DSSignal)
    listener = models.ForeignKey(MDSEventListener)

    def save(self, *args, **kwargs):
        super(ListenerSignals, self).save(*args, **kwargs)
        self.listener.start_listener()

class UserSignal(models.Model):
    """Save data URLs for user."""

    # TODO: unique together user, name

    user = models.ForeignKey(User, editable=False)
    url = models.URLField(max_length=2048)
    name = models.CharField(max_length=1024)
    ordering = models.IntegerField(blank=True)
    is_fixed_to_shot = models.BooleanField(default=True)
    shot = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return unicode("%s" %(self.name))


class UserSignalForm(ModelForm):
    class Meta:
        model = UserSignal
        fields = ('name','is_fixed_to_shot',)
