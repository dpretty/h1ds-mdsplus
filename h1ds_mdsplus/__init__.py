"""A web interface to the MDSPlus data acquisition system."""

import os
import numpy
import MDSplus
from MDSplus._treeshr import TreeException
from django.db.utils import DatabaseError
from django.conf import settings
from h1ds_mdsplus.models import MDSPlusTree, MDSEventListener

MODULE_DOC_NAME = "MDSPlus"



"""
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
"""

for config_tree in settings.EXTRA_MDS_TREES:
    os.environ[config_tree[0]+"_path"] = config_tree[1]

def get_trees_from_env():
    trees = []
    env_paths = [i for i in os.environ.keys() if i.lower().endswith('_path')]
    for path in env_paths:
        tree_name = path[:-5]
        try:
            tree =  MDSplus.Tree(tree_name, 0, 'READONLY')
            trees.append(tree_name)
        except TreeException:
            pass
    return trees


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


sql_type_mapping = {
    numpy.float32:"FLOAT",
    numpy.float64:"FLOAT",
    numpy.int32:"INT",
    }
