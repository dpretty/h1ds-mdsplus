import os
from numpy import int32, int64, string_, shape, array, int16, fft

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse

import MDSplus
from MDSplus._treeshr import TreeException
from MDSplus._tdishr import TdiException

from models import MDSPlusTree

#################################
#        Helper functions       #
# (don't return HTTP responses) #
#################################

def tree_shot_mapper(tree, shot):
    def map_url(data):
        pre_path = '/mdsplus/%s/%d/' %(tree, int(shot)) ## shouldn't hardcode this here...
        try:
            ## this causes segfault for children of http://h1svr/mdsplus/h1data/67896/OPERATIONS/ !!??!
            #dd = data.data()
            dd = 0
        except:
            dd = None
        ## hack..
        if not '::' in repr(data):
            url = pre_path +repr(data).strip('.').strip(':').replace('.','/').replace(':','/')
        else:
            url = pre_path
        return (data.getNodeName(), url, dd)
    return map_url

def get_breadcrumbs(node, tree, shot):
    breadcrumbs = []
    cont = True
    url_mapper = tree_shot_mapper(tree, shot)
    while cont:
        try:
            if node.__class__ != None.__class__:
                breadcrumbs.append(url_mapper(node))
            node = node.getParent()
        except:
            cont = False
    return breadcrumbs[::-1]

def get_subnodes(tree, shot, node):
    url_mapper = tree_shot_mapper(tree, shot)

    try:
        children = map(url_mapper, node.getChildren())
    except:
        children = None

    try:
        members = map(url_mapper, node.getMembers())
    except:
        members = None
        
    return members, children


###########################
#         Views           #
# (return HTTP responses) #
###########################

def tree_list(request, format="html"):
    """List all MDSplus trees stored in database."""
    trees = MDSPlusTree.objects.all()
    return render_to_response('h1ds_mdsplus/tree_list.html', 
                              {'trees':trees}, 
                              context_instance=RequestContext(request))

def node_raw(node):
    raw_data = node.raw_of().data().tostring()
    return HttpResponse(raw_data, mimetype='application/octet-stream')


def node(request, tree="", shot=-1, format="html", path=""):
    """Display MDS tree node (member or child)."""
    
    # Default to HTML if view type is not specified by user.
    view = request.GET.get('view','html')

    # Get top node
    mdspath="\\%s::top" %(tree)
    if path:
        mdspath = mdspath + '.' + path.strip(':').replace('/','.')

    t = MDSplus.Tree(tree, int(shot), 'READONLY')
    top_node = t.getNode(mdspath)

    # We don't need any further info for raw data
    if view == 'raw':
        return node_raw(top_node)

    # Get tree navigation info
    members, children = get_subnodes(tree, shot, top_node)
    
    # get tdi expression
    try:
        tdi = unicode(top_node.getData())
    except:
        tdi = u''

    datatype = 'unknown'    
    data = []
    data_exists = True
    try:
        data = top_node.data()
        data_shape = shape(data)
    except TdiException:
        data_exists = False
    fft_lit = []
    if data_exists:
        try:
            dim = top_node.dim_of().data()
            if len(data_shape)>1:
                tmp_data = []
                for ddi, dd in enumerate(data):
                    tmp_data.append([[dim[i], j] for i,j in enumerate(data[ddi])])
                data = tmp_data
                datatype = 'signal2d'
            else:
                # assume signal
                # do fft:
                #max_t = 
                
                n_samples = 1000
                n_jump = int(float(len(data))/n_samples)
                if n_jump > 2:
                    data = data[::n_jump]
                    dim = dim[::n_jump]
                data = [[dim[i], j] for i,j in enumerate(data)]
                datatype = 'signal'
        except TdiException:
            if type(data) in [int, float, int32, int64]:
                datatype = 'number'
            elif type(data) in [str, string_]:
                datatype = 'string'


    return render_to_response('h1ds_mdsplus/node.html', 
                              {'children':children, 
                               'members':members, 
                               'data':data,
                               'datatype':datatype,
                               'input_tree':tree,
                               'tdi':tdi,
                               'input_path':path,
                               'shot':shot,
                               'breadcrumbs':get_breadcrumbs(top_node, tree, shot)}, 
                              context_instance=RequestContext(request))
    


def tree_overview(request, tree, format="html"):
    return HttpResponseRedirect(reverse('mds-root-node', kwargs={'tree':tree, 'shot':-1}))#, 'format':format}))

def request_shot(request):
    """Redirect to shot, as requested by HTTP post."""
    shot = request.POST['requested-shot']
    input_path = request.POST['input-path']
    input_tree = request.POST['input-tree']
    return HttpResponseRedirect('/'.join([input_tree, shot, input_path]))
