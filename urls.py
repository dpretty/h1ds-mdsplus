from django.conf.urls.defaults import *

from views import tree_overview, tree_list, shot_overview

urlpatterns = patterns('',
                       url(r'^$', tree_list, name="mds-tree-list"),
                       url(r'^(?P<tree>[^/]+)/$', tree_overview, name="mds-tree-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', shot_overview, name="mds-shot-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<path>.*)/$', shot_overview, name="mds-path-detail"),
                       )
