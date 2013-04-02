"""A web interface to the MDSPlus data acquisition system."""

import os
import numpy
import MDSplus
from MDSplus._treeshr import TreeException
from django.db.utils import DatabaseError
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

# populate environ  before other h1ds_mdsplus imports  to avoid circular
# import problem where trees are undefined.
for config_tree in settings.EXTRA_MDS_TREES:
    os.environ[config_tree[0]+"_path"] = config_tree[1]

from h1ds_mdsplus.models import MDSEventListener
from h1ds_mdsplus.tasks import track_latest_shot
from h1ds_mdsplus.utils import URLProcessor, Node, get_latest_shot

MODULE_DOC_NAME = "MDSPlus"
if hasattr(settings, "H1DS_MDSPLUS_ROOT_URL"):
    MODULE_ROOT_URL = settings.H1DS_MDSPLUS_ROOT_URL
else:
    MODULE_ROOT_URL = "mdsplus" 
TEST_TREE_NAME = "test"

def get_trees_from_env(use_config_trees_only=True):
    trees = []
    if use_config_trees_only:
        env_paths = [i[0]+"_path" for i in settings.EXTRA_MDS_TREES]
    else:
        env_paths = [i for i in os.environ.keys() if i.lower().endswith('_path')]
    for path in env_paths:
        tree_name = path[:-5]
        try:
            tree =  MDSplus.Tree(tree_name, 0, 'READONLY')
            trees.append(tree_name)
        except TreeException:
            pass
    return trees

# for h1ds API
def get_trees():
    return get_trees_from_env()


# Start MDSEvent listener tasks
try:
    for event_listener in MDSEventListener.objects.all():
        event_listener.start_listener()

except (DatabaseError, ImproperlyConfigured):
    # A DatabaseError is raised when we  try to syncdb, or migrate the
    # database when  no database  exists. This  appears to  be because
    # syncdb/migrate import the  module, and the module  tries to read
    # the      (non-existant)      database     when      we      call
    # MDSPlusTree.objects.all().
    #
    # ImproperlyConfigured is  raised when no  database is set  in the
    # settings.    e.g.  if   we   import   h1ds_mdsplus  for   sphinx
    # documentation we use the basic  settings.py which doesn't have a
    # database specified which raises this exception.
    #
    # TODO: Find a better solution.
    # 
    # TODO: we have now removed MDSPlusTree - is this still a problem?
    pass

#start latest shot tracker
track_latest_shot.delay()


sql_type_mapping = {
    numpy.float32:"FLOAT",
    numpy.float64:"FLOAT",
    numpy.int32:"INT",
    }
