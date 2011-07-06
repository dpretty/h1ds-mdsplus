from django.core.urlresolvers import reverse
import MDSplus
import numpy as np

def resample(dwrapper, max_samples):
    max_samples = int(max_samples)
    signal_length = dwrapper.data.T.shape[0]
    delta_sample = signal_length/max_samples
        
    # put trailing [:max_samples] in case we get an extra one at the end
    dwrapper.data = dwrapper.data[::delta_sample][:max_samples]
    dwrapper.dim = dwrapper.dim[::delta_sample][:max_samples]

def resample_minmax(dwrapper, n_bins):
    """TODO: only works for 1D array..."""
    n_bins = int(n_bins)
    signal_length = dwrapper.data.T.shape[0]
    if signal_length >= 2*n_bins:
        delta_sample = signal_length/n_bins
        dwrapper.dim = dwrapper.dim[::delta_sample][:n_bins]
        max_data = []
        min_data = []

        for i in range(n_bins):
            tmp = dwrapper.data[i*delta_sample:(i+1)*delta_sample]
            max_data.append(max(tmp))
            min_data.append(min(tmp))

        dwrapper.label = ('min', 'max',)
        dwrapper.data = np.array([min_data, max_data])

def mean(dwrapper):
    """TODO: test for 2+ dimensional arrays"""
    dwrapper.data = np.mean(dwrapper.data)
    dwrapper.dim = None
    dwrapper.label = ('mean(%s)' %dwrapper.label[0],)

def dim_range(dwrapper, min_val, max_val):
    """Reduce range of signal."""
    min_val = float(min_val)
    max_val = float(max_val)
    min_e, max_e = np.searchsorted(dwrapper.dim, [min_val, max_val])
    dwrapper.data = dwrapper.data[min_e:max_e]
    dwrapper.dim = dwrapper.dim[min_e:max_e]
