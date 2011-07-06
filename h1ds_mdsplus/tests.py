from django.utils import unittest
from django.test.client import Client

from h1ds_mdsplus.models import MDSPlusTree
from h1ds_mdsplus.wrappers import mds_to_url

import MDSplus

def get_nodes(node):
    output_nodes = [node]
    d_list = node.getDescendants()
    if type(d_list) == MDSplus.treenode.TreeNodeArray:
        for d in d_list:
            output_nodes.extend(get_nodes(d))
    return output_nodes


class NodeUnitTest(unittest.TestCase):
    """Check that each node in the most recent shot can return HTML."""

    def setUp(self):
        self.tree = MDSPlusTree.objects.create(name="h1data", description="test data", path="/home/dave/data", display_order=10)
        self.client = Client()
        
    def test_html(self):
        # get root node of default tree, latest shot.
        for shot in [0]:
            django_mds_tree = MDSPlusTree.objects.all()[0]
            mds_tree = django_mds_tree.get_tree(0)
            root_node = mds_tree.getNode("\\%s::top" %django_mds_tree.name)
            node_list = get_nodes(root_node)
            for node_i, node in enumerate(node_list):
                print node_i+1, len(node_list)
                print node
                print node.getFullPath()
                print '--'
                response = self.client.get(mds_to_url(node))
                self.assertEqual(response.status_code, 200)
