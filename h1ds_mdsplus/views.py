import os
import xml.etree.ElementTree as etree
from numpy import int32, int64, string_, shape, array, int16
from xml.dom import minidom

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.csrf.middleware import csrf_exempt
import django.dispatch
from django.core import serializers

import MDSplus
from MDSplus._treeshr import TreeException
from MDSplus._tdishr import TdiException

from models import MDSPlusTree
from utils import discretise_array
from datetime import datetime

mdsevent_signal = django.dispatch.Signal(providing_args=["name", "time", "data"])


####################################
# Abbreviated set of mds datatypes #
####################################

signal_dtypes = [195, # signal
                 211, # 'data with units' - seems to be used for link to signal??
                 ]
text_dtypes = [14]
scalar_dtypes = [8, # 32bit int 
                 52, # single precision real
                 ]

# if node, then we get the dtype of the node
node_dtypes = [192,
               ]

# these give segfaults through mdsobjects - need to investigate
disabled_nodes = [50331887, # John's spectrscopy.survey:spectrum - gives segfault
                  14, # .ech:i_beam (function call)
                  8, # log.heating:pulse_width
                  449, # .operations:i_sec
                  50332106, # .SPECTROSCOPY.SURVEY:SPECT_NOBSLN
                  ]

#################################
#        Helper functions       #
# (don't return HTTP responses) #
#################################

def tree_shot_mapper(tree, shot):
    def map_url(data):
        data_tree=data.__str__().strip('\\').split('::')[0]
        pre_path = '/mdsplus/%s/%d/' %(data_tree, int(shot)) ## shouldn't hardcode this here...
        try:
            ## this causes segfault for children of http://h1svr/mdsplus/h1data/67896/OPERATIONS/ !!??!
            #dd = data.data()
            #dd = 0
            ## let's return node ID rather than data - use it for javascript navigation
            dd = data.getNid()
        except:
            dd = None
        
        #url = pre_path + data.__str__()[len(tree)+3:].strip('.').strip(':').replace('.','/').replace(':','/')
        url = pre_path + data.__str__().split('::')[1].strip('.').strip(':').replace('.','/').replace(':','/')

        return (data.getNodeName(), url, dd, data_tree)
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


simple_xml_value = lambda doc, tag: doc.getElementsByTagName(tag)[0].firstChild.nodeValue

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
    """Return raw mds binary."""
    raw_data = mds_node.raw_of().data().tostring()
    return HttpResponse(raw_data, mimetype='application/octet-stream')

def node_signal_bin(mds_node, data):
    """Use Boyd's quantised compression to return binary data."""
    discretised_data = discretise_array(data)
    dim = mds_node.dim_of().data()

    signal = discretised_data['iarr'].tostring()
    response = HttpResponse(signal, mimetype='application/octet-stream')
    response['X-H1DS-signal-min'] = discretised_data['minarr']
    response['X-H1DS-signal-delta'] = discretised_data['deltar']
    response['X-H1DS-dim-t0'] = dim[0]
    response['X-H1DS-dim-delta'] = dim[1]-dim[0]
    response['X-H1DS-dim-length'] = len(dim)
    response['X-H1DS-signal-units'] = mds_node.units
    response['X-H1DS-dim-units'] = mds_node.dim_of().units

    return response

def node_signal_csv(mds_node, data, node_info):

    dim = mds_node.dim_of().data()

    output = ["# shot: %s, tree: %s, path: %s" %(str(node_info['shot']), str(node_info['input_tree']), str(node_info['input_path']))]
    output.append("# time, signal")
    for di,d in enumerate(data):
        output.append("%e, %e" %(dim[di], d))

    output = '\n'.join(output)

    response = HttpResponse(output, mimetype='text/csv')

    return response



def generic_xml(shot, mds_node, node_info):
    data_xml = etree.Element('{http://h1svr.anu.edu.au/mdsplus}mdsdata',
                             attrib={'{http://www.w3.org/XML/1998/namespace}lang': 'en'})
    
    # add shot info
    shot_number = etree.SubElement(data_xml, 'shot_number', attrib={})
    shot_number.text = shot
    shot_time = etree.SubElement(data_xml, 'shot_time', attrib={})
    shot_time.text = str(mds_node.getTimeInserted().date)
    

    # add mds info
    mds_tree = etree.SubElement(data_xml, 'mds_tree', attrib={})
    mds_tree.text = node_info['input_tree']
    mds_path = etree.SubElement(data_xml, 'mds_path', attrib={})
    mds_path.text = repr(mds_node)

    return data_xml

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
        data_xml = generic_xml(shot, mds_node, node_info)

        # add signal
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

    if view.lower() == 'xml':
        # root element
        data_xml = generic_xml(shot, mds_node, node_info)

        # add signal
        signal = etree.SubElement(data_xml, 'data', attrib={'type':'scalar'})
        signal.text = str(data)
        return HttpResponse(etree.tostring(data_xml), mimetype='text/xml; charset=utf-8')

    template_name = 'h1ds_mdsplus/node_scalar.html'
    node_info.update({'data':data})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))

def node_text(request, shot, view, node_info, data, mds_node):
    if view.lower() == 'xml':
        # root element
        data_xml = generic_xml(shot, mds_node, node_info)

        # add signal
        signal = etree.SubElement(data_xml, 'data', attrib={'type':'text'})
        signal.text = data
        return HttpResponse(etree.tostring(data_xml), mimetype='text/xml; charset=utf-8')

    template_name = 'h1ds_mdsplus/node_text.html'
    node_info.update({'data':data})
    return render_to_response(template_name, 
                              node_info,
                              context_instance=RequestContext(request))



def node(request, tree="", shot=0, format="html", path="top"):
    """Display MDS tree node (member or child)."""
    
    # Default to HTML if view type is not specified by user.
    view = request.GET.get('view','html').lower()

    # Get node
    #mds_path="\\%s::top" %(tree)
    #if path:
    #    #mds_path = mds_path + '.' + path.strip(':').replace('/','.')
    mds_path = '\\' + tree + '::' + path.strip(':').replace('/','.')
    if int(shot) == 0:
        try:
            t = MDSplus.Tree(tree, int(shot), 'READONLY')
        except TreeException:
            return render_to_response('h1ds_mdsplus/cannot_find_latest_shot.html', 
                                      {'shot':shot,
                                       'input_tree':tree,
                                       'input_path':path},
                                      context_instance=RequestContext(request))
    else:
        t = MDSplus.Tree(tree, int(shot), 'READONLY')
            
    mds_node = t.getNode(mds_path)
    # We don't need any further info for raw data
    if view == 'raw':
        return node_raw(mds_node)

    # Get tree navigation info
    members, children = get_subnodes(tree, shot, mds_node)

    debug_data = mds_node.getNid()
    # Get tdi expression
    tdi = get_tdi(mds_node)

    # Get MDS data type for node
    node_dtype = mds_node.dtype
    
    if node_dtype in node_dtypes:
        node_dtype = mds_node.getData().dtype

    # Metadata common to all (non-binary) view types.
    # Any variables required in base_node.html should be here.
    node_info = {'shot':shot,
                 'dtype':node_dtype,
                 'tdi':tdi, 
                 'children':children, 
                 'members':members, 
                 'input_tree':tree, 
                 'input_path':path,
                 'input_query':request.GET.urlencode(),
                 'breadcrumbs':get_breadcrumbs(mds_node, tree, shot),
                 'debug_data':debug_data,
                 }
    
    if mds_node.getNid() in disabled_nodes:
        return render_to_response('h1ds_mdsplus/node_disabled.html', 
                                  node_info,
                                  context_instance=RequestContext(request))


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
        if view == 'bin':
            return node_signal_bin(mds_node, data)
        elif view == 'csv':
            return node_signal_csv(mds_node, data, node_info)
        else:
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
    """Display tree at latest shot."""
    return HttpResponseRedirect(reverse('mds-root-node', kwargs={'tree':tree, 'shot':0}))#, 'format':format}))

def request_shot(request):
    """Redirect to shot, as requested by HTTP post."""
    shot = request.POST['requested-shot']
    input_path = request.POST['input-path']
    input_tree = request.POST['input-tree']
    input_query = request.POST['input-query']
    return_url = '/'.join([input_tree, shot, input_path])
    if input_query == '':
        return HttpResponseRedirect(return_url)
    else:        
        return HttpResponseRedirect(return_url+'?'+input_query)

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

    
    url_pre_path = '/mdsplus/%s/%d/' %(tree, int(shot)) 
    url = url_pre_path + path.strip('.').strip(':').replace('.','/').replace(':','/')
    
    url_el = etree.SubElement(url_xml, 'mds_url', attrib={})
    url_el.text = url

    return HttpResponse(etree.tostring(url_xml), mimetype='text/xml; charset=utf-8')


def latest_shot(request, tree_name):
    """Return latest shot (AJAX only)."""
    try:
        t = MDSplus.Tree(tree_name, 0, 'READONLY')
        latest_shot = t.shot
    except:
        latest_shot=-1
    if request.is_ajax():
        return HttpResponse('{"latest_shot":"%s"}' %latest_shot, 'application/javascript')
    else:
        return HttpResponseRedirect('/')
        

def mds_navigation_subtree(request, tree_name, shot, node_id):
    """Return MDSPlus subtree, used fro AJAX building of tree navigation."""
    if request.is_ajax():
        shot = int(shot)
        tsm = tree_shot_mapper(tree_name, shot)
        t = MDSplus.Tree(tree_name, shot, 'READONLY')
        node = MDSplus.TreeNode(int(node_id), t)
        descendants = node.getDescendants()
        try:
            desc_data = [[tsm(i),str(i.getNid())] for i in descendants]
            js_desc_data = ['{"url":"%s", "nid":"%s", "name":"%s", "tree":"%s"}' %(j[0][1], j[1], j[0][0], j[0][3]) for j in desc_data]
            output_js = '{"nodes":[%s]}' %(','.join(js_desc_data))
        except TypeError:
            output_js = '{"nodes":[]}'
        return HttpResponse(output_js, 'application/javascript')

    else:
        return HttpResponseRedirect('/')
    
