# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'UserSignal'
        db.delete_table(u'h1ds_mdsplus_usersignal')


    def backwards(self, orm):
        # Adding model 'UserSignal'
        db.create_table(u'h1ds_mdsplus_usersignal', (
            ('ordering', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('shot', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('is_fixed_to_shot', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=2048)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('h1ds_mdsplus', ['UserSignal'])


    models = {
        u'h1ds_core.h1dssignal': {
            'Meta': {'object_name': 'H1DSSignal'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'h1ds_mdsplus.listenersignals': {
            'Meta': {'object_name': 'ListenerSignals'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'listener': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['h1ds_mdsplus.MDSEventListener']"}),
            'signal': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['h1ds_core.H1DSSignal']"})
        },
        u'h1ds_mdsplus.mdseventlistener': {
            'Meta': {'object_name': 'MDSEventListener'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'event_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'h1ds_signal': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['h1ds_core.H1DSSignal']", 'through': u"orm['h1ds_mdsplus.ListenerSignals']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'server': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['h1ds_mdsplus']