import MDSplus


def maxsamples(data, max_samples_str):
    # for data type MDSplus.Signal
    max_samples = int(max_samples_str)
    print max_samples
    numpy_array = data.data()
    try:
        numpy_arr_dimof = data.dim_of().data()
    except:
        numpy_arr_dimof = data.dim_of()

    delta_sample = len(numpy_array)/max_samples
    
    # put trailing [:max_samples] in case we get an extra one at the end
    new_array = numpy_array[::delta_sample][:max_samples]
    new_dim = numpy_arr_dimof[::delta_sample][:max_samples]
    return MDSplus.Signal(new_array, None, new_dim)
