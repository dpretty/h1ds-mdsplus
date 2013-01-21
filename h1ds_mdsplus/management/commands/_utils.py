import numpy
import MDSplus
from h1ds_mdsplus import TEST_TREE_NAME

SIGNAL_LENGTH = 2**16

mdsplus_dtypes = [
    i[6:] for i in MDSplus._mdsdtypes.__dict__.keys() if i.startswith('DTYPE_')
    ]


def create_test_shot(shot_number, tree_name=TEST_TREE_NAME):
    """Create a shot using all of the MDSplus data types.

    Note: this is incomplete, so not all datatypes are present yet.
    """
    t = MDSplus.Tree(tree_name, shot_number, mode="NEW")
    t.addNode('node_A')
    t.addNode('node_B')

    node_a = t.getNode('node_A')
    node_a.setUsage("SIGNAL")
    node_a.addTag("tag_A")

    node_a.addNode('node_AA')
    node_a.addNode('node_AB')

    sig = MDSplus.Signal(MDSplus.makeArray(numpy.random.poisson(lam=10, size=SIGNAL_LENGTH)), 
                         None, MDSplus.makeArray(0.1*numpy.arange(SIGNAL_LENGTH)))
    node_a.putData(sig)

    node_aa = t.getNode('\\test::top.node_A.node_AA')
    node_aa.addTag("tag_AA")
    node_aa.addNode("node_AAA")

    node_ab = t.getNode('\\test::top.node_A.node_AB')
    str_data = MDSplus.StringArray(["elmt1", "elmt2"])
    node_ab.putData(str_data)
    
    t.setCurrent('test', shot_number)
    t.write()
