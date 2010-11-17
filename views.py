import os
import xml.etree.ElementTree as etree
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


def node_signal(request, shot, view, node_info, data, mds_node):
    """Supported views: html, xml."""

    original_data_shape = shape(data)

    if view == 'html':    
        n_samples_str = request.GET.get('n_samples','1000')
    else:
        n_samples_str = request.GET.get('n_samples','all')
    
    if not n_samples_str.lower() == 'all':
        try:
            n_samples_int = int(n_samples_str)
        except:
            n_samples_str = 'all'

    dim = mds_node.dim_of().data()
    
    if len(original_data_shape)>1:
        #tmp_data = []
        if n_samples_str.lower() != 'all':
            n_jump = int(float(len(data))/n_samples_int)
            if n_jump > 1:
                dim = dim[::n_jump]
                data = [d[::n_jump] for d in data]
        #for ddi, dd in enumerate(data):
        #    tmp_data.append([[dim[i], j] for i,j in enumerate(dd)])
        #data = tmp_data
    else:
        if n_samples_str.lower() != 'all':
            n_jump = int(float(len(data))/n_samples_int)
            if n_jump > 1:
                data = data[::n_jump]
                dim = dim[::n_jump]
        data = [data]
        #data = [[[dim[i], j] for i,j in enumerate(data)],]


    if view.lower() == 'xml':
        # root element
        data_xml = etree.Element('{http://h1svr.anu.edu.au/mdsplus}data',
                                 attrib={'{http://www.w3.org/XML/1998/namespace}lang': 'en'})
        # add timebase element
        timebase = etree.SubElement(data_xml, 'timebase', attrib={})
        t_start = etree.SubElement(timebase, 't_start', attrib={})
        t_start.text = str(dim[0])
        delta_t = etree.SubElement(timebase, 'delta_t', attrib={})
        delta_t.text = str(dim[1]-dim[0])
        n_samples = etree.SubElement(timebase, 'n_samples', attrib={})
        n_samples.text = str(len(dim))

        # add shot element
        shot = etree.SubElement(data_xml, 'shot', attrib={})
        shot_number = etree.SubElement(shot, 'shot_number', attrib={})
        shot_number.text = '12345' #str(shot)
        shot_time = etree.SubElement(shot, 'shot_time', attrib={})
        shot_time.text = 'sometime'

        # add signal

        signal = etree.SubElement(data_xml, 'signal', attrib={})

        ## make xlink to signal binary 
        signal.text = 'xlink signal here'


        return HttpResponse(etree.tostring(data_xml), mimetype='text/xml; charset=utf-8')


    tmp_data = []
    for ddi, dd in enumerate(data):
        tmp_data.append([[dim[i], j] for i,j in enumerate(dd)])
    data = tmp_data

    displayed_data_shape = shape(array(data))[:-1] # last element of shape() is just the timebase we've added in for jflot
    
    template_name = 'h1ds_mdsplus/node_signal.html'
    node_info.update({'data':data, 
                      'original_shape':original_data_shape,
                      'displayed_shape':displayed_data_shape})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))

def node_scalar(request, shot, view, node_info, data, mds_node):
    template_name = 'h1ds_mdsplus/node_scalar.html'
    node_info.update({'data':data})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))

def node_text(request, shot, view, node_info, data, mds_node):
    template_name = 'h1ds_mdsplus/node_text.html'
    node_info.update({'data':data})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))



def node(request, tree="", shot=-1, format="html", path=""):
    """Display MDS tree node (member or child)."""
    
    # Default to HTML if view type is not specified by user.
    view = request.GET.get('view','html').lower()

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
        # TODO: alternative response for non-html views
        # If we can't get data for the node, return the 'no data' page.
        return render_to_response('h1ds_mdsplus/node_no_data.html', 
                                  node_info,
                                  context_instance=RequestContext(request))

    if node_dtype in signal_dtypes:
        return node_signal(request, shot, view, node_info, data, mds_node)
  
    elif node_dtype in scalar_dtypes:
        return node_scalar(request, shot, view, node_info, data, mds_node)
        
    elif node_dtype in text_dtypes:
        return node_text(request, shot, view, node_info, data, mds_node)

    else:
        # TODO: alternative response for non-HTML views
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
