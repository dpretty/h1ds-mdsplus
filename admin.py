from django.contrib import admin
from models import MDSPlusTree, MDSEventInstance

class MDSPlusTreeAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSPlusTree, MDSPlusTreeAdmin)


class MDSEventInstanceAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSEventInstance, MDSEventInstanceAdmin)
