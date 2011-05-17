from django.core.urlresolvers import reverse
#from django.http import QueryDict
import MDSplus
import numpy as np

#
# Note: you need to add each filter to the filter_mapping dict below
#

class BaseFilter(object):
    template = ""

    @classmethod
    def get_template(cls, request):
        submit_url = reverse("apply-filter")
        existing_query_string = ''.join(['<input type="hidden" name="%s" value="%s" />' %(k,v) for k,v in request.GET.items()])
        input_str = ''.join(['<input type="text" size=5 name="%s">' %i for i in cls.template_info['args']])
        
        template = '<div class="mds-filter"><form action="%(submit_url)s"><span class="left">%(text)s</span><span class="right">%(input_str)s<input type="submit" title="add" value="+"/></span><input type="hidden" name="filter" value="%(clsname)s"><input type="hidden" name="path" value="%(path)s">%(input_query)s</form></div>' %{'text':cls.template_info['text'], 'input_str':input_str, 'clsname':cls.__name__, 'submit_url':submit_url, 'path':request.path, 'input_query':existing_query_string}
        return template

    @classmethod
    def get_template_applied(cls, request, arg_str, fid):
        update_url = reverse("update-filter")
        remove_url = reverse("remove-filter")

        existing_query_string = ''.join(['<input type="hidden" name="%s" value="%s" />' %(k,v) for k,v in request.GET.items()])
        split_args = arg_str.split('_')
        input_str = ''.join(['<input type="text" size=5 name="%s" value="%s">' %(j,split_args[i]) for i,j in enumerate(cls.template_info['args'])])

        update_template = '<form action="%(update_url)s"><span class="left">%(text)s</span><span class="right">%(input_str)s<input type="hidden" name="fid" value="%(fid)s"><input title="update" type="submit" value="u"/></span><input type="hidden" name="filter" value="%(clsname)s"><input type="hidden" name="path" value="%(path)s">%(input_query)s</form>' %{'update_url':update_url, 'text':cls.template_info['text'], 'input_str':input_str, 'clsname':cls.__name__, 'path':request.path, 'input_query':existing_query_string, 'fid':fid}
        
        remove_template = '<span class="right"><form action="%(remove_url)s"><input type="hidden" name="path" value="%(path)s"><input type="hidden" name="fid" value="%(fid)s"><input title="remove" type="submit" value="-"/>%(existing_query)s</form></span>' %{'remove_url':remove_url, 'existing_query':existing_query_string, 'path':request.path, 'fid':fid}
        
        template = '<div class="mds-filter">'+remove_template+update_template+'</div>'

        return template
        

class MaxSamples(BaseFilter):
    """Resample signal.

    Example: To get the signal with 20 samples, use MaxSamples=20
    """

    template_info = {'text':"resample",
                     'args':['n_bins']}

    def __init__(self, data, arg_string):
        self.data = data
        self.max_samples = int(arg_string)
    def filter(self):
        numpy_array = self.data.data()
        numpy_arr_dimof = self.data.dim_of().data()
        delta_sample = len(numpy_array)/self.max_samples
        
        # put trailing [:max_samples] in case we get an extra one at the end
        new_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_array[::delta_sample][:self.max_samples], data.units))
        new_dim = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_arr_dimof[::delta_sample][:self.max_samples], data.dim_of().units))
        return MDSplus.Signal(new_array, None, new_dim)


class NBinsMinMax(BaseFilter):
    """Take a Signal and return a pair of signals (in MDSplus Dictionary) with min and max values with n bins.

    The returned MDSplus dictionary has the structure {'sigmin':(signal with min values), 'sigmax':(signal with max values)}
    
    Example: to resample a signal to 50 bins, use NBinsMinMax=50
    """

    template_info = {'text':"Min/max (nbins)",
                     'args':['n_bins']}

    def __init__(self, data, arg_string):
        self.data = data
        self.n_bins = int(arg_string)

    def filter(self):
        numpy_array = self.data.data()
        if len(numpy_array) < 2*self.n_bins:
            return self.data
        numpy_arr_dimof = self.data.dim_of().data()
        delta_sample = len(numpy_array)/self.n_bins

        new_dim = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_arr_dimof[::delta_sample][:self.n_bins], self.data.dim_of().units))

        max_data = []
        min_data = []

        for i in range(self.n_bins):
            tmp = numpy_array[i*delta_sample:(i+1)*delta_sample]
            max_data.append(max(tmp))
            min_data.append(min(tmp))

        max_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(np.array(max_data), self.data.units))
        min_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(np.array(min_data), self.data.units))

        return_dict = MDSplus.Dictionary({'sigmin':MDSplus.Signal(min_array, None, new_dim),
                                          'sigmax':MDSplus.Signal(max_array, None, new_dim)})
        return return_dict

class DimRange(BaseFilter):
    """Reduce range of signal.
    
    Example: to change the range of a signal to 1.23 < t < 1.51, use DimRange=1.23_1.52
    """
    template_info = {'text':"Range",
                     'args':['from', 'to']}


    def __init__(self, data, arg_string):
        self.data = data
        self.min_val, self.max_val = map(float, arg_string.split('_'))
        
    def filter(self):
        numpy_array = self.data.data()
        numpy_arr_dimof = self.data.dim_of().data()

        min_e, max_e = np.searchsorted(numpy_arr_dimof, [self.min_val, self.max_val])
        new_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_array[min_e:max_e], self.data.units))
        new_dim = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_arr_dimof[min_e:max_e], self.data.dim_of().units))
        return MDSplus.Signal(new_array, None, new_dim)


class MeanValue(BaseFilter):
    """Mean of signal.

    Example: MeanValue=1 (the query value can be anything).
    """
    template_info = {'text':"Mean value",
                     'args':[]}


    def __init__(self, data, arg_string):
        self.data = data

    def filter(self):
        mean_value = np.mean(self.data.data())
        return MDSplus.Float32(mean_value)

# Dictionary which keeps lower case class mappings

filter_mapping = {
    'maxsamples':MaxSamples,
    'nbinsminmax':NBinsMinMax,
    'dimrange':DimRange,
    'meanvalue':MeanValue,
    }
