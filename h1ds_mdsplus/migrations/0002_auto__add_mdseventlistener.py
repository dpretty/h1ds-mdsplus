# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MDSEventListener'
        db.create_table('h1ds_mdsplus_mdseventlistener', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('server', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
        ))
        db.send_create_signal('h1ds_mdsplus', ['MDSEventListener'])


    def backwards(self, orm):
        
        # Deleting model 'MDSEventListener'
        db.delete_table('h1ds_mdsplus_mdseventlistener')


    models = {
        'h1ds_mdsplus.mdseventinstance': {
            'Meta': {'ordering': "('-time',)", 'object_name': 'MDSEventInstance'},
            'data': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'h1ds_mdsplus.mdseventlistener': {
            'Meta': {'object_name': 'MDSEventListener'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'event_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'server': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'h1ds_mdsplus.mdsplustree': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MDSPlusTree'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['h1ds_mdsplus']
