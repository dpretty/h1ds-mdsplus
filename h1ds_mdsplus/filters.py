from urlparse import urlparse, urlunparse
import urllib2, json
from django.core.urlresolvers import reverse
import MDSplus
import numpy as np

########################################################################
## signal -> scalar                                                   ##
########################################################################

def max_val(dwrapper):
    """TODO: test for 2+ dimensional arrays"""
    dwrapper.data = np.max(dwrapper.data)
    dwrapper.dim = None
    dwrapper.label = ('max(%s)' %dwrapper.label[0],)
    
def mean(dwrapper):
    """TODO: test for 2+ dimensional arrays"""
    dwrapper.data = np.mean(dwrapper.data)
    dwrapper.dim = None
    dwrapper.label = ('mean(%s)' %dwrapper.label[0],)

def element(dwrapper, index):
    """Get an element of an array.

    The first element has index 0.
    """
    dwrapper.data = dwrapper.data[int(index)]
    dwrapper.dim = None
    dwrapper.label = ('%s[%s]' %(dwrapper.label[0], index),)

def peak_to_peak(dwrapper):
    """Max(signal) - min(signal)."""
    dwrapper.data = max(dwrapper.data) - min(dwrapper.data)
    dwrapper.dim = None
    dwrapper.label = ('max(%(lab)s)-min(%(lab)s)' %{'lab':dwrapper.label[0]},)

########################################################################
## signal -> signal                                                   ##
########################################################################

def prl_lpn(dwrapper, f0, order):
    """prl_lpn
    
    TODO: only working for order = 1
    """
    order = int(order)
    N = int(0.5 + 0.5/(dwrapper.dim[1]-dwrapper.dim[0])/float(f0))
    a = np.cumsum(dwrapper.data)
    if order > 1:
        # if (_order > 1 ) return(prl_lpn(prl_lpn( _signal, _f0, _order-1),_f0, 1));
        pass
    else:
        dwrapper.data = (a[N:]-a[:-N])/float(N)
        dwrapper.label = ('prl_lpn(%s)' %dwrapper.label[0],)

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

def dim_range(dwrapper, min_val, max_val):
    """Reduce range of signal."""
    min_val = float(min_val)
    max_val = float(max_val)
    min_e, max_e = np.searchsorted(dwrapper.dim, [min_val, max_val])
    dwrapper.data = dwrapper.data[min_e:max_e]
    dwrapper.dim = dwrapper.dim[min_e:max_e]

########################################################################
## scalar or vector -> same                                           ##
########################################################################

def multiply(dwrapper, factor):
    """Multiply data by scale factor"""
    dwrapper.data = float(factor)*dwrapper.data
    dwrapper.label = ('%s*(%s)' %(factor, dwrapper.label[0]),)

def divide(dwrapper, factor):
    """Divide data by scale factor"""
    dwrapper.data = dwrapper.data/float(factor)
    dwrapper.label = ('(%s)/%s' %(dwrapper.label[0], factor),)

def subtract(dwrapper, value):
    """Subtract the value.

    Value can be a URL, with shot replaced by %(shot)d
    (only operations using the same shot are presently supported)
    """

    if value.startswith("http://"):
        url = value %{'shot':dwrapper.original_mds['shot']}
        # make sure we get the JSON view, in case the user didn't add view=json
        # Split URL into [scheme, netloc, path, params, query, fragments]
        parsed_url = urlparse(url)

        # parsed_url is an immutable ParseResult instance, copy it to a (mutable) list
        parsed_url_list = [i for i in parsed_url]
        
        # Now we can update the URL query string to enforce the JSON view.
        parsed_url_list[4] = '&'.join([parsed_url[4], 'view=json'])
        
        # And here is our original URL with view=json query added
        attr_url_json = urlunparse(parsed_url_list)
        request = urllib2.Request(attr_url_json)
        response = json.loads(urllib2.urlopen(request).read())
        value = float(response['data'])
        
    else:
        value = float(value)

    dwrapper.data = dwrapper.data - value
    dwrapper.label = ('%s - %s' %(dwrapper.label[0], value),)
