"""A web interface to the MDSPlus data acquisition system."""

import os
import numpy
from django.db.utils import DatabaseError

from h1ds_mdsplus.models import MDSPlusTree, MDSEventListener

MODULE_DOC_NAME = "MDSPlus"

# load all mdsplus trees into os environment

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



# Start MDSEvent listener tasks
try:
    for event_listener in MDSEventListener.objects.all():
        event_listener.start_listener()

except DatabaseError:
    # A DatabaseError is raised when we try to syncdb,  or migrate the database
    # when no database exists. This appears to be because syncdb/migrate import
    # the module, and the module tries to read the (non-existant) database when
    # we call MDSPlusTree.objects.all(). 
    #
    # TODO: Find a better solution.
    pass


mds_sql_mapping = {
    "DTYPE_FLOAT":"FLOAT",
    "DTYPE_F":"FLOAT",
    }


sql_type_mapping = {
    numpy.float32:"FLOAT",
    numpy.float64:"FLOAT",
    }
