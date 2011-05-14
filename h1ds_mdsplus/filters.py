import MDSplus
import numpy as np

def maxsamples(data, max_samples_str):
    # for data type MDSplus.Signal
    max_samples = int(max_samples_str)
    numpy_array = data.data()
    numpy_arr_dimof = data.dim_of().data()
    delta_sample = len(numpy_array)/max_samples
    
    # put trailing [:max_samples] in case we get an extra one at the end
    new_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_array[::delta_sample][:max_samples], data.units))
    new_dim = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_arr_dimof[::delta_sample][:max_samples], data.dim_of().units))
    return MDSplus.Signal(new_array, None, new_dim)

def nbins_minmax(data, n_bins_str):
    n_bins = int(n_bins_str)
    numpy_array = data.data()
    numpy_arr_dimof = data.dim_of().data()
    delta_sample = len(numpy_array)/n_bins
    
    new_dim = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(numpy_arr_dimof[::delta_sample][:n_bins], data.dim_of().units))
    
    max_data = []
    min_data = []

    for i in range(n_bins):
        tmp = numpy_array[i*delta_sample:(i+1)*delta_sample]
        max_data.append(max(tmp))
        min_data.append(min(tmp))
    
    max_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(np.array(max_data), data.units))
    min_array = MDSplus.Function(opcode="BUILD_WITH_UNITS", args=(np.array(min_data), data.units))
    
    return_dict = MDSplus.Dictionary({'sigmin':MDSplus.Signal(min_array, None, new_dim),
                                      'sigmax':MDSplus.Signal(max_array, None, new_dim)})
    return return_dict
