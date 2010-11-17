import os
from numpy import int32, int64, string_, shape, array, int16

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse

import MDSplus
from MDSplus._treeshr import TreeException
from MDSplus._tdishr import TdiException

from models import MDSPlusTree

####################################
# Abbreviated set of mds datatypes #
####################################

signal_dtypes = [195]
text_dtypes = [14]
scalar_dtypes = [8, # 32bit int 
                 ]

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

def get_breadcrumbs(mds_node, tree, shot):
    breadcrumbs = []
    cont = True
    url_mapper = tree_shot_mapper(tree, shot)
    while cont:
        try:
            if mds_node.__class__ != None.__class__:
                breadcrumbs.append(url_mapper(mds_node))
            mds_node = mds_node.getParent()
        except:
            cont = False
    return breadcrumbs[::-1]

def get_subnodes(tree, shot, mds_node):
    url_mapper = tree_shot_mapper(tree, shot)

    try:
        children = map(url_mapper, mds_node.getChildren())
    except:
        children = None

    try:
        members = map(url_mapper, mds_node.getMembers())
    except:
        members = None
        
    return members, children

def get_tdi(mds_node):
    try:
        tdi = unicode(mds_node.getData())
    except:
        tdi = u''
    return tdi


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

def node_raw(mds_node):
    raw_data = mds_node.raw_of().data().tostring()
    return HttpResponse(raw_data, mimetype='application/octet-stream')


def node_signal(request, node_info, data, mds_node):
        dim = mds_node.dim_of().data()
        if len(shape(data))>1:
            tmp_data = []
            for ddi, dd in enumerate(data):
                tmp_data.append([[dim[i], j] for i,j in enumerate(data[ddi])])
            data = tmp_data
            template_name = 'h1ds_mdsplus/node_signal2d.html'
        else:
            # assume signal
            n_samples = 1000
            n_jump = int(float(len(data))/n_samples)
            if n_jump > 2:
                data = data[::n_jump]
                dim = dim[::n_jump]
            data = [[dim[i], j] for i,j in enumerate(data)]
            template_name = 'h1ds_mdsplus/node_signal.html'
        node_info.update({'data':data})
        return render_to_response(template_name, 
                                  node_info,
                                  context_instance=RequestContext(request))

def node_scalar(request, node_info, data, mds_node):
    template_name = 'h1ds_mdsplus/node_scalar.html'
    node_info.update({'data':data})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))

def node_text(request, node_info, data, mds_node):
    template_name = 'h1ds_mdsplus/node_text.html'
    node_info.update({'data':data})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))



def node(request, tree="", shot=-1, format="html", path=""):
    """Display MDS tree node (member or child)."""
    
    # Default to HTML if view type is not specified by user.
    view = request.GET.get('view','html')

    # Get node
    mds_path="\\%s::top" %(tree)
    if path:
        mds_path = mds_path + '.' + path.strip(':').replace('/','.')
    t = MDSplus.Tree(tree, int(shot), 'READONLY')
    mds_node = t.getNode(mds_path)

    # We don't need any further info for raw data
    if view == 'raw':
        return node_raw(mds_node)

    # Get tree navigation info
    members, children = get_subnodes(tree, shot, mds_node)
    
    # Get tdi expression
    tdi = get_tdi(mds_node)

    # Get MDS data type for node
    node_dtype = mds_node.dtype
    
    # Metadata common to all (non-binary) view types.
    # Any variables required in base_node.html should be here.
    node_info = {'shot':shot,
                 'dtype':node_dtype,
                 'tdi':tdi, 
                 'children':children, 
                 'members':members, 
                 'input_tree':tree, 
                 'input_path':path,
                 'breadcrumbs':get_breadcrumbs(mds_node, tree, shot),
                 }
    
    # Get data if the node has any.
    try:
        data = mds_node.data()
    except TdiException:
        # If we can't get data for the node, return the 'no data' page.
        return render_to_response('h1ds_mdsplus/node_no_data.html', 
                                  node_info,
                                  context_instance=RequestContext(request))

    if node_dtype in signal_dtypes:
        return node_signal(request, node_info, data, mds_node)
  
    elif node_dtype in scalar_dtypes:
        return node_scalar(request, node_info, data, mds_node)
        
    elif node_dtype in text_dtypes:
        return node_text(request, node_info, data, mds_node)

    else:
        return render_to_response('h1ds_mdsplus/node_unconfigured.html', 
                                  node_info,
                                  context_instance=RequestContext(request))
    


def tree_overview(request, tree, format="html"):
    return HttpResponseRedirect(reverse('mds-root-node', kwargs={'tree':tree, 'shot':-1}))#, 'format':format}))

def request_shot(request):
    """Redirect to shot, as requested by HTTP post."""
    shot = request.POST['requested-shot']
    input_path = request.POST['input-path']
    input_tree = request.POST['input-tree']
    return HttpResponseRedirect('/'.join([input_tree, shot, input_path]))
