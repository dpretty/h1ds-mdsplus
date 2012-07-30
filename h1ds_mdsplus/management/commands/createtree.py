from django.core.management.base import BaseCommand
import os, sys
import MDSplus
import numpy

SIGNAL_LENGTH = 2**16

def create_tree(tree_path):
    if not os.path.exists(tree_path):
        os.mkdir(tree_path)
    os.environ['test_path'] = tree_path
    for shot_number in xrange(1, 4):
        t = MDSplus.Tree('test', shot_number, mode="NEW")
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

        t.setCurrent('test', shot_number)
        t.write()

class Command(BaseCommand):
    args = '<treepath>'
    help = 'Creates a test mds tree at treepath'

    def handle(self, *args, **options):
        create_tree(args[0])
