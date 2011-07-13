import re, json, inspect

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from MDSplus import Tree
from MDSplus._treeshr import TreeException

from h1ds_mdsplus.models import MDSPlusTree
from h1ds_mdsplus.utils import get_latest_shot, url_path_components_to_mds_path
from h1ds_mdsplus.wrappers import NodeWrapper
import h1ds_mdsplus.filters as df

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

########################################################################
## Django views                                                       ##
########################################################################

def node(request, tree="", shot=0, tagname="top", nodepath=""):
    """Display MDS tree node.

    Arguments:
    request -- a HttpRequest instance

    Keyword arguments:
    tree -- name on an MDSPlusTree instance TODO: should this be a non-keyword argument (no default)?
    shot -- shot number (default 0)
    tagname -- MDSplus tag name (default 'top')
    nodepath -- MDSplus node path, with dot (.) and colon (:) replaced with URL path slashes (/) (default "")
    
    An instance of NodeWrapper  is created for the requested node
    which handles filters and returns an appropriate HttpResponse.
    
    """

    if request.GET.has_key('go_to_shot'):
        new_get = request.GET.copy()
        new_shot = int(new_get.pop('go_to_shot')[-1])
        request.GET = new_get
        new_url = reverse('mds-node', kwargs={'tree':tree, 'shot':new_shot, 'tagname':tagname, 'nodepath':nodepath})
        new_url += '?%s' %(new_get.urlencode())
        return HttpResponseRedirect(new_url)
    # Default to HTML if view type is not specified by user.
    view = request.GET.get('view','html').lower()
    try:
        mds_tree_model_instance = MDSPlusTree.objects.get(name__iexact=tree)
    except ObjectDoesNotExist:
        # TODO: return relevant view type (here we return HTML even if request is json, xml, etc)
        return render_to_response('h1ds_mdsplus/cannot_find_tree.html', 
                                  {'shot':shot,
                                   'input_tree':tree},
                                  context_instance=RequestContext(request))        
    mds_tree = mds_tree_model_instance.get_tree(shot)
    if mds_tree == None:
        # TODO: return relevant view type (here we return HTML even if request is json, xml, etc)
        return render_to_response('h1ds_mdsplus/cannot_find_latest_shot.html', 
                                  {'shot':shot,
                                   'input_tree':tree},
                                  context_instance=RequestContext(request))
        
    mds_path = url_path_components_to_mds_path(tree, tagname, nodepath)
    mds_node = NodeWrapper(mds_tree.getNode(mds_path))
    for fid, name, args, kwargs in get_filter_list(request):
        mds_node.data.apply_filter(fid, name, *args, **kwargs)

    # get metadata for HTML (in HTML <head> (not HTTP header) to be parsed by javascript, or saved with HTML source etc)
    html_metadata = {
        'mds_path':mds_path,
        'shot':shot,
        }

    if view == 'json':
        data_dict = mds_node.get_view('json', dict_only=True)
        # add metadata...
        data_dict.update({'meta':html_metadata})
        return HttpResponse(json.dumps(data_dict), mimetype='application/json')
    
    return render_to_response('h1ds_mdsplus/node.html', 
                              {'mdsnode':mds_node, 'html_metadata':html_metadata,
                               'request_fullpath':request.get_full_path()},
                              context_instance=RequestContext(request))

    #return mds_node.get_view(request, view)


def tree_overview(request, tree):
    """Display tree at latest shot."""
    return HttpResponseRedirect(reverse('mds-root-node', kwargs={'tree':tree, 'shot':0}))

def request_shot(request):
    """Redirect to shot, as requested by HTTP post."""
    if not request.method == 'POST':
        return HttpResponseRedirect("/")        
    shot = request.POST['go_to_shot']
    input_path = request.POST['reqpath']
    input_shot = shot_regex.findall(input_path)[0]
    new_path = input_path.replace(input_shot, shot)
    return HttpResponseRedirect(new_path)

def latest_shot(request, tree_name=None):
    """Return latest shot (AJAX only for now...)."""
    if not request.is_ajax():
        return HttpResponseRedirect('/')

    latest_shot = get_latest_shot(tree_name)
        
    return HttpResponse('{"latest_shot":"%s"}' %latest_shot, 'application/javascript')
        

def homepage(request):
    """Show latest shot from default tree."""
    # Tree objects are ordered by the display_order field, so if we grab 
    # a single object it should be the one with the lowest display_order
    # value, which is what we use as the default tree.
    try:
        default_tree = MDSPlusTree.objects.all()[0]
    except IndexError:
        # This occurs if there are no MDSPlusTree instances
        return render_to_response('h1ds_mdsplus/no_trees_found.html', 
                                  context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('mds-tree-overview', args=[default_tree.name]))

def apply_filter(request):
    # Get name of filter function
    qdict = request.GET.copy()
    filter_name = qdict.pop('filter')[-1]

    # Get the actual filter function
    filter_function = getattr(df, filter_name)

    # We'll append the filter to this path and redirect there.
    return_path = qdict.pop('path')[-1]

    # Find the maximum fid in the existing query and +1
    new_fid = get_max_fid(request)+1
    
    # We expect the filter arguments to be passed as key&value in the HTTP query.
    filter_arg_names = inspect.getargspec(filter_function).args[1:]
    filter_arg_values = [qdict.pop(a)[-1] for a in filter_arg_names]

    # add new filter to query dict
    qdict.update({'f%d_name' %(new_fid):filter_name})
    for argn, arg_val in enumerate(filter_arg_values):
        qdict.update({'f%d_arg%d' %(new_fid,argn):arg_val})

    return_url = '?'.join([return_path, qdict.urlencode()])
    return HttpResponseRedirect(return_url)
    

def update_filter(request):
    # name of filter_class
    qdict = request.GET.copy()
    filter_name = qdict.pop('filter')[-1]
    filter_function = getattr(df, filter_name)

    return_path = qdict.pop('path')[-1]
    new_filter_values = []
    for a in inspect.getargspec(filter_function).args[1:]:
        aname = qdict.pop(a)[-1]
        new_filter_values.append(aname)
    new_filter_str = '__'.join(new_filter_values)

    filter_id = int(qdict.pop('fid')[-1])

    # add new filter to query dict
    filter_key = 'f%d_%s' %(filter_id, filter_name)

    qdict[filter_key] = new_filter_str
    return_url = '?'.join([return_path, qdict.urlencode()])
    return HttpResponseRedirect(return_url)

def remove_filter(request):
    qdict = request.GET.copy()
    filter_id = int(qdict.pop('fid')[-1])
    return_path = qdict.pop('path')[-1]
    new_filter_values = []
    for k,v in qdict.items():
        if k.startswith('f%d_' %filter_id):
            qdict.pop(k)
    return_url = '?'.join([return_path, qdict.urlencode()])
    return HttpResponseRedirect(return_url)
    
