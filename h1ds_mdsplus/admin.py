from django.contrib import admin
from models import MDSPlusTree, MDSEventInstance, MDSEventListener

class MDSPlusTreeAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSPlusTree, MDSPlusTreeAdmin)


class MDSEventInstanceAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSEventInstance, MDSEventInstanceAdmin)

class MDSEventListenerAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSEventListener, MDSEventListenerAdmin)
