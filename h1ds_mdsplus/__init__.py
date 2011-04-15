### load all mdsplus trees into os environment

import os
from django.db.utils import DatabaseError

from h1ds_mdsplus.models import MDSPlusTree

try:
    for tree in MDSPlusTree.objects.all():
        os.environ['%s_path' %tree.name] = tree.path
except DatabaseError:
    # A DatabaseError is raised when we try to syncdb,  or migrate the database
    # when no database exists. This appears to be because syncdb/migrate import
    # the module, and the module tries to read the (non-existant) database when
    # we call MDSPlusTree.objects.all(). 
    #
    # TODO: Find a better solution.
    pass

