import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse


dtype_mappings = {
    "DTYPE_Z":{'id':0, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_MISSING":{'id':0, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_V":{'id':1, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_BU":{'id':2, 'views':{}, 'filters':(), 'description':"Unsigned Byte (8-bit unsigned integer)"},
    "DTYPE_WU":{'id':3, 'views':{}, 'filters':(), 'description':"Unsigned Word (16-bit unsigned integer)"},
    "DTYPE_LU":{'id':4, 'views':{}, 'filters':(), 'description':"Unsigned Long (32-bit unsigned integer)"},
    "DTYPE_QU":{'id':5, 'views':{}, 'filters':(), 'description':"Unsigned Quadword (64-bit unsigned integer)"},
    "DTYPE_B":{'id':6, 'views':{}, 'filters':(), 'description':"Signed Byte (8-bit signed integer)"},
    "DTYPE_W":{'id':7, 'views':{}, 'filters':(), 'description':"Signed Word (16-bit signed integer)"},
    "DTYPE_L":{'id':8, 'views':{}, 'filters':(), 'description':"Signed Long (32-bit signed integer)"},
    "DTYPE_Q":{'id':9, 'views':{}, 'filters':(), 'description':"Signed Quadword (64-bit signed integer)"},
    "DTYPE_F":{'id':10, 'views':{}, 'filters':(), 'description':"Single Precision Real (VAX format)"},
    "DTYPE_D":{'id':11, 'views':{}, 'filters':(), 'description':"Double Precision Real (VAX format)"},
    "DTYPE_FC":{'id':12, 'views':{}, 'filters':(), 'description':"Single Precision Real Complex (VAX format)"},
    "DTYPE_DC":{'id':13, 'views':{}, 'filters':(), 'description':"Double Precision Real Complex (VAX format)"},
    "DTYPE_T":{'id':14, 'views':{}, 'filters':(), 'description':"Text (8-bit characters"},
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
    "DTYPE_FS":{'id':52, 'views':{}, 'filters':(), 'description':"Single Precision Real (IEEE format)"},
    "DTYPE_FT":{'id':53, 'views':{}, 'filters':(), 'description':"Double Precision Real (IEEE format)"},
    "DTYPE_FSC":{'id':54, 'views':{}, 'filters':(), 'description':"Single Precision Real Complex (IEEE frmat)"},
    "DTYPE_FTC":{'id':55, 'views':{}, 'filters':(), 'description':"Double Precision Real (IEEE format)"},
    "DTYPE_IDENT":{'id':191, 'views':{}, 'filters':(), 'description':"Variable Name"},
    "DTYPE_NID":{'id':192, 'views':{}, 'filters':(), 'description':"Node (ID)"},
    "DTYPE_PATH":{'id':193, 'views':{}, 'filters':(), 'description':"Node (Path)"},
    "DTYPE_PARAM":{'id':194, 'views':{}, 'filters':(), 'description':"Parameter"},
    "DTYPE_SIGNAL":{'id':195, 'views':{}, 'filters':(), 'description':"Signal"},
    "DTYPE_DIMENSION":{'id':196, 'views':{}, 'filters':(), 'description':"Dimension"},
    "DTYPE_WINDOW":{'id':197, 'views':{}, 'filters':(), 'description':"Window"},
    "DTYPE_SLOPE":{'id':198, 'views':{}, 'filters':(), 'description':"Slope (depreciated?)"},
    "DTYPE_FUNCTION":{'id':199, 'views':{}, 'filters':(), 'description':"Built-in Function Call"},
    "DTYPE_CONGLOM":{'id':200, 'views':{}, 'filters':(), 'description':"Conglomerate/Device"},
    "DTYPE_RANGE":{'id':201, 'views':{}, 'filters':(), 'description':"Range"},
    "DTYPE_ACTION":{'id':202, 'views':{}, 'filters':(), 'description':"Action"},
    "DTYPE_DISPATCH":{'id':203, 'views':{}, 'filters':(), 'description':"Dispatch"},
    "DTYPE_PROGRAM":{'id':204, 'views':{}, 'filters':(), 'description':"Program (deprecited?"},
    "DTYPE_ROUTINE":{'id':205, 'views':{}, 'filters':(), 'description':"Routine"},
    "DTYPE_PROCEDURE":{'id':206, 'views':{}, 'filters':(), 'description':"Procedure (depreciated?"},
    "DTYPE_METHOD":{'id':207, 'views':{}, 'filters':(), 'description':"Method"},
    "DTYPE_DEPENDENCY":{'id':208, 'views':{}, 'filters':(), 'description':"Dependency (depreciated?"},
    "DTYPE_CONDITION":{'id':209, 'views':{}, 'filters':(), 'description':"Condition (depreciated?"},
    "DTYPE_EVENT":{'id':210, 'views':{}, 'filters':(), 'description':"Event (depreciated?"},
    "DTYPE_WITH_UNITS":{'id':211, 'views':{}, 'filters':(), 'description':"Data with units"},
    "DTYPE_CALL":{'id':212, 'views':{}, 'filters':(), 'description':"External function call"},
    "DTYPE_WITH_ERROR":{'id':213, 'views':{}, 'filters':(), 'description':"Data with error"},
    "DTYPE_LIST":{'id':214, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_TUPLE":{'id':215, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DICTIONARY":{'id':216, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NATIVE_DOUBLE":{'id':53, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_NATIVE_FLOAT":{'id':52, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DOUBLE_COMPLEX":{'id':54, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_DOUBLE":{'id':53, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_FLOAT_COMPLEX":{'id':54, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
    "DTYPE_FLOAT":{'id':52, 'views':{}, 'filters':(), 'description':"Unknown to Dave..."},
}


def unsupported_view(request, data):
    dtype_desc = dtype_mappings[data.dtype]['description']
    return render_to_response('h1ds_mdsplus/unsupported_view.html', 
                              #{'dtype':data.dtype, 'dtype_desc':dtype_desc},
                              data.get_view_data(),
                              context_instance=RequestContext(request))

mds_path_regex = re.compile('^\\\\(?P<tree>\w+?)::(?P<tagname>\w+?)[\.|:](?P<nodepath>[\w\.:]+)')

def mds_to_url(mds_data_object):
    components = mds_path_regex.search(mds_data_object.__str__())
    slashed_nodepath = components.group('nodepath').replace('.','/').replace(':','/')
    return reverse('mds-node', kwargs={'tree':components.group('tree'), 
                                       'shot':mds_data_object.tree.shot,
                                       'tagname':components.group('tagname'),
                                       'nodepath':slashed_nodepath})


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

    return (data.getNodeName(), url, dd)#, data_tree)





########################################################################
## H1DS Node class                                                    ##
########################################################################


class MDSPlusDataWrapper(object):
    def __init__(self,mds_object):
        self.mds_object = mds_object
        self.dtype = str(self.mds_object.getDtype())

    def get_view(self, request, view_name):
        view_function = dtype_mappings[self.dtype]['views'].get(view_name, unsupported_view)
        return view_function(request, self)

    def get_subnode_data(self):
        #url_mapper = tree_shot_mapper(self.mds_object.tree.name, self.mds_object.tree.shot)
        
        #try:
        children = map(map_url, self.mds_object.getChildren())
        #except:
        #    children = None
            
        try:
            members = map(map_url, self.mds_object.getMembers())
        except:
            members = None

        # TODO: get tagnames too
        
        return members, children

    def get_view_data(self):
        members, children = self.get_subnode_data()
        view_data = {'shot':self.mds_object.tree.shot,
                     'dtype':self.dtype,
                     #'tdi':tdi, 
                     'children':children, 
                     'members':members, 
                     #'input_tree':tree, 
                     #'input_path':path,
                     #'input_query':request.GET.urlencode(),
                     #'breadcrumbs':get_breadcrumbs(mds_node, tree, shot),
                     #'debug_data':debug_data,
                     }
        return view_data
