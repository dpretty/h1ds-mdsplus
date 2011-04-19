from django.db import models
import MDSplus

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

    def __unicode__(self):
        return unicode("%s@%s" %(self.event_name, self.server))
    

    def save(self, *args, **kwargs):
        super(MDSEventListener, self).save(*args, **kwargs)
        self.tmp = mds_event_listener.delay(self.server, self.event_name)
        #import os
        #os.environ['mds_event_server'] = self.server
        #self.event_instalce = MDSEvent(self.event_name)
 
       

"""    
os.environ['mds_event_server'] = 'prl60.anu.edu.au:8000'

event_name = sys.argv[1]

def send_to_url(mdsevent):
    url = 'http://h1svr.anu.edu.au/mdsplus/event/%s/' %mdsevent.getName()
    data = unicode(mdsevent.getData())
    params = urllib.urlencode({'data':data})
    f = urllib2.urlopen(url,params)

class MDSEvent(MDSplus.Event):
    def run(self):
        print self.getName()
        #send_to_url(self)

event_instance = MDSEvent(event_name)

while True:
    time.sleep(10)

"""
