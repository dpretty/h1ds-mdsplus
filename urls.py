from django.conf.urls.defaults import *

from views import tree_overview, tree_list, node, request_shot, request_url, mds_event, list_events, latest_shot, mds_navigation_subtree

urlpatterns = patterns('',
                       url(r'^$', tree_list, name="mds-tree-list"),
                       url(r'^event/(?P<event_name>[^/]+)/$', mds_event, name="mds-event"),
                       url(r'^latest_shot/(?P<tree_name>[^/]+)/$', latest_shot, name="latest-shot-mds"),
                       url(r'^mds_nav_subtree/(?P<tree_name>[^/]+)/(?P<shot>-?\d+)/(?P<node_id>\d+)/$', mds_navigation_subtree, name="mds-nav-subtree"),
                       url(r'^events/$', list_events, name="mds-event-list"),
                       url(r'^request_shot$', request_shot, name="mds-request-shot"),
                       url(r'^request_url$', request_url, name="mds-request-url"),
                       url(r'^(?P<tree>[^/]+)/$', tree_overview, name="mds-tree-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', node, name="mds-root-node"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<path>.*)/$', node, name="mds-node"),
                       )

