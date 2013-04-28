"""MDSplus specific utils for H1DS."""

import datetime
import numpy as np
from django.conf import settings

from h1ds_core.base import BaseURLProcessor, BaseNode
import MDSplus
from MDSplus import TdiException
from MDSplus._treeshr import TreeNoDataException

MDS_TREE = MDSplus.Tree(settings.DEFAULT_TREE, 0, 'READONLY')

class URLProcessor(BaseURLProcessor):
    """MDSplus URLProcessor"""
    
    def urlized_path(self): 
        url_path = self.path.strip('.:').replace('.','/').replace(':','/')
        return url_path
    
    def deurlize_path(self, url_path):
        path = url_path.strip(':/').replace('/','.')
        return path

def get_url_processor_for_mds_node(mds_node):
    """Get URLProcessor instance for a MDSplus node."""
    
    return URLProcessor(tree=mds_node.getLocalTree(),
                        shot=mds_node.tree.shot,
                        path=mds_node.getLocalPath())

class Node(BaseNode):
    """Node class customised for MDSplus data."""
            
    def __init__(self, *args, **kwargs):
        try:
            self.mds_node = kwargs.pop('mds_node')
        except KeyError:
            self.mds_node = None
        if type(self.mds_node) != type(None):
            u_p = get_url_processor_for_mds_node(self.mds_node)
            kwargs['url_processor'] = u_p
        super(Node, self).__init__(*args, **kwargs)
            
    def get_raw_data(self):
        mds_node = self.get_mds_node()
        try:
            raw_data = mds_node.getData().data()
        except (TreeNoDataException, TdiException, AttributeError):
            raw_data = None
        return raw_data

    def get_raw_dim(self):
        """Get dimension of raw data (i.e. no filters)."""
        mds_node = self.get_mds_node()
        try:
            shape = mds_node.getShape()
            if len(shape) == 1:
                raw_dim = mds_node.getDimensionAt().data()
            else:
                dim_list = []
                for i in range(len(shape)):
                    dim_list.append(mds_node.getDimensionAt(i).data())
                raw_dim = np.array(dim_list)
        except MDSplus.TdiException:
            raw_dim = None
        return raw_dim
    
    def get_mds_node(self):
        """Get the corresponding MDSplus node for this H1DS tree node."""
        
        if type(self.mds_node) == type(None):
            mds_tree = MDSplus.Tree(str(self.url_processor.tree), # force str rather than unicode. unicode hits mds bug?
                                    self.url_processor.shot)
            if self.url_processor.path == "":
                default_node = "\\{}::TOP".format(self.url_processor.tree)
                self.mds_node = mds_tree.getNode(default_node)
            else:
                self.mds_node = mds_tree.getNode(self.url_processor.path)
        return self.mds_node
    
    def get_parent(self):
        node = self.get_mds_node()
        parent = node.getParent()
        if type(parent) == type(None):
            return None
        return Node(mds_node=parent)

    def get_children(self):
        node = self.get_mds_node()
        # HACK - MDS python library seems to have a bug in getDescendants()
        # see http://www.mdsplus.org/bugzilla/show_bug.cgi?id=49
        # for now, do a manual join of children and members.
        children = []
        mds_children = node.getChildren()
        if type(mds_children) != type(None):
            children.extend([Node(mds_node=desc) for desc in mds_children])
        mds_members = node.getMembers()
        if type(mds_members) != type(None):
            children.extend([Node(mds_node=desc) for desc in mds_members])
        return sorted(children, key = lambda n: n.get_short_name())
            
    def get_short_name(self):
        node = self.get_mds_node()
        return node.getNodeName()

    def get_data_time(self):
        node = self.get_mds_node()
        data_time = node.getTimeInserted()._getDate()
        return datetime.datetime.strptime(str(data_time), "%d-%b-%Y %H:%M:%S.%f")

    def get_metadata(self):
        mds_node = self.get_mds_node()
        metadata = {}
        try:
            metadata['Acquisition time'] = self.get_data_time()
        except:
            pass
        try:
            metadata['MDSplus path'] = mds_node.getFullPath()
        except:
            pass
        try:
            metadata['MDSplus dtype'] = mds_node.getDtype()
        except:
            pass
        try:
            metadata['MDSplus usage'] = mds_node.getUsage()
        except:
            pass
        return metadata
    
def get_latest_shot(tree_name = None):
    """Get latest shot from tree.

    If tree_name is not provided, use the default tree."""
    if tree_name == None:
        # Get default tree.
        tree_name = settings.DEFAULT_TREE
    try:
        latest_shot = MDS_TREE.getCurrent(tree_name)
    except:
        latest_shot = -1
    return latest_shot

