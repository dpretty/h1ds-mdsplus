from django.db import models

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
