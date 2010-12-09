from django.conf.urls.defaults import *

from views import tree_overview, tree_list, node, request_shot, request_url

urlpatterns = patterns('',
                       url(r'^$', tree_list, name="mds-tree-list"),
                       url(r'^request_shot$', request_shot, name="mds-request-shot"),
                       url(r'^request_url$', request_url, name="mds-request-url"),
                       url(r'^(?P<tree>[^/]+)/$', tree_overview, name="mds-tree-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', node, name="mds-root-node"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<path>.*)/$', node, name="mds-node"),
                       )
