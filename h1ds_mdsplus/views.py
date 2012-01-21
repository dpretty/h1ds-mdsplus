import re, json, inspect, StringIO
import pylab
import xml.etree.ElementTree as etree

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.views.generic import View, RedirectView

from MDSplus import Tree
from MDSplus._treeshr import TreeException

from h1ds_mdsplus.utils import get_latest_shot, url_path_components_to_mds_path
from h1ds_mdsplus.wrappers import NodeWrapper
import h1ds_mdsplus.filters as df

DEFAULT_TAGNAME = "top"
DEFAULT_NODEPATH = ""


########################################################################
## Helper functions                                                   ##
########################################################################

# Match any URL path component comprising only digits.
# e.g. "foo/bar/12345/stuff" -> 12345
shot_regex = re.compile(r".*?\/(\d+?)\/.*?")

# Match strings "f(fid)_name", where fid is the filter ID
filter_name_regex = re.compile('^f(?P<fid>\d+?)_name')

# Match strings "f(fid)_arg(arg number)", where fid is the filter ID
filter_arg_regex = re.compile('^f(?P<fid>\d+?)_arg(?P<argn>\d+)')

# Match strings "f(fid)_kwarg_(arg name)", where fid is the filter ID
filter_kwarg_regex = re.compile('^f(?P<fid>\d+?)_kwarg_(?P<kwarg>.+)')

def get_filter_list(request):
    """Parse GET query sring and return sorted list of filter names.

    Arguments:
    request -- a HttpRequest instance with HTTP GET parameters.
    
    """
    filter_list = []

    if not request.method == 'GET':
        # If the HTTP method is not GET, return an empty list.
        return filter_list

    # First, create a dictionary with filter numbers as keys:
    # e.g. {1:{'name':filter, 'args':{1:arg1, 2:arg2, ...}, kwargs:{}}
    # note  that the  args  are stored  in  a dictionary  at this  point
    # because we cannot assume GET query will be ordered.
    filter_dict = {}
    for key, value in request.GET.iteritems():
        
        name_match = filter_name_regex.match(key)
        if name_match != None:
            fid = int(name_match.groups()[0])
            if not filter_dict.has_key(fid):
                filter_dict[fid] = {'name':"", 'args':{}, 'kwargs':{}}
            filter_dict[fid]['name'] = value
            continue

        arg_match = filter_arg_regex.match(key)
        if arg_match != None:
            fid = int(arg_match.groups()[0])
            argn = int(arg_match.groups()[1])
            if not filter_dict.has_key(fid):
                filter_dict[fid] = {'name':"", 'args':{}, 'kwargs':{}}
            filter_dict[fid]['args'][argn] = value
            continue

        kwarg_match = filter_kwarg_regex.match(key)
        if kwarg_match != None:
            fid = int(arg_match.groups()[0])
            kwarg = arg_match.groups()[1]
            if not filter_dict.has_key(fid):
                filter_dict[fid] = {'name':"", 'args':{}, 'kwargs':{}}
            filter_dict[fid]['kwargs'][kwarg] = value
            continue
    
    for fid, filter_data in sorted(filter_dict.items()):
        arg_list = [i[1] for i in sorted(filter_data['args'].items())]
        filter_list.append([fid, filter_data['name'], arg_list, filter_data['kwargs']])
                           
    return filter_list

def get_max_fid(request):
    # get maximum filter number
    filter_list = get_filter_list(request)
    if len(filter_list) == 0:
        max_filter_num = 0
    else:
        max_filter_num = max([i[0] for i in filter_list])
    return max_filter_num

def get_subtree(mds_node):

    try:
        desc = map(get_subtree, mds_node.getDescendants())
    except TypeError:
        desc = []

    tree = {
        "id":unicode(mds_node.nid),
        "name":unicode(mds_node.getNodeName()),
        "data":{"$dim":0.5*len(desc)+1, "$area":0.5*len(desc)+1, "$color":"#888"},
        "children":desc,
        }
    return tree

def get_nav_for_shot(tree, shot):
    mds_tree = Tree(tree, shot, 'READONLY')
    root_node = mds_tree.getNode(0)
    return get_subtree(root_node)
    
####def get_tree_exception_response()


########################################################################
## Django views                                                       ##
########################################################################



class NodeMixin(object):
    def get_node(self):
        tagname = self.kwargs.get('tagname', DEFAULT_TAGNAME)
        nodepath = self.kwargs.get('nodepath', DEFAULT_NODEPATH)
        try:
            mds_tree = Tree(self.kwargs['tree'], int(self.kwargs['shot']), 'READONLY')
        except TreeException:
            # If the  data cannot be  found, raise HTTP 404  error. HTTP
            # 404 is  appropriate, as  the requested resource  cannot be
            # found,  but may be  available in  the future  (i.e. future
            # shot number)
            raise Http404
        mds_path = url_path_components_to_mds_path(self.kwargs['tree'], tagname, nodepath)
        return NodeWrapper(mds_tree.getNode(mds_path))

    def get_filtered_node(self, request):
        mds_node = self.get_node()
        for fid, name, args, kwargs in get_filter_list(request):
            if u'' in args:
                messages.info(request, "Error: Filter '%s' is missing argument(s)" %(name))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            mds_node.data.apply_filter(fid, name, *args, **kwargs)
        return mds_node

class JSONNodeResponseMixin(NodeMixin):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        mds_node = self.get_filtered_node(request)
        data_dict = mds_node.get_view('json', dict_only=True)
        html_metadata = {
            'mds_tree':mds_node.mds_object.tree.name,
            'mds_shot':mds_node.mds_object.tree.shot,
            'mds_node_id':mds_node.mds_object.nid,
            }
        # add metadata...
        data_dict.update({'meta':html_metadata})
        return HttpResponse(json.dumps(data_dict), mimetype='application/json')

class XMLNodeResponseMixin(NodeMixin):
    """TODO: Generalise this for all datatypes"""

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        mds_node = self.get_filtered_node(request)
        # TODO: this should be handled by wrappers
        # however, at present mds_node.get_view
        # calls get_view on the data object which
        # doesn't ?? know about shot info, etc
        # the proper fix might be to have wrappers
        # take as args wrappers rather than data objects?
        
        data_xml = etree.Element('{http://h1svr.anu.edu.au/mdsplus}mdsdata',
                                 attrib={'{http://www.w3.org/XML/1998/namespace}lang': 'en'})

        # add shot info
        shot_number = etree.SubElement(data_xml, 'shot_number', attrib={})
        shot_number.text = str(mds_node.mds_object.tree.shot)
        shot_time = etree.SubElement(data_xml, 'shot_time', attrib={})
        shot_time.text = str(mds_node.mds_object.getTimeInserted().date)
        

        # add mds info
        mds_tree = etree.SubElement(data_xml, 'mds_tree', attrib={})
        mds_tree.text = mds_node.mds_object.tree.name
        mds_path = etree.SubElement(data_xml, 'mds_path', attrib={})
        mds_path.text = repr(mds_node.mds_object)

        signal = etree.SubElement(data_xml, 'data', attrib={'type':'signal'})

        ## make xlink ? to signal binary 
        ## for now, just text link
        #### should use proper url joining rather than string hacking...
        signal.text = request.build_absolute_uri()
        if '?' in signal.text:
            # it doesn't matter if we have multiple 'view' get queries - only the last one is used
            signal.text += '&view=bin' 
        else:
            signal.text += '?view=bin'

        return HttpResponse(etree.tostring(data_xml), mimetype='text/xml; charset=utf-8')

class PNGNodeResponseMixin(NodeMixin):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        mds_node = self.get_filtered_node(request)
        data = mds_node.get_view('png')
        img_buffer = StringIO.StringIO()
        pylab.imsave(img_buffer, data.data, format='png')
        return HttpResponse(img_buffer.getvalue(), mimetype='image/png')

class BinaryNodeResponseMixin(NodeMixin):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        mds_node = self.get_filtered_node(request)
        disc_data = mds_node.get_view('bin')
        response = HttpResponse(disc_data['iarr'].tostring(), mimetype='application/octet-stream')
        response['X-H1DS-signal-min'] = disc_data['minarr']
        response['X-H1DS-signal-delta'] = disc_data['deltar']
        response['X-H1DS-dim-t0'] = mds_node.data.dim[0]
        response['X-H1DS-dim-delta'] = mds_node.data.dim[1]-mds_node.data.dim[0]
        response['X-H1DS-dim-length'] = len(mds_node.data.dim)
        response['X-H1DS-signal-units'] = mds_node.data.units
        response['X-H1DS-signal-dtype'] = str(disc_data['iarr'].dtype)
        response['X-H1DS-dim-units'] = mds_node.data.dim_units
        return response

    
class HTMLNodeResponseMixin(NodeMixin):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        mds_node = self.get_filtered_node(request)
        html_metadata = {
            'mds_tree':mds_node.mds_object.tree.name,
            'mds_shot':mds_node.mds_object.tree.shot,
            'mds_node_id':mds_node.mds_object.nid,
            }

        return render_to_response('h1ds_mdsplus/node.html', 
                                  {'node_content':mds_node.get_view('html'),
                                   'html_metadata':html_metadata,
                                   'mdsnode':mds_node,
                                   'request_fullpath':request.get_full_path()},
                                  context_instance=RequestContext(request))

class MultiNodeResponseMixin(HTMLNodeResponseMixin, JSONNodeResponseMixin, PNGNodeResponseMixin, XMLNodeResponseMixin, BinaryNodeResponseMixin):
    """Dispatch to requested representation."""

    representations = {
        "html":HTMLNodeResponseMixin,
        "json":JSONNodeResponseMixin,
        "png":PNGNodeResponseMixin,
        "xml":XMLNodeResponseMixin,
        "bin":BinaryNodeResponseMixin,
        }

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method for requested representation; 
        # if a method doesn't exist, defer to the error handler. 
        # Also defer to the error handler if the request method isn't on the approved list.
        
        # TODO: for now, we only support GET and POST, as we are using the query string to 
        # determing which representation should be used, and the querydict is only available
        # for GET and POST. Need to bone up on whether query strings even make sense on other
        # HTTP verbs. Probably, we should use HTTP headers to figure out which content type should be
        # returned - also, we might be able to support both URI and header based content type selection.
        # http://stackoverflow.com/questions/381568/rest-content-type-should-it-be-based-on-extension-or-accept-header
        # http://www.xml.com/pub/a/2004/08/11/rest.html

        if request.method == 'GET':
            requested_representation = request.GET.get('view', 'html').lower()
        elif request.method == 'POST':
            requested_representation = request.GET.get('view', 'html')
        else:
            # until we figure out how to determine appropriate content type
            return self.http_method_not_allowed(request, *args, **kwargs)

        if not requested_representation in self.representations:
            # TODO: should handle this and let user know? rather than ignore?
            requested_representation = 'html'
            
        rep_class = self.representations[requested_representation]

        if request.method.lower() in rep_class.http_method_names:
            handler = getattr(rep_class, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        self.request = request
        self.args = args
        self.kwargs = kwargs
        return handler(self, request, *args, **kwargs)


class NodeView(MultiNodeResponseMixin, View):
    pass

class TreeOverviewView(RedirectView):   
    # TODO: currently HTML only.
    http_method_names = ['get']
    def get_redirect_url(self, **kwargs):
        return reverse('mds-root-node', kwargs={'tree':kwargs['tree'], 'shot':0})


class RequestShotView(RedirectView):
    """Redirect to shot, as requested by HTTP post."""

    http_method_names = ['post']

    def get_redirect_url(self, **kwargs):
        shot = self.request.POST['go_to_shot']
        input_path = self.request.POST['reqpath']
        input_shot = shot_regex.findall(input_path)[0]
        return input_path.replace(input_shot, shot)

class HomepageView(RedirectView):    

    def get_redirect_url(self, **kwargs):
        return reverse('mds-tree-overview', args=[settings.DEFAULT_MDS_TREE])

class FilterBaseView(RedirectView):
    """Read in filter info from HTTP query and apply H1DS filter syntax.

    The request GET query must contain a field named 'filter' which has the filter function name as its value.
    Separate fields for each of the filter arguments are also required, where the argument name is as it appears in the filter function code.

    If overwrite_fid is False, the new filter will have an FID +1 greater than the highest existing filter.
    If overwrite_fid is True, we expect a query field with an fid to overwrite.
    
    TODO: Do we really need path to be passed explicitly as a query field? or can we use session info? - largest FID is taken from the request, but we return url from path... can't be good.
    TODO: kwargs are not yet supported for filter functions.
    """
    
    http_method_name = ['get']

    def get_filter_url(self, overwrite_fid=False):
        # Get name of filter function
        qdict = self.request.GET.copy()
        filter_name = qdict.pop('filter')[-1]

        # Get the actual filter function
        filter_function = getattr(df, filter_name)

        # We'll append the filter to this path and redirect there.
        return_path = qdict.pop('path')[-1]

        if overwrite_fid:
            fid = int(qdict.pop('fid')[-1])
            for k,v in qdict.items():
                if k.startswith('f%d_' %fid):
                    qdict.pop(k)
        else:
            # Find the maximum fid in the existing query and +1
            fid = get_max_fid(self.request)+1

        # We expect the filter arguments to be passed as key&value in the HTTP query.
        filter_arg_names = inspect.getargspec(filter_function).args[1:]
        filter_arg_values = [qdict.pop(a)[-1] for a in filter_arg_names]

        # add new filter to query dict
        qdict.update({'f%d_name' %(fid):filter_name})
        for argn, arg_val in enumerate(filter_arg_values):
            qdict.update({'f%d_arg%d' %(fid,argn):arg_val})

        return '?'.join([return_path, qdict.urlencode()])

class ApplyFilterView(FilterBaseView):
    def get_redirect_url(self, **kwargs):
        return self.get_filter_url()

class UpdateFilterView(FilterBaseView):
    def get_redirect_url(self, **kwargs):
        return self.get_filter_url(overwrite_fid=True)

class RemoveFilterView(RedirectView):

    http_method_names = ['get']

    def get_redirect_url(self, **kwargs):
        qdict = self.request.GET.copy()
        filter_id = int(qdict.pop('fid')[-1])
        return_path = qdict.pop('path')[-1]
        new_filter_values = []
        for k,v in qdict.items():
            if k.startswith('f%d_' %filter_id):
                qdict.pop(k)
        return '?'.join([return_path, qdict.urlencode()])

########################################################################
#### AJAX Only Views                                                ####
########################################################################

class AJAXNodeNavigationView(View):
    """Return tree navigation data for shot"""
    
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        tree = kwargs['tree']
        shot = int(kwargs['shot'])
        cache_name = "nav_%s_%d" %(tree, shot)
        nav_data = cache.get(cache_name, 'no_cache')
        if nav_data == 'no_cache':
            nav_data = get_nav_for_shot(tree, shot)
            cache.set(cache_name, nav_data, 60 * 20)
        json_nav_data = json.dumps(nav_data)
        return HttpResponse(json_nav_data,
                            content_type='application/json')


class AJAXLatestShotView(View):
    """Return latest shot."""
    
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        latest_shot = get_latest_shot(tree_name)
        return HttpResponse('{"latest_shot":"%s"}' %latest_shot, 'application/javascript')


def request_url(request):
    """Return the URL for the requested MDS parameters."""

    shot = request.GET['shot']
    path = request.GET['mds-path']
    tree = request.GET['mds-tree']

    
    url_xml = etree.Element('{http://h1svr.anu.edu.au/mdsplus}mdsurlmap',
                             attrib={'{http://www.w3.org/XML/1998/namespace}lang': 'en'})
    
    # add mds info
    shot_number = etree.SubElement(url_xml, 'shot_number', attrib={})
    shot_number.text = shot
    mds_path = etree.SubElement(url_xml, 'mds_path', attrib={})
    mds_path.text = path
    mds_tree = etree.SubElement(url_xml, 'mds_tree', attrib={})
    mds_tree.text = tree

    
    url_pre_path = '/mdsplus/%s/%d/TOP/' %(tree, int(shot)) 
    url = url_pre_path + path.strip('.').strip(':').replace('.','/').replace(':','/')
    
    url_el = etree.SubElement(url_xml, 'mds_url', attrib={})
    url_el.text = url

    return HttpResponse(etree.tostring(url_xml), mimetype='text/xml; charset=utf-8')
