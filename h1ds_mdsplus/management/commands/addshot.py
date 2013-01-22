from django.core.management.base import BaseCommand
import MDSplus
import numpy
from h1ds_mdsplus import TEST_TREE_NAME
from h1ds_mdsplus.utils import get_latest_shot
from h1ds_mdsplus.management.commands._utils import create_test_shot

import os, sys

class Command(BaseCommand):
    #args = '<treepath>'
    help = 'test command'

    def handle(self, *args, **options):
        latest_shot = get_latest_shot(TEST_TREE_NAME)
        create_test_shot(latest_shot+1, TEST_TREE_NAME)
