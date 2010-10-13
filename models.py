from django.db import models

class MDSPlusTree(models.Model):
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=100)
    description = models.CharField(max_length=500)

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        ordering = ('name',)

    def save(self, *args, **kwargs):
        super(MDSPlusTree, self).save(*args, **kwargs)
        import os
        os.environ['%s_path' %self.name] = self.path
