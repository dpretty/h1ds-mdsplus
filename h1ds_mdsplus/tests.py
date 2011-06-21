import unittest
from h1ds_mdsplus.models import MDSPlusTree

def get_dtypes(node):
    print repr(node)
    output_dtypes = [[repr(node.dtype), repr(node)]]
    d_list = node.getDescendants()
    if type(d_list) == MDSplus.treenode.TreeNodeArray:
        for d in d_list:
            output_dtypes.extend(get_dtypes(d))
    return output_dtypes

class NodeUnitTest(unittest.TestCase):
    """Check that each node in the most recent shot can return HTML."""

    def test_html(self):
        # get root node of default tree, latest shot.
        django_mds_tree = MDSPlusTree.objects.all()[0]
