from django.contrib import admin
from models import MDSPlusTree, MDSEventListener, ListenerSignals

class MDSPlusTreeAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSPlusTree, MDSPlusTreeAdmin)

class ListenerSignalsInline(admin.TabularInline):
    model = ListenerSignals
    extra = 1

class MDSEventListenerAdmin(admin.ModelAdmin):
    #filter_horizontal = ('h1ds_signal',)
    inlines = (ListenerSignalsInline,)

admin.site.register(MDSEventListener, MDSEventListenerAdmin)


