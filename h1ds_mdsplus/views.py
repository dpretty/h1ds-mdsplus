import re, json

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from MDSplus import Tree
from MDSplus._treeshr import TreeException

from h1ds_mdsplus.models import MDSPlusTree
from h1ds_mdsplus.utils import get_latest_shot, url_path_components_to_mds_path
from h1ds_mdsplus.dtype_nodes import MDSPlusNodeWrapper
from h1ds_mdsplus.filters import filter_mapping

# Match any URL path component comprising only digits.
# e.g. "foo/bar/12345/stuff" -> 12345
shot_regex = re.compile(r".*?\/(\d+?)\/.*?")

# Match strings "f(fid)_(filtername)", where fid is the filter ID.
# e.g. "f5_mean" -> fid is 5, filtername is 'mean'
filter_regex=re.compile('^f(?P<fid>\d+?)_(?P<filtername>.+)')

def get_filter_list(request):
    """Parse GET query sring and return sorted list of filter names.

    Arguments:
    request -- a HttpRequest instance with HTTP GET parameters.
    
    """
    filter_list = []

    if not request.method == 'GET':
        # If the HTTP method is not GET, return an empty list.
        return filter_list

    for key, value in request.GET.iteritems():
        try:
            fid_str,fname = filter_regex.search(key).groups()
            filter_list.append([int(fid_str), fname, value])
        except AttributeError:
            # regex failed (not a filter f(int)_name key)
            pass

    filter_list.sort()
    return filter_list

def node(request, tree="", shot=0, tagname="top", nodepath=""):
    """Display MDS tree node.

    Arguments:
    request -- a HttpRequest instance

    Keyword arguments:
    tree -- name on an MDSPlusTree instance TODO: should this be a non-keyword argument (no default)?
    shot -- shot number (default 0)
    tagname -- MDSplus tag name (default 'top')
    nodepath -- MDSplus node path, with dot (.) and colon (:) replaced with URL path slashes (/) (default "")
    
    An instance of MDSPlusNodeWrapper  is created for the requested node
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
        mds_tree_model_instance = MDSPlusTree.objects.get(name=tree)
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
    mds_node = MDSPlusNodeWrapper(mds_tree.getNode(mds_path))
    mds_node.apply_filters(get_filter_list(request))

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
                              {'mdsnode':mds_node, 'html_metadata':html_metadata},
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
    default_tree = MDSPlusTree.objects.all()[0]
    return HttpResponseRedirect(reverse('mds-tree-overview', args=[default_tree.name]))

def apply_filter(request):
    # name of filter_class
    qdict = request.GET.copy()
    filter_name = qdict.pop('filter')[-1]
    filter_class = filter_mapping[filter_name.lower()]

    return_path = qdict.pop('path')[-1]
    new_filter_values = []
    for a in filter_class.template_info['args']:
        aname = qdict.pop(a)[-1]
        new_filter_values.append(aname)
    new_filter_str = '_'.join(new_filter_values)

    # get maximum filter number
    filter_list = get_filter_list(request)
    if len(filter_list) == 0:
        max_filter_num = 0
    else:
        max_filter_num = max([i[0] for i in filter_list])

    # add new filter to query dict
    new_filter_key = 'f%d_%s' %(max_filter_num+1, filter_class.__name__)
    qdict.update({new_filter_key:new_filter_str})
    return_url = '?'.join([return_path, qdict.urlencode()])
    return HttpResponseRedirect(return_url)
    

def update_filter(request):
    # name of filter_class
    qdict = request.GET.copy()
    filter_name = qdict.pop('filter')[-1]
    filter_class = filter_mapping[filter_name.lower()]

    return_path = qdict.pop('path')[-1]
    new_filter_values = []
    for a in filter_class.template_info['args']:
        aname = qdict.pop(a)[-1]
        new_filter_values.append(aname)
    new_filter_str = '_'.join(new_filter_values)

    filter_id = int(qdict.pop('fid')[-1])

    # add new filter to query dict
    filter_key = 'f%d_%s' %(filter_id, filter_class.__name__)

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
    
