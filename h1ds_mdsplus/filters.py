import MDSplus


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
