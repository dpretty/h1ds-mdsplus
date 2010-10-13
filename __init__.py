### load all mdsplus trees into os environment

import os

from models import MDSPlusTree

for tree in MDSPlusTree.objects.all():
    os.environ['%s_path' %tree.name] = tree.path

