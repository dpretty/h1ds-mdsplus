from django.conf.urls.defaults import *

from h1ds_mdsplus.views import NodeView, TreeOverviewView, RequestShotView, HomepageView
from h1ds_mdsplus.views import AJAXLatestShotView, AJAXNodeNavigationView
from h1ds_mdsplus.views import ApplyFilterView, UpdateFilterView, RemoveFilterView
from h1ds_mdsplus.views import UserSignalCreateView, UserSignalDeleteView
from h1ds_mdsplus.views import request_url

# special urls
urlpatterns = patterns('',
                       url(r'^_/get_navigation/(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', AJAXNodeNavigationView.as_view(), name="get-navigation"),
                       url(r'^_/apply_filter$', ApplyFilterView.as_view(), name="apply-filter"),
                       url(r'^_/update_filter$', UpdateFilterView.as_view(), name="update-filter"),
                       url(r'^_/remove_filter$', RemoveFilterView.as_view(), name="remove-filter"),
                       url(r'^_/request_shot$', RequestShotView.as_view(), name="mds-request-shot"),
                       url(r'^_/request_url$', request_url, name="mds-request-url"),
                       url(r'^_/add_user_signal$', UserSignalCreateView.as_view(), name="mds-add-user-signal"),
                       url(r'^_/delete_user_signal/(?P<pk>\d+)$', UserSignalDeleteView.as_view(), name="mds-delete-user-signal"),
                       url(r'^_/latest_shot/$', AJAXLatestShotView.as_view(), name="mds-latest-shot-for-default-tree"),
                       url(r'^_/latest_shot/(?P<tree_name>[^/]+)/$', AJAXLatestShotView.as_view(), name="mds-latest-shot"),
                       )

urlpatterns += patterns('',
                       url(r'^$', HomepageView.as_view(), name="h1ds-mdsplus-homepage"),
                       url(r'^(?P<tree>[^/]+)/$', TreeOverviewView.as_view(), name="mds-tree-overview"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/$', NodeView.as_view(), name="mds-root-node"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<tagname>[^/]+)/$', NodeView.as_view(), name="mds-tag"),
                       url(r'^(?P<tree>[^/]+)/(?P<shot>-?\d+)/(?P<tagname>[^/]+)/(?P<nodepath>.*)/$', NodeView.as_view(), name="mds-node"),
                       )

