from django.contrib import admin
from models import MDSPlusTree

class MDSPlusTreeAdmin(admin.ModelAdmin):
    pass

admin.site.register(MDSPlusTree, MDSPlusTreeAdmin)

