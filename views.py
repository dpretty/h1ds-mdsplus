import os, MDSplus
from numpy import int32, int64, string_, shape

from MDSplus._treeshr import TreeException
from MDSplus._tdishr import TdiException

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from models import MDSPlusTree


def tree_list(request, format="html"):
    """List all MDSplus trees."""
    trees = MDSPlusTree.objects.all()
    return render_to_response('h1ds_mdsplus/tree_list.html', {'trees':trees}, context_instance=RequestContext(request))

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


def shot_overview(request, tree="", shot=-1, format="html", path=""):

    view = request.GET.get('view','')

    input_path = path
    input_tree = tree
    
    mdspath="\\%s::top" %(tree)
    if path:
        path = path.strip(':')
        mdspath = mdspath + '.' + path.replace('/','.')
    ## ugly hack - looks like sometimes the proper tree isn't returned??
    #try:
    t = MDSplus.Tree(tree, int(shot), 'READONLY')
    top_node = t.getNode(mdspath)

    
    url_mapper = tree_shot_mapper(tree, shot)

        
    child_nodes = top_node.getChildren()

    #if child_nodes.__class__ == None.__class__:
    #    children = None
    #else:
    try:
        children = map(url_mapper, child_nodes)
    except:
        children = None
    member_nodes = top_node.getMembers()

    #if member_nodes.__class__ == None.__class__:
    #    members = None
    #else:
    try:
        members = map(url_mapper, member_nodes)
    except:
        members = None
    
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


    return render_to_response('h1ds_mdsplus/shot_overview.html', 
                              {'children':children, 
                               'members':members, 
                               'data':data,
                               'datatype':datatype,
                               'input_tree':input_tree,
                               'tdi':tdi,
                               'input_path':input_path,
                               'shot':shot,
                               'breadcrumbs':get_breadcrumbs(top_node, input_tree, shot)}, 
                              context_instance=RequestContext(request))
    


def tree_overview(request, tree, format="html"):
    return HttpResponseRedirect(reverse('mds-shot-overview', kwargs={'tree':tree, 'shot':-1}))#, 'format':format}))

def request_shot(request):
    shot = request.POST['requested-shot']
    input_path = request.POST['input-path']
    input_tree = request.POST['input-tree']
    return HttpResponseRedirect('/'.join([input_tree, shot, input_path]))
