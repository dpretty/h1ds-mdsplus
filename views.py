import os, MDSplus

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from models import MDSPlusTree


def tree_list(request, format="html"):
    """List all MDSplus trees."""
    trees = MDSPlusTree.objects.all()
    return render_to_response('h1ds_mdsplus/tree_list.html', {'trees':trees}, context_instance=RequestContext(request))


def shot_overview(request, tree="", shot=-1, format="html", path=""):
    import os, MDSplus
    MDSplus = reload(MDSplus)
    os = reload(os)
    for t in MDSPlusTree.objects.all():
        os.environ['%s_path' %t.name] = t.path

    qq = os.environ
    t = MDSplus.Tree(tree, int(shot), 'READONLY')
    mdspath="\\%s::top" %(tree)
    if path:
        path = path.strip(':')
        mdspath = mdspath + '.' + path.replace('/','.')
    top_node = t.getNode(mdspath)
    #node_children = top_node.getChildren()
    pre_path = '/mdsplus/%s/%d/' %(tree, int(shot)) ## shouldn't hardcode this here...
    try:
        child_nodes = [(i, pre_path +repr(i).strip('.').strip(':').replace('.','/')) for i in top_node.getChildren()]
    except:
        child_nodes = [(i, pre_path+repr(i).strip('.').strip(':').replace('.','/')) for i in top_node.getDescendants()]
    
    return render_to_response('h1ds_mdsplus/shot_overview.html', {'child_nodes':child_nodes}, context_instance=RequestContext(request))
    


def tree_overview(request, tree, format="html"):
    #return redirect(shot_overview, tree=tree, shot=-1)
    return HttpResponseRedirect(reverse('mds-shot-overview', kwargs={'tree':tree, 'shot':-1}))#, 'format':format}))
