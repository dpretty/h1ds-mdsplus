from django.conf.urls.defaults import *

from h1ds_mdsplus.views import request_shot, latest_shot, homepage, apply_filter, update_filter, remove_filter
from h1ds_mdsplus.views import NodeView, AJAXNodeNavigationView, TreeOverviewView

# special urls ()
urlpatterns = patterns('',
                       url(r'^_/get_navigation/(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', AJAXNodeNavigationView.as_view(), name="get-navigation"),
                       url(r'^_/apply_filter$', apply_filter, name="apply-filter"),
                       url(r'^_/update_filter$', update_filter, name="update-filter"),
                       url(r'^_/remove_filter$', remove_filter, name="remove-filter"),
                       url(r'^_/request_shot$', request_shot, name="mds-request-shot"),
                       url(r'^_/latest_shot/$', latest_shot, name="mds-latest-shot-for-default-tree"),
                       url(r'^_/latest_shot/(?P<tree_name>[^/]+)/$', latest_shot, name="mds-latest-shot"),
                       )

urlpatterns += patterns('',
                       url(r'^$', homepage, name="h1ds-mdsplus-homepage"),
                       url(r'^(?P<tree>[^/]+)/$', TreeOverviewView.as_view(), name="mds-tree-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', NodeView.as_view(), name="mds-root-node"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<tagname>[^/]+)/$', NodeView.as_view(), name="mds-tag"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<tagname>[^/]+)/(?P<nodepath>.*)/$', NodeView.as_view(), name="mds-node"),
                       )

