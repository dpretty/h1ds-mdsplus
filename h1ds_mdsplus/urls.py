from django.conf.urls.defaults import *

from h1ds_mdsplus.views import tree_overview, tree_list, node, request_shot, request_url, latest_shot, mds_navigation_subtree, homepage, apply_filter, update_filter, remove_filter

# special urls ()
urlpatterns = patterns('',
                       url(r'^_/apply_filter$', apply_filter, name="apply-filter"),
                       url(r'^_/update_filter$', update_filter, name="update-filter"),
                       url(r'^_/remove_filter$', remove_filter, name="remove-filter"),
                       url(r'^_/request_shot$', request_shot, name="mds-request-shot"),
                       url(r'^_/latest_shot/$', latest_shot, name="mds-latest-shot-for-default-tree"),
                       url(r'^_/latest_shot/(?P<tree_name>[^/]+)/$', latest_shot, name="mds-latest-shot"),
                       )

urlpatterns += patterns('',
                       url(r'^$', homepage, name="h1ds-mdsplus-homepage"),
                       url(r'^trees$', tree_list, name="mds-tree-list"),
                       url(r'^mds_nav_subtree/(?P<tree_name>[^/]+)/(?P<shot>-?\d+)/(?P<node_id>\d+)/$', mds_navigation_subtree, name="mds-nav-subtree"),
                       url(r'^request_url$', request_url, name="mds-request-url"),
                       url(r'^(?P<tree>[^/]+)/$', tree_overview, name="mds-tree-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', node, name="mds-root-node"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<tagname>[^/]+)/$', node, name="mds-tag"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<tagname>[^/]+)/(?P<nodepath>.*)/$', node, name="mds-node"),
                       )

