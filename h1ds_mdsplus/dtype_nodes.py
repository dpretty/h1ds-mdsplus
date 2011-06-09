import re, json

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponse
#from django.utils import simplejson

from MDSplus._tdishr import TdiException
from MDSplus._treeshr import TreeException
from MDSplus import _mdsdtypes
import MDSplus

from h1ds_mdsplus.models import MDSPlusTree
from h1ds_mdsplus.utils import discretise_array
#df -> dtype filters
import h1ds_mdsplus.filters as df
from h1ds_mdsplus import mds_sql_mapping

tagname_regex = re.compile('^\\\\(?P<tree>\w+?)::(?P<tagname>.+)')
mds_path_regex = re.compile('^\\\\(?P<tree>\w+?)::(?P<tagname>\w+?)[.|:](?P<nodepath>[\w.:]+)')


def mds_to_url(mds_data_object):
    # I haven't figured out how to do a single regex which would get the
    # correct  tagname when a node path exists,  and not fail when there
    # is no node path. So we do a simple check to see if there is a node
    # path
    path_string = mds_data_object.__str__()
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

def no_data_view_html(request, data):
    return render_to_response('h1ds_mdsplus/no_data_view.html', 
                              data.get_view_data(request),
                              context_instance=RequestContext(request))

def no_data_view_json(request, data):
    serial_data = json.dumps({'mds_dtype':data.filtered_dtype,
                              'summary_dtype':mds_sql_mapping.get(data.filtered_dtype),
                              'data':None})
    return HttpResponse(serial_data, mimetype='application/json')
    

def int_view_html(request, data):
    # we don't care about whether a integer is unsigned, 8bit etc for 
    # HTML view, we we'll take all here.
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/int_view.html', 
                              view_data,
                              context_instance=RequestContext(request))

def float_view_html(request, data):
    # take all floats and assume python can convert all to string format
    # well enough for HTML.
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/float_view.html', 
                              view_data,
                              context_instance=RequestContext(request))


def float_view_serialized(request, data, mode='xml'):
    if mode == 'xml':
        pass
    elif mode == 'json':
        serial_data = json.dumps({'mds_dtype':data.filtered_dtype,
                                  'summary_dtype':mds_sql_mapping.get(data.filtered_dtype),
                                  'data':float(data.filtered_data)})
        return HttpResponse(serial_data, mimetype='application/json')
    else:
        raise Exception

def float_view_json(request, data):
    return float_view_serialized(request, data, mode='json')

def text_view_html(request, data):
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/text_view.html', 
                              view_data,
                              context_instance=RequestContext(request))

def nodeid_view_html(request, data):
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    view_data['node_data_url'] = mds_to_url(view_data['node_data'])
    return render_to_response('h1ds_mdsplus/nodeid_view.html', 
                              view_data,
                              context_instance=RequestContext(request))

def nodepath_view_html(request, data):
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    view_data['node_data_url'] = mds_to_url(view_data['node_data'])
    return render_to_response('h1ds_mdsplus/nodepath_view.html', 
                              view_data,
                              context_instance=RequestContext(request))

def range_view_html(request, data):
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/range_view.html', 
                              view_data,
                              context_instance=RequestContext(request))

def function_call_view_html(request, data):
    # TODO: show data returned by function (don't require filter, should
    # show returned data by default - along with function)
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/function_call_view.html', 
                              view_data,
                              context_instance=RequestContext(request))

def action_view_html(request, data):
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/action_view.html',
                              view_data,
                              context_instance=RequestContext(request))

def data_with_units_view_html(request, data):
    # TODO, desplay returned datatype (e.g. signal) beneath node_data.
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/data_with_units_view.html',
                              view_data,
                              context_instance=RequestContext(request))

def conglom_view_html(request, data):
    view_data = data.get_view_data(request)
    view_data['node_data'] = data.filtered_data
    return render_to_response('h1ds_mdsplus/conglom_view.html',
                              view_data,
                              context_instance=RequestContext(request))

def signal_view_html(request, data):
    view_data = data.get_view_data(request)
    # tell the HTML page what the datatype is, so it knows how to 
    # process binary data sent to javascript for plotting.
    try:
        view_data['signal_dtype'] = data.mds_object.raw_of().mdsdtype
    except AttributeError:
        view_data['signal_dtype'] = data.mds_object.getData().getValue().raw_of().mdsdtype

    return render_to_response('h1ds_mdsplus/signal_view.html',
                              view_data,
                              context_instance=RequestContext(request))

def clean_signal_for_serialization(request, data):
    #view_data = data.get_view_data(request)
    view_data = {}
    view_data['data_units'] = str(data.units)
    view_data['dim_units'] = str(data.dim_of().units)
    view_data['node_data'] = data.data().tolist()
    view_data['node_dim'] = data.dim_of().data().tolist()
    return view_data

def signal_view_serialized(request, data, mode='xml'):
    view_data = clean_signal_for_serialization(request, data.filtered_data)

    if mode == 'xml':
        pass
    elif mode == 'json':
        serial_data = json.dumps(view_data)
        return HttpResponse(serial_data, mimetype='application/json')
    else:
        raise Exception

def dictionary_view_serialized(request, data, mode='xml'):
    view_data = {}
    for key, value in data.filtered_data.items():
        # TODO: what's the proper way of getting dtype from MDS object?
        # some seem to have obj.dtype, some have obj.getDtype, some have
        # obj.mdsdype. And the signal create from filter is obj._dtype...
        if value._dtype == _mdsdtypes.DTYPE_SIGNAL:
            view_data[key] = clean_signal_for_serialization(request, value)
        else:
            # TODO: support other dtypes in signal
            raise Error("Non signal datapoints not supported.")
    if mode == 'xml':
        pass
    elif mode == 'json':
        serial_data = json.dumps(view_data)
        return HttpResponse(serial_data, mimetype='application/json')
    else:
        raise Exception

def signal_view_json(request, data):
    return signal_view_serialized(request, data, mode='json')

def dictionary_view_json(request, data):
    return dictionary_view_serialized(request, data, mode='json')


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


# Filters for all dtypes
filters_all = {
    # show TDI
    }
    
dtype_mappings = {
    "DTYPE_Z":{'id':0, 
               'views':{}, 
               'filters':(), 
               'description':"Unknown to Dave..."
               },
    "DTYPE_MISSING":{'id':0, 
                     'views':{'html':no_data_view_html, 'json':no_data_view_json}, 
                     'filters':(), 
                     'description':"Unknown to Dave..."
                     },
    "DTYPE_V":{'id':1, 
               'views':{}, 
               'filters':(), 
               'description':"Unknown to Dave..."
               },
    "DTYPE_BU":{'id':2, 
                'views':{'html':int_view_html}, 
                'filters':(), 
                'description':"Unsigned Byte (8-bit unsigned integer)"
                },
    "DTYPE_WU":{'id':3, 
                'views':{'html':int_view_html}, 
                'filters':(), 
                'description':"Unsigned Word (16-bit unsigned integer)"
                },
    "DTYPE_LU":{'id':4, 
                'views':{'html':int_view_html}, 
                'filters':(), 
                'description':"Unsigned Long (32-bit unsigned integer)"
                },
    "DTYPE_QU":{'id':5, 
                'views':{'html':int_view_html}, 
                'filters':(), 
                'description':"Unsigned Quadword (64-bit unsigned integer)"
                },
    "DTYPE_B":{'id':6, 
               'views':{'html':int_view_html}, 
               'filters':(), 
               'description':"Signed Byte (8-bit signed integer)"
               },
    "DTYPE_W":{'id':7, 
               'views':{'html':int_view_html}, 
               'filters':(), 
               'description':"Signed Word (16-bit signed integer)"
               },
    "DTYPE_L":{'id':8, 
               'views':{'html':int_view_html}, 
               'filters':(), 
               'description':"Signed Long (32-bit signed integer)"
               },
    "DTYPE_Q":{'id':9, 
               'views':{'html':int_view_html}, 
               'filters':(), 
               'description':"Signed Quadword (64-bit signed integer)"
               },
    "DTYPE_F":{'id':10, 
               'views':{'html':float_view_html}, 
               'filters':(), 
               'description':"Single Precision Real (VAX format)"
               },
    "DTYPE_D":{'id':11, 
               'views':{'html':float_view_html}, 
               'filters':(), 
               'description':"Double Precision Real (VAX format)"
               },
    "DTYPE_FC":{'id':12, 'views':{}, 'filters':(), 'description':"Single Precision Real Complex (VAX format)"},
    "DTYPE_DC":{'id':13, 'views':{}, 'filters':(), 'description':"Double Precision Real Complex (VAX format)"},
    "DTYPE_T":{'id':14, 
               'views':{'html':text_view_html}, 
               'filters':(), #TODO: length filter
               'description':"Text (8-bit characters)"
               },
    "DTYPE_NU":{'id':15, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NL":{'id':16, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NLO":{'id':17, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NR":{'id':18, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NRO":{'id':19, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NZ":{'id':20, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_P":{'id':21, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_ZI":{'id':22, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_ZEM":{'id':23, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DSC":{'id':24, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_OU":{'id':25, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_O":{'id':26, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_G":{'id':27, 'views':{}, 'filters':(), 'description':"Double Precision Real (VAX G_FLOAT format)"},
    "DTYPE_H":{'id':28, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_GC":{'id':29, 'views':{}, 'filters':(), 'description':"Double Precision Real Complex (VAX G_FLOAT format)"},
    "DTYPE_HC":{'id':30, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_CIT":{'id':31, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_BPV":{'id':32, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_BLV":{'id':33, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_VU":{'id':34, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_ADT":{'id':35, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_VT":{'id':37, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_FS":{'id':52, 
                'views':{'html':float_view_html}, 
                'filters':(), 
                'description':"Single Precision Real (IEEE format)"
                },
    "DTYPE_FT":{'id':53, 
                'views':{'html':float_view_html}, 
                'filters':(), 
                'description':"Double Precision Real (IEEE format)"
                },
    "DTYPE_FSC":{'id':54, 'views':{}, 'filters':(), 'description':"Single Precision Real Complex (IEEE frmat)"},
    "DTYPE_FTC":{'id':55, 'views':{}, 'filters':(), 'description':"Double Precision Real (IEEE format)"},
    "DTYPE_IDENT":{'id':191, 'views':{}, 'filters':(), 'description':"Variable Name"},
    "DTYPE_NID":{'id':192, 
                 'views':{'html':nodeid_view_html}, 
                 'filters':(), # TODO: follow link filter
                 'description':"Node (ID)"
                 },
    "DTYPE_PATH":{'id':193, 
                  'views':{'html':nodepath_view_html}, 
                  'filters':(), # TODO: follow link filter
                  'description':"Node (Path)"
                  },
    "DTYPE_PARAM":{'id':194, 'views':{}, 'filters':(), 'description':"Parameter"},
    "DTYPE_SIGNAL":{'id':195, 
                    'views':{'html':signal_view_html, 'bin':signal_view_bin, 'json':signal_view_json}, 
                    'filters':(df.Resample, df.ResampleMinMax, df.DimRange, df.MeanValue), 
                    'description':"Signal"
                    },
    "DTYPE_DIMENSION":{'id':196, 'views':{}, 'filters':(), 'description':"Dimension"},
    "DTYPE_WINDOW":{'id':197, 'views':{}, 'filters':(), 'description':"Window"},
    "DTYPE_SLOPE":{'id':198, 'views':{}, 'filters':(), 'description':"Slope (deprecated?)"},
    "DTYPE_FUNCTION":{'id':199, 
                      'views':{'html':function_call_view_html}, 
                      'filters':(), 
                      'description':"Built-in Function Call"
                      },
    "DTYPE_CONGLOM":{'id':200, 
                     'views':{'html':conglom_view_html}, 
                     'filters':(), 
                     'description':"Conglomerate/Device"
                     },
    "DTYPE_RANGE":{'id':201, 
                   'views':{'html':range_view_html}, 
                   'filters':(), 
                   'description':"Range"
                   },
    "DTYPE_ACTION":{'id':202, 
                    'views':{'html':action_view_html}, 
                    'filters':(), 
                    'description':"Action"
                    },
    "DTYPE_DISPATCH":{'id':203, 'views':{}, 'filters':(), 'description':"Dispatch"},
    "DTYPE_PROGRAM":{'id':204, 'views':{}, 'filters':(), 'description':"Program (deprecited?"},
    "DTYPE_ROUTINE":{'id':205, 'views':{}, 'filters':(), 'description':"Routine"},
    "DTYPE_PROCEDURE":{'id':206, 'views':{}, 'filters':(), 'description':"Procedure (deprecated?"},
    "DTYPE_METHOD":{'id':207, 'views':{}, 'filters':(), 'description':"Method"},
    "DTYPE_DEPENDENCY":{'id':208, 'views':{}, 'filters':(), 'description':"Dependency (deprecated?"},
    "DTYPE_CONDITION":{'id':209, 'views':{}, 'filters':(), 'description':"Condition (deprecated?"},
    "DTYPE_EVENT":{'id':210, 'views':{}, 'filters':(), 'description':"Event (deprecated?"},
    "DTYPE_WITH_UNITS":{'id':211, 
                        'views':{'html':data_with_units_view_html}, 
                        'filters':(), 
                        'description':"Data with units"
                        },
    "DTYPE_CALL":{'id':212, 'views':{}, 'filters':(), 'description':"External function call"},
    "DTYPE_WITH_ERROR":{'id':213, 'views':{}, 'filters':(), 'description':"Data with error"},
    "DTYPE_LIST":{'id':214, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_TUPLE":{'id':215, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DICTIONARY":{'id':216, 
                        'views':{'json':dictionary_view_json},
                        'filters':(), 
                        'description':"Unknown to Dave..."},
    "DTYPE_NATIVE_DOUBLE":{'id':53, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NATIVE_FLOAT":{'id':52, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DOUBLE_COMPLEX":{'id':54, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DOUBLE":{'id':53, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_FLOAT_COMPLEX":{'id':54, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_FLOAT":{'id':52,
                   'views':{'html':float_view_html, 'json':float_view_json}, 
                   'filters':(),
                   'description':"Unknown to Dave..."},
}


map_dtype_id = {}
for k,v in dtype_mappings.items():
    map_dtype_id[str(v['id'])] = k


def get_dtype(mds_data):
    if hasattr(mds_data, 'getDtype'):
        return mds_data.getDtype()
    elif hasattr(mds_data, 'mdsdtype'):
        return map_dtype_id[str(mds_data.mdsdtype)]
    elif hasattr(mds_data, 'dtype'):
        return mds_data.dtype
    elif hasattr(mds_data, '_dtype'):
        return map_dtype_id[str(mds_data._dtype)]
    elif type(mds_data) == MDSplus.Dictionary:
        return "DTYPE_DICTIONARY"


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
## H1DS Node class                                                    ##
########################################################################


class MDSPlusDataWrapper(object):
    def __init__(self,mds_object):
        self.mds_object = mds_object
        self.dtype = str(self.mds_object.getDtype())
        self.shot = self.mds_object.tree.shot
        self.filter_list = []
        self.filter_history = []
        try:
            self.filtered_data = self.mds_object.getData()
        except TreeException:
            self.filtered_data = None
        self.filtered_dtype = self.dtype
        self.n_filters = 0

            
    def get_view(self, request, view_name):
        print self.filtered_dtype
        view_function = dtype_mappings[self.filtered_dtype]['views'].get(view_name, unsupported_view(view_name))
        return view_function(request, self)

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

    def apply_filters(self, filter_list):
        self.filter_list = filter_list
        # Don't apply filters to nodes with missing data
        if self.dtype != 'DTYPE_MISSING':
            for fid, fname, fval in filter_list:
                filter_class = getattr(df, fname)
                self.filtered_data = filter_class(self.filtered_data, fval).filter()
                self.filter_history.append([fid, filter_class, fval])
                self.filtered_dtype = get_dtype(self.filtered_data)
                self.n_filters += 1
        
    def get_view_data(self, request):
        # TODO: clean up.
        view_links = [[i, get_view_path(request,i)] for i in dtype_mappings[self.dtype]['views'].keys()]
        filter_links = [{'name':i.__name__, 'doc':i.__doc__, 't':i.get_template(request)} for i in dtype_mappings[self.dtype]['filters']]
        f_view_links = [[i, get_view_path(request,i)] for i in dtype_mappings[self.filtered_dtype]['views'].keys()]
        f_filter_links = [{'name':i.__name__, 'doc':i.__doc__, 't':i.get_template(request)} for i in dtype_mappings[self.filtered_dtype]['filters']]

        applied_filter_links = [i.get_template_applied(request,j, fid) for fid,i,j in self.filter_history]

        members, children = self.get_subnode_data()
        node_metadata = {'datatype':self.dtype,
                         'node id':self.mds_object.nid,
                         'type':member_or_child(self.mds_object)}
        view_data = {'shot':self.shot,
                     'dtype':self.dtype,
                     'filtered_dtype':self.filtered_dtype,
                     #'tdi':tdi, 
                     'node_metadata':node_metadata,
                     'children':children, 
                     'members':members, 
                     'tagnames':get_tree_tagnames(self.mds_object),
                     'treelinks':get_trees(),
                     #'input_tree':tree, 
                     #'input_path':path,
                     #'input_query':request.GET.urlencode(),
                     'node_views':view_links,
                     'node_filters':filter_links,
                     'f_node_views':f_view_links,
                     'f_node_filters':f_filter_links,
                     'request_query':json.dumps(request.GET),
                     'request_fullpath':request.get_full_path(),
                     'absolute_uri':request.build_absolute_uri(),
                     'filter_list':applied_filter_links,
                     'summary_dtype':mds_sql_mapping.get(self.filtered_dtype),
                     'path_breadcrumbs':get_mds_path_breadcrumbs(self.mds_object),
                     #'debug_data':debug_data,
                     }
        return view_data
