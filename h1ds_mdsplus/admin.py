from django.contrib import admin
from models import MDSEventListener, ListenerSignals, UserSignal

class ListenerSignalsInline(admin.TabularInline):
    model = ListenerSignals
    extra = 1

class MDSEventListenerAdmin(admin.ModelAdmin):
    #filter_horizontal = ('h1ds_signal',)
    inlines = (ListenerSignalsInline,)

admin.site.register(MDSEventListener, MDSEventListenerAdmin)


class UserSignalAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserSignal, UserSignalAdmin)

