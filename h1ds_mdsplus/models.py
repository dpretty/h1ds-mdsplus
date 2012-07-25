from django.contrib.auth.models import User
from django.db import models
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from celery.task.control import inspect

import MDSplus
from MDSplus._treeshr import TreeException

from h1ds_core.models import H1DSSignal
from h1ds_mdsplus.tasks import mds_event_listener




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

    def __unicode__(self):
        return unicode("%s" %(self.name))


class UserSignalForm(ModelForm):
    class Meta:
        model = UserSignal
        fields = ('name',)
