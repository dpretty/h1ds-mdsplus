import re, json
from types import NoneType
import numpy

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

from MDSplus._tdishr import TdiException
from MDSplus._treeshr import TreeException
from MDSplus import _mdsdtypes
import MDSplus

from h1ds_mdsplus.models import MDSPlusTree
from h1ds_mdsplus.utils import discretise_array
#df -> dtype filters
import h1ds_mdsplus.filters as df
from h1ds_mdsplus import sql_type_mapping

try:
    NODE_BLACKLIST = settings.H1DS_MDSPLUS_NODE_BLACKLIST
except:
    NODE_BLACKLIST = []

class BlacklistType(type):
    def __str__(cls):
        return "%s"%cls.__name__

class Blacklist:
    __metaclass__ = BlacklistType


tagname_regex = re.compile('^\\\\(?P<tree>\w+?)::(?P<tagname>.+)')
mds_path_regex = re.compile('^\\\\(?P<tree>\w+?)::(?P<tagname>\w+?)[.|:](?P<nodepath>[\w.:]+)')

def mds_to_url(mds_data_object):
    # I haven't figured out how to do a single regex which would get the
    # correct  tagname when a node path exists,  and not fail when there
    # is no node path. So we do a simple check to see if there is a node
    # path
    #path_string = mds_data_object.__str__()
    path_string = unicode(mds_data_object.getFullPath())
    tag_node_string = path_string.split('::')[1]
    if ('.' in tag_node_string) or (':' in tag_node_string):
        # we have a node path.
        components = mds_path_regex.search(path_string)
        slashed_nodepath = components.group('nodepath').replace('.','/').replace(':','/')
        return reverse('mds-node', kwargs={'tree':components.group('tree'),
                                           'shot':mds_data_object.tree.shot,
                                           'tagname':components.group('tagname'),
                                           'nodepath':slashed_nodepath})
    else:
        components = tagname_regex.search(path_string)
        return reverse('mds-tag', kwargs={'tree':components.group('tree'), 
                                           'shot':mds_data_object.tree.shot,
                                           'tagname':components.group('tagname')})

def generic_data_view(data):
    return unicode(data.data)

def no_data_view_html(data):
    return "This node has no data."

def blacklist_view_html(data):
    return "This node has been blacklisted."

def blacklist_view_json(data, dict_only=False):
    data_dict =  {'summary_dtype':data.summary_dtype,
                 'data':"This node has been blacklisted"}
    if dict_only:
        return data_dict
    serial_data = json.dumps(data_dict)
    return HttpResponse(serial_data, mimetype='application/json')

def no_data_view_json(data, dict_only=False):
    data_dict =  {'summary_dtype':data.summary_dtype,
                 'data':None}
    if dict_only:
        return data_dict
    serial_data = json.dumps(data_dict)
    return HttpResponse(serial_data, mimetype='application/json')

def string_view_json(data, dict_only=False):
    data_dict =  {'summary_dtype':data.summary_dtype,
                 'data':str(data.data)}
    if dict_only:
        return data_dict
    serial_data = json.dumps(data_dict)
    return HttpResponse(serial_data, mimetype='application/json')


def float_view_serialized(data, mode='xml', dict_only=False):

    view_data = {'summary_dtype':data.summary_dtype,
                 'data':float(data.data),
                 }
    if dict_only == True:
        return view_data

    if mode == 'xml':
        pass
    elif mode == 'json':
        return json.dumps(view_data)
    else:
        raise Exception

def float_view_json(data, **kwargs):
    return float_view_serialized(data, mode='json', **kwargs)

def int_view_serialized(data, mode='xml', dict_only=False):

    view_data = {'summary_dtype':data.summary_dtype,
                 'data':int(data.data),
                 }
    if dict_only == True:
        return view_data

    if mode == 'xml':
        pass
    elif mode == 'json':
        return json.dumps(view_data)
    else:
        raise Exception

def int_view_json(data, **kwargs):
    return int_view_serialized(data, mode='json', **kwargs)


def signal_view_html(data):
    return """
    <div id="signal-placeholder" style="width:600px;height:300px;"></div>
    <div id="signal-overview" style="width:600px;height:100px"></div>
    """

def clean_signal_for_serialization(data):
    view_data = {}
    view_data['data_units'] = str(data.units)
    view_data['dim_units'] = str(data.dim_units)
    view_data['node_data'] = data.data.tolist()
    view_data['node_dim'] = data.dim.tolist()
    view_data['labels'] = data.label
    return view_data

def signal_view_serialized(data, mode='xml', dict_only=False):
    """Return the data in serialised form, i.e. XML, JSON, etc.
    
    Keyword arguments:
    dict_only -- don't actually serialise the data, just return the data
    which would be  serialised as a dictionary. This  is useful if other
    data (e.g. metadata) is to be added before serialisation).

    """
    view_data = clean_signal_for_serialization(data)
    if dict_only:
        return view_data

    if mode == 'xml':
        pass
    elif mode == 'json':
        return json.dumps(view_data)
    else:
        raise Exception

def dictionary_view_serialized(data, mode='xml', dict_only=False):
    view_data = {}
    for key, value in data.data.items():
        # TODO: what's the proper way of getting dtype from MDS object?
        # some seem to have obj.dtype, some have obj.getDtype, some have
        # obj.mdsdype. And the signal create from filter is obj._dtype...
        if value._dtype == _mdsdtypes.DTYPE_SIGNAL:
            view_data[key] = clean_signal_for_serialization(value)
        else:
            # TODO: support other dtypes in signal
            raise Error("Non signal datapoints not supported.")
    if dict_only:
        return view_data
    if mode == 'xml':
        pass
    elif mode == 'json':
        return json.dumps(view_data)
    else:
        raise Exception

def signal_view_json(data, **kwargs):
    return signal_view_serialized(data, mode='json', **kwargs)

def dictionary_view_json(data, **kwargs):
    return dictionary_view_serialized(data, mode='json', **kwargs)


def signal_view_bin(request, data):
    """Use Boyd's quantised compression to return binary data."""
    discretised_data = discretise_array(data.mds_object.data())
    dim = data.mds_object.dim_of().data()

    signal = discretised_data['iarr'].tostring()
    response = HttpResponse(signal, mimetype='application/octet-stream')
    response['X-H1DS-signal-min'] = discretised_data['minarr']
    response['X-H1DS-signal-delta'] = discretised_data['deltar']
    response['X-H1DS-dim-t0'] = dim[0]
    response['X-H1DS-dim-delta'] = dim[1]-dim[0]
    response['X-H1DS-dim-length'] = len(dim)
    response['X-H1DS-signal-units'] = data.mds_object.units
    response['X-H1DS-signal-dtype'] = str(discretised_data['iarr'].dtype)
    response['X-H1DS-dim-units'] = data.mds_object.dim_of().units
    return response


dtype_mappings = {
    NoneType:{'views':{'html':no_data_view_html, 'json':no_data_view_json}, 
              'filters':(),
              },
    numpy.string_:{'views':{'html':generic_data_view, 'json':string_view_json}, 
                   'filters':(), #TODO: length filter
                   },
    numpy.ndarray:{'views':{'html':signal_view_html, 'bin':signal_view_bin, 'json':signal_view_json},
                   'filters':(df.resample, df.resample_minmax, df.dim_range, df.mean, df.max_val, df.element, df.multiply, df.divide, df.peak_to_peak, df.prl_lpn),
                   },
    numpy.float32:{'views':{'html':generic_data_view, 'json':float_view_json},
                   'filters':(df.multiply, df.divide),
                   },
    numpy.float64:{'views':{'html':generic_data_view, 'json':float_view_json},
                   'filters':(df.multiply, df.divide),
                   },
    numpy.int32:{'views':{'html':generic_data_view, 'json':int_view_json},
                 'filters':(df.multiply, df.divide),
                 },
    numpy.int16:{'views':{'html':generic_data_view, 'json':int_view_json},
                 'filters':(df.multiply, df.divide),
                 },
    numpy.uint8:{'views':{'html':generic_data_view, 'json':int_view_json},
                 'filters':(df.multiply, df.divide),
                 },
    type(Blacklist()):{'views':{'html':blacklist_view_html, 'json':blacklist_view_json},
                       'filters':(),
                       }
    }


def get_tree_tagnames(mds_data_object, cache_timeout = 10):
    ## TODO: increase default timeout after debugging.
    tree_name = mds_data_object.tree.name
    shot = mds_data_object.tree.shot
    cache_name = 'tagnames_%s_%d' %(tree_name, shot)
    cached_data = cache.get(cache_name) 
    if cached_data != None:
        return cached_data
    else:
        # get data
        output_data = []
        # TODO: there appears to be some sort of binary? tag name \x01 in H1data tree.
        # this will probably break things - so will need to change regex and allow
        # for None returned by regex.search()
        tagnames = (tagname_regex.search(t).group('tagname') for t in mds_data_object.tree.findTags('*'))
        for tn in tagnames:
            url = reverse('mds-tag', kwargs={'tree':tree_name, 
                                             'shot':shot,
                                             'tagname':tn})
            output_data.append((tn,url))            
        # put in cache
        cache.set(cache_name, output_data, cache_timeout)
        # return data
        return output_data

def get_trees():
    cache_name = 'trees'
    cached_data = cache.get(cache_name) 
    if cached_data != None:
        return cached_data
    else:
        output_data = []
        for t in MDSPlusTree.objects.all():
            output_data.append((t.name, t.get_url()))
        cache.set(cache_name, output_data)
        return output_data

def unsupported_view(requested_view_type):
    def get_view(request, data):
        view_data = data.get_view_data(request)
        view_data['requested_view'] = requested_view_type
        return render_to_response('h1ds_mdsplus/unsupported_view.html', 
                                  #{'dtype':data.dtype, 'dtype_desc':dtype_desc},
                                  view_data,
                                  context_instance=RequestContext(request))
    return get_view

def member_or_child(mds_data):
    if mds_data.isChild():
        return 'Child'
    elif mds_data.isMember():
        return 'Member'
    else:
        return 'Unknown'

def map_url(data):
    #data_tree=data.__str__().strip('\\').split('::')[0]
    #pre_path = '/mdsplus/%s/%d/' %(data_tree, int(shot)) ## shouldn't hardcode this here...
    try:
        #  this causes segfault for children of http://h1svr/mdsplus/h1data/67896/OPERATIONS/ !!??!
        # dd = data.data()
        # dd = 0
        #  let's return node ID rather than data - use it for javascript navigation
        dd = data.getNid()
    except:
        dd = None
        
    url = mds_to_url(data)

    return (data.getNodeName(), url, dd, data.tree.name)

def get_mds_path_breadcrumbs(mds_data):
    cache_name = '%s_%d_%d' %(mds_data.tree.name, 
                              mds_data.tree.shot, mds_data.nid)
    cached_data = cache.get(cache_name) 
    if cached_data != None:
        return cached_data
    else:
        if mds_data.getDepth() == 1:
            tree_url = reverse("mds-tree-overview", kwargs={'tree':mds_data.tree.name})
            breadcrumb_string = '\\<a href="%(url)s">%(tree)s</a>::' %{'url':tree_url, 'tree':mds_data.tree.name}
        else:
            breadcrumb_string = get_mds_path_breadcrumbs(mds_data.getParent())
            if mds_data.isMember():
                breadcrumb_string+=":"
            else:
                breadcrumb_string+="."
        breadcrumb_string+='<a href="%(url)s">%(name)s</a>' %{'url':mds_to_url(mds_data), 'name':mds_data.getNodeName()}
        cache.set(cache_name, breadcrumb_string)
        return breadcrumb_string


def get_view_path(request, h1ds_view_name):
    qd_copy = request.GET.copy()
    qd_copy.update({'view': h1ds_view_name})
    return '?'.join([request.path, qd_copy.urlencode()])

########################################################################
## Data Wrapper                                                       ##
########################################################################

class DataWrapper(object):
    def __init__(self, mds_object):
        """Take an MDS object and provide a uniform interface to all data types."""        
        self.original_mds = {'path':mds_object.getFullPath(), 'shot':mds_object.tree.shot}
        if self.original_mds['path'] in NODE_BLACKLIST:
            self.data = Blacklist()
            self.units = None
            self.dim = None
            self.dim_units = None
        else:
            try:
                self.data = mds_object.data()
            except (TdiException, AttributeError):
                self.data = None
            try:
                self.units = mds_object.units
            except TdiException:
                self.units = None
            try:
                self.dim = mds_object.dim_of().data()
            except TdiException:
                self.dim = None
            try:
                self.dim_units = mds_object.dim_of().units
            except TdiException:
                self.dim_units = None

        self.filter_history = []
        self.available_filters = dtype_mappings[type(self.data)]['filters']
        self.available_views = dtype_mappings[type(self.data)]['views'].keys()
        self.summary_dtype = sql_type_mapping.get(type(self.data))
        print "... ", type(self.data), self.summary_dtype
        # TODO... labels need to have same dimension as data... and get from introspection where possible
        self.label = ('data',)
        
    def apply_filter(self, fid, name, value):
        filter_function = getattr(df, name)
        if value == "":
            filter_args = []
        else:
            filter_args = value.split('__')
        filter_function(self, *filter_args)
        self.filter_history.append((fid, filter_function, value))
        self.summary_dtype = sql_type_mapping.get(type(self.data))
        print "... ", type(self.data), self.summary_dtype
        self.available_filters = dtype_mappings[type(self.data)]['filters']
        self.available_views = dtype_mappings[type(self.data)]['views'].keys()

    def get_view(self, view_name):
        # TODO: is there a need for more detailed logic than the simple datatype key, value mapping?
        return dtype_mappings[type(self.data)]['views'].get(view_name, unsupported_view(view_name))
        

########################################################################
## Node Wrapper                                                       ##
########################################################################

class NodeWrapper(object):
    def __init__(self,mds_object):
        """A uniform interface to all MDS data objects.

        This wrapper holds additional information about the data object,
        such as  which filters  have been applied  to it, and  which are
        available...

        The MDS TDI is executed  during instantiation, so don't use this
        wrapper unless you're going to be using the data (e.g. don't use
        it to loop through trees etc).
        """
        # The original mds object
        self.mds_object = mds_object
            
        # A HTML string of the full MDS path with links to each path component.
        self.path_breadcrumbs = get_mds_path_breadcrumbs(self.mds_object)

        # shot number of the data
        self.shot = self.mds_object.tree.shot

        # the (numpy) data visible to the user
        self.data = DataWrapper(self.mds_object)

        self.members, self.children = self.get_subnode_data()

        self.tagnames = get_tree_tagnames(self.mds_object)
        self.treelinks = get_trees()

    def get_view(self, view_name, **kwargs):
        view_function = self.data.get_view(view_name)
        return view_function(self.data, **kwargs)

    def get_subnode_data(self):
        
        try:
            children = map(map_url, self.mds_object.getChildren())
        except TypeError:
            children = None
            
        try:
            members = map(map_url, self.mds_object.getMembers())
        except TypeError:
            members = None

        return members, children
