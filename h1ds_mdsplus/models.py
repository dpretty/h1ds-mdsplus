from django.db import models
from celery.task.control import inspect

import MDSplus

from h1ds_core.models import H1DSSignal
from h1ds_mdsplus.tasks import mds_event_listener



class MDSPlusTree(models.Model):
    """Stores path information for an MDSPlus tree."""
    name = models.CharField(max_length=100, help_text="Tree name to be used with name_path (without _path). e.g. mydata")
    path = models.CharField(max_length=100, help_text="A local path with the MDSplus data files. e.g. /data/mydata")
    description = models.CharField(max_length=500, help_text="You are free to write what you like here (max length is 500 characters).")

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        ordering = ('name',)

    def save(self, *args, **kwargs):
        super(MDSPlusTree, self).save(*args, **kwargs)
        import os
        os.environ['%s_path' %self.name] = self.path


class MDSEventInstance(models.Model):
    """Records an instance of an MDSPlus event."""
    name = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)
    data = models.CharField(max_length=100)


    def __unicode__(self):
        return unicode("%s > %s" %(self.time, self.name))

    
    class Meta:
        ordering = ('-time',)
        get_latest_by = 'time'



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
            signals[s.name] = {'active':False, 'args':u"(u'%s', u'%s', u'%s')" %(self.server, self.event_name, s.name)}
        active_workers = inspect().active()
        if active_workers != None:
            for worker in active_workers.keys():
                for active_task in active_workers[worker]:
                    for sig in signals.keys():
                        if active_task['name'] == task_name and active_task['args'] == signals[sig]['args']:
                            signals[sig]['active'] = True

        for sig in signals.keys():
            if not signals[sig]['active']:
                self.listener = mds_event_listener.delay(self.server, self.event_name, sig)

    def save(self, *args, **kwargs):
        super(MDSEventListener, self).save(*args, **kwargs)
        self.start_listener()

class ListenerSignals(models.Model):
    signal = models.ForeignKey(H1DSSignal)
    listener = models.ForeignKey(MDSEventListener)

    def save(self, *args, **kwargs):
        super(ListenerSignals, self).save(*args, **kwargs)
        self.listener.start_listener()
