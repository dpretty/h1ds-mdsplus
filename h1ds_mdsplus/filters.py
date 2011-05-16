import MDSplus
import numpy as np


class BaseFilter(object):
    template = ""

class MaxSamples(BaseFilter):
    """Resample signal.

    Example: To get the signal with 20 samples, use MaxSamples=20
    """
    
    template = "MaxSamples"

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

    template="NBinsMinMax"

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

    template = "DimRange"

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

    template = "MeanValue"

    def __init__(self, data, arg_string):
        self.data = data

    def filter(self):
        mean_value = mean(self.data.data())
        return MDSplus.Float32(mean_value)
