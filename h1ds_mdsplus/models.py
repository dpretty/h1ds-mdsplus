"""Models to store MDSplus events."""
from django.db import models
from celery.task.control import inspect

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
        for signal in self.h1ds_signal.all():
            signals[signal.name] = {'active':False,
                               'class':signal,
                               'args':u"(u'{}', u'{}', u'{}')".format(
                                    self.server,
                                    self.event_name,
                                    signal.name)}
        active_workers = inspect().active()
        if active_workers != None:
            for worker in active_workers.keys():
                for active_task in active_workers[worker]:
                    for sig in signals.keys():
                        if (active_task['name'] == task_name and
                            active_task['args'] == signals[sig]['args']):
                            signals[sig]['active'] = True

        for sig in signals.keys():
            if not signals[sig]['active']:
                self.listener = mds_event_listener.delay(self.server,
                                                         self.event_name,
                                                         signals[sig]['class'])

    def save(self, *args, **kwargs):
        super(MDSEventListener, self).save(*args, **kwargs)
        self.start_listener()

class ListenerSignals(models.Model):
    signal = models.ForeignKey(H1DSSignal)
    listener = models.ForeignKey(MDSEventListener)

    def save(self, *args, **kwargs):
        super(ListenerSignals, self).save(*args, **kwargs)
        self.listener.start_listener()

