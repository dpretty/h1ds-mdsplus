from urlparse import urlparse, urlunparse
import urllib2, json
from django.core.urlresolvers import reverse
import MDSplus
import numpy as np

def http_arg(dwrapper, arg):
    if arg.startswith("http://"):
        url = arg.replace('__shot__', str(dwrapper.original_mds['shot']))
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

        return response['data']
    else:
        return arg

def float_or_array(data):
    """Data will probably be a string or a list, convert it to a float or np array."""
    if isinstance(data, list):
        return np.array(data)
    else:
        return float(data)


binary_powers = 2**np.arange(30)

########################################################################
## signal -> scalar                                                   ##
########################################################################

def first_pulse(dwrapper, threshold):
    """Return first dimension (i.e. time) when the signal is greater than threshold.

    threshold can be a number or 'mid'.
    threshold = 'mid' will use (max(signal)+min(signal))/2
    """

    _threshold = http_arg(dwrapper, threshold)
    if _threshold.lower() == 'mid':
        _threshold = (max(dwrapper.data)+min(dwrapper.data))/2
    else:
        _threshold = float(_threshold)

    first_element = np.where(dwrapper.data>_threshold)[0][0]
    dwrapper.data = dwrapper.dim[first_element]
    dwrapper.dim = None
    dwrapper.label = ('first_pulse(%s, %s)' %(dwrapper.label[0], threshold), )

def pulse_width(dwrapper, threshold):
    """
    pulse width...

    """
    _threshold = http_arg(dwrapper, threshold)
    if _threshold.lower() == 'mid':
        _threshold = (max(dwrapper.data)+min(dwrapper.data))/2
    else:
        _threshold = float(_threshold)

    t = dwrapper.dim[dwrapper.data>_threshold]
    end1 = dwrapper.dim[(dwrapper.data[:-1]-dwrapper.data[1:])>_threshold]

    use_size = min([len(t), len(end1)])

    dwrapper.data = np.min(end1[:use_size]-t[:use_size])
    dwrapper.dim = None
    dwrapper.label = ('pulse_width(%s, %s)' %(dwrapper.label[0], threshold), )


def pulse_number(dwrapper, threshold):
    """
    number of pulses...??

    """
    _threshold = http_arg(dwrapper, threshold)
    if _threshold.lower() == 'mid':
        _threshold = (max(dwrapper.data)+min(dwrapper.data))/2
    else:
        _threshold = float(_threshold)

    t = dwrapper.dim[dwrapper.data>_threshold]
    end1 = dwrapper.dim[(dwrapper.data[:-1]-dwrapper.data[1:])>_threshold]

    # TODO: should no need to cast this as int32, but there is some bizarre problem
    # with dtype_mapping key... without casting the result of np.min, type(dwrapper.data)
    # says it is numpy.int32, but it is somehow different to the numpy.int32 in the dtype_mapping key.
    dwrapper.data = np.int32(np.min([t.shape[0], end1.shape[0]]))
    dwrapper.dim = None
    dwrapper.label = ('pulse_number(%s, %s)' %(dwrapper.label[0], threshold), )


def max_val(dwrapper):
    """TODO: test for 2+ dimensional arrays"""
    dwrapper.data = np.max(dwrapper.data)
    dwrapper.dim = None
    dwrapper.label = ('max(%s)' %dwrapper.label[0],)


def max_of(dwrapper, value):
    """Returns max(data, value).

    if the data is an array, an array is returned with each element having max(data[element], value)
    value should be a float

    """
    _value = float(http_arg(dwrapper, value))
    if isinstance(dwrapper.data, np.ndarray):
        dwrapper.data[dwrapper.data<_value] = _value
    else:
        dwrapper.data =  np.max([dwrapper.data, _value])
    dwrapper.label = ('max_of(%s, %s)' %(dwrapper.label[0], value),)

def dim_of_max_val(dwrapper):
    """Returns dim at signal peak.

    """

    dwrapper.data = dwrapper.dim[np.argmax(dwrapper.data)]
    dwrapper.dim = None
    dwrapper.label = ('dim_of_max_val(%s)' %dwrapper.label[0],)


def mean(dwrapper):
    """TODO: test for 2+ dimensional arrays"""
    if len(dwrapper.data) > 0:
        dwrapper.data = np.mean(dwrapper.data)
    else:
        dwrapper.data = None
    dwrapper.dim = None
    dwrapper.label = ('mean(%s)' %dwrapper.label[0],)

def element(dwrapper, index):
    """Get an element of an array.

    The first element has index 0.
    """
    _index = int(http_arg(dwrapper, index))
    dwrapper.data = dwrapper.data[_index]
    dwrapper.dim = None
    dwrapper.label = ('%s[%s]' %(dwrapper.label[0], index),)

def peak_to_peak(dwrapper):
    """Max(signal) - min(signal)."""
    dwrapper.data = max(dwrapper.data) - min(dwrapper.data)
    dwrapper.dim = None
    dwrapper.label = ('max(%(lab)s)-min(%(lab)s)' %{'lab':dwrapper.label[0]},)

def n_signals(dwrapper):
    """Single trace returns 1, images return > 1"""
    dwrapper.data = np.int16(dwrapper.data.ndim)
    dwrapper.dim = None
    dwrapper.label = ('n_signals(%(lab)s)' %{'lab':dwrapper.label[0]},)

########################################################################
## signal -> signal                                                   ##
########################################################################

def slanted_baseline(dwrapper, window):
    """Remove linear baseline.

    window must be an integer.

    endpoints are computed at the first (window) and last (window) samples.

    """
    _window = int(http_arg(dwrapper, window))
    start = np.mean(dwrapper.data[:_window])
    end = np.mean(dwrapper.data[-_window:])

    baseline = start + (end-start)*np.arange(dwrapper.data.shape[0], dtype=float)/(dwrapper.data.shape[0]-1)
    dwrapper.data -= baseline
    dwrapper.label = ('slanted_baseline(%(lab)s, %(win)s)' %{'lab':dwrapper.label[0], 'win':window},)

def _do_prl_lpn(signal, dim, f0, order):
    """This  function is required  to handle  the recursion  in prl_lpn.

    Handle  only the  signal,  not  the data  wrapper.  Also, we  assume
    arguments have already been cast to numeric types.
    """
    N = int(0.5 + 0.5/(dim[1]-dim[0])/f0)
    a = np.cumsum(signal)
    if order > 1:
        return _do_prl_lpn(_do_prl_lpn(signal, dim, f0, order-1), dim, f0, 1)
    else:
        return (a[N:]-a[:-N])/float(N)

def prl_lpn(dwrapper, f0, order):
    """prl_lpn

    TODO: only working for order = 1
    """
    _f0 = float(http_arg(dwrapper, f0))
    _order = int(http_arg(dwrapper, order))
    dwrapper.data = _do_prl_lpn(dwrapper.data, dwrapper.dim, _f0, _order)
    dwrapper.label = ('prl_lpn(%s, %s, %s)' %(dwrapper.label[0], f0, order),)

def resample(dwrapper, max_samples):
    _max_samples = int(http_arg(dwrapper, max_samples))
    signal_length = dwrapper.data.T.shape[0]
    delta_sample = signal_length/_max_samples

    # put trailing [:max_samples] in case we get an extra one at the end
    dwrapper.data = dwrapper.data[::delta_sample][:_max_samples]
    dwrapper.dim = dwrapper.dim[::delta_sample][:_max_samples]
    dwrapper.label = ('resample(%s, %s)' %(dwrapper.label[0], max_samples),)


def resample_minmax(dwrapper, n_bins):
    """TODO: only works for 1D array..."""
    _n_bins = int(http_arg(dwrapper, n_bins))
    signal_length = dwrapper.data.T.shape[0]
    if signal_length >= 2*_n_bins:
        delta_sample = signal_length/_n_bins
        dwrapper.dim = dwrapper.dim[::delta_sample][:_n_bins]
        max_data = []
        min_data = []

        for i in range(_n_bins):
            tmp = dwrapper.data[i*delta_sample:(i+1)*delta_sample]
            max_data.append(max(tmp))
            min_data.append(min(tmp))

        dwrapper.label = ('min', 'max',)
        dwrapper.data = np.array([min_data, max_data])

def norm_dim_range(dwrapper, min_val, max_val):
    """Reduce range of signal."""
    _min_val = float(http_arg(dwrapper, min_val))
    _max_val = float(http_arg(dwrapper, max_val))
    min_e, max_e = int(_min_val*len(dwrapper.dim)), int(_max_val*len(dwrapper.dim))
    dwrapper.data = dwrapper.data[min_e:max_e]
    dwrapper.dim = dwrapper.dim[min_e:max_e]
    dwrapper.label = ('normdim_range(%s, %s, %s)' %(dwrapper.label[0], min_val, max_val),)

def dim_range(dwrapper, min_val, max_val):
    """Reduce range of signal."""
    _min_val = float(http_arg(dwrapper, min_val))
    _max_val = float(http_arg(dwrapper, max_val))
    min_e, max_e = np.searchsorted(dwrapper.dim, [_min_val, _max_val])
    dwrapper.data = dwrapper.data[min_e:max_e]
    dwrapper.dim = dwrapper.dim[min_e:max_e]
    dwrapper.label = ('dim_range(%s, %s, %s)' %(dwrapper.label[0], min_val, max_val),)

def power_spectrum(dwrapper):
    """power spectrum of signal."""
    output_size = 2**np.searchsorted(binary_powers, dwrapper.data.shape[0])
    dwrapper.data = np.abs(np.fft.fft(dwrapper.data, n=output_size))
    length = len(dwrapper.data)
    sample_rate = np.mean(dwrapper.dim[1:] - dwrapper.dim[:-1])
    dwrapper.dim = (1./sample_rate)*np.arange(length)/(length-1)
    dwrapper.label = ('power_spectrum(%s)' %(dwrapper.label[0]),)

# TODO: generalise energy limits between 1d and 2d signals.
def x_axis_energy_limit(dwrapper, threshold):
    """for 1d signal, limit range to include fraction of total energy"""
    _threshold = float(http_arg(dwrapper, threshold))

    ## TODO: need to get x,y dimensions standardised for matrix
    ## which dimension should be which??

    total_power = np.sum(dwrapper.data.ravel()**2)

    removed_power = 0
    while removed_power < (1-_threshold)*total_power:
        lower = dwrapper.data[0]**2
        upper = dwrapper.data[-1]**2
        if (min(lower, upper) + removed_power) > _threshold*total_power:
            break
        if lower < upper:
            dwrapper.data = dwrapper.data[1:]
            dwrapper.dim = dwrapper.dim[1:]
            removed_power += lower
        else:
            dwrapper.data = dwrapper.data[:-1]
            dwrapper.dim = dwrapper.dim[:-1]
            removed_power += upper


########################################################################
## scalar or vector -> same                                           ##
########################################################################

def multiply(dwrapper, factor):
    """Multiply data by scale factor"""

    _factor = float_or_array(http_arg(dwrapper, factor))

    dwrapper.data = _factor*dwrapper.data
    dwrapper.label = ('%s*(%s)' %(factor, dwrapper.label[0]),)

def divide(dwrapper, factor):
    """Divide data by scale factor"""
    _factor = float(http_arg(dwrapper, factor))
    dwrapper.data = dwrapper.data/_factor
    dwrapper.label = ('(%s)/%s' %(dwrapper.label[0], factor),)

def subtract(dwrapper, value):
    """Subtract the value.

    """
    _value = float(http_arg(dwrapper, value))

    dwrapper.data = dwrapper.data - _value
    dwrapper.label = ('%s - %s' %(dwrapper.label[0], value),)

def add(dwrapper, value):
    """Add the value.

    """
    _value = float(http_arg(dwrapper, value))

    dwrapper.data = dwrapper.data + _value
    dwrapper.label = ('%s + %s' %(dwrapper.label[0], value),)

def exponent(dwrapper, value):
    """Raise data to the (value)th power."""

    _value =float(http_arg(dwrapper, value))
    dwrapper.data = dwrapper.data**_value
    dwrapper.label = ('%s^%s' %(dwrapper.label[0], value),)


########################################################################
## 1d signals -> 2d                                                   ##
########################################################################

def spectrogram(dwrapper, bin_size):
    """spectrogram of signal. use bin_size=-1 for auto"""
    _bin_size =int(http_arg(dwrapper, bin_size))
    if _bin_size < 0:
        # have a guess...
        approx_bin_size = np.sqrt(len(dwrapper.dim))
        _bin_size=2**np.searchsorted(binary_powers, approx_bin_size)
    sample_rate = np.mean(dwrapper.dim[1:] - dwrapper.dim[:-1])

    new_x_dim = dwrapper.dim[::_bin_size]
    new_y_dim = (1./sample_rate)*np.arange(_bin_size,dtype=float)/(_bin_size-1)

    #new_y_dim = new_y_dim[:_bin_size/2]

    new_data = []
    for t_el in np.arange(len(dwrapper.data))[::_bin_size]:
        #new_data.append(np.abs(np.fft.fft(dwrapper.data[t_el:t_el+_bin_size],n=_bin_size)[:_bin_size/2]).tolist())
        new_data.append(np.abs(np.fft.fft(dwrapper.data[t_el:t_el+_bin_size],n=_bin_size)[:_bin_size]).tolist())

    dwrapper.data = np.array(new_data)

    # TODO: this is a hack because I don't properly understand how numpy
    # determines dtypes - if new x and y dims are the same then it will have
    # dtype of float, etc. if different length it will be object dtype
    # object dtype is what we are using, as we can get different lengths for
    # different dimensions. (Should we even use a numpy array? How does MDSplus
    # perfer to deal with higher dim signals? - we should use the same format as
    # MDSplus). Anyway - it seems that even if we assert dtype to be object
    # >>> q=np.array([[1,2,3],[2,3,4]], dtype=np.object)
    # >>> q[1] = q[1][:2] ** fails
    # it fails when we later try and have different shaped elements.
    # So, let's create dwrapper.dim as something we know we can resizt
    dwrapper.dim = np.array([[None],[None, None]])
    dwrapper.dim[0] = new_x_dim.tolist()
    dwrapper.dim[1] = new_y_dim.tolist()

    dwrapper.label = ('spectrogram(%s,%d)' %(dwrapper.label[0],_bin_size),)



########################################################################
## 2d signals                                                         ##
########################################################################

def shape(dwrapper):
    """Shape of image"""
    dwrapper.data = {"rows":dwrapper.data.shape[0],
                    "columns":dwrapper.data.shape[1]}
    dwrapper.dim = None
    dwrapper.label = ('shape(%s)' %(dwrapper.label[0]),)

def transpose(dwrapper):
    """Transpose a 2d array"""
    dwrapper.data = np.transpose(dwrapper.data)
    #TODO: how to treat dim?
    dwrapper.label = ('transpose(%s)' %(dwrapper.label[0]),)

def flip_vertical(dwrapper):
    """Flip array vertically"""
    tmp_data = dwrapper.data.copy()
    for r in xrange(tmp_data.shape[0]/2):
        dwrapper.data[r,:] = tmp_data[-(r+1),:]
        dwrapper.data[-(r+1),:] = tmp_data[r,:]
    #TODO: how to treat dim?
    dwrapper.label = ('vertical_flip(%s)' %(dwrapper.label[0]),)

def flip_horizontal(dwrapper):
    """Flip array vertically"""
    tmp_data = dwrapper.data.copy()
    for c in xrange(tmp_data.shape[1]/2):
        dwrapper.data[:,c] = tmp_data[:,-(c+1)]
        dwrapper.data[:,-(c+1)] = tmp_data[:,c]
    #TODO: how to treat dim?
    dwrapper.label = ('horizontal_flip(%s)' %(dwrapper.label[0]),)

def norm_dim_range_2d(dwrapper, min_x_val, max_x_val, min_y_val, max_y_val):
    """Reduce range of signal."""
    _min_x_val = float(http_arg(dwrapper, min_x_val))
    _max_x_val = float(http_arg(dwrapper, max_x_val))
    _min_y_val = float(http_arg(dwrapper, min_y_val))
    _max_y_val = float(http_arg(dwrapper, max_y_val))

    min_xe, max_xe = int(_min_x_val*len(dwrapper.dim[0])), int(_max_x_val*len(dwrapper.dim[0]))
    min_ye, max_ye = int(_min_y_val*len(dwrapper.dim[1])), int(_max_y_val*len(dwrapper.dim[1]))

    dwrapper.data = dwrapper.data[min_xe:max_xe,min_ye:max_ye]
    dwrapper.dim[0] = dwrapper.dim[0][min_xe:max_xe]
    dwrapper.dim[1] = dwrapper.dim[1][min_ye:max_ye]
    dwrapper.label = ('2d_normdim_range(%s, %s, %s, %s, %s)' %(dwrapper.label[0], min_x_val, max_x_val,min_y_val,max_y_val),)

def y_axis_energy_limit(dwrapper, threshold):
    "2D reduce y-axis range to threshold*100% of total signal energy"
    _threshold = float(http_arg(dwrapper, threshold))

    ## TODO: need to get x,y dimensions standardised for matrix
    ## which dimension should be which??

    total_power = np.sum(dwrapper.data.ravel()**2)

    # if the result is going to be less than min_y_resolution then don't do it.
    min_y_resolution = 10

    low_counter = 0
    high_counter = -1
    removed_power = 0
    while removed_power < (1-_threshold)*total_power:
        lower = np.sum(dwrapper.data[:,low_counter]**2)
        upper = np.sum(dwrapper.data[:,high_counter]**2)
        if (min(lower, upper) + removed_power) > _threshold*total_power:
            break
        if lower < upper:
            removed_power += lower
            low_counter += 1
        else:
            removed_power += upper
            high_counter -= 1
    if len(dwrapper.dim[1][low_counter:high_counter]) > min_y_resolution:
        dwrapper.data = dwrapper.data[:,low_counter:high_counter]
        dwrapper.dim[1] = dwrapper.dim[1][low_counter:high_counter]

########################################################################
## Other                                                              ##
########################################################################

def dim_of(dwrapper):
    """Return the dim of the data as the data."""

    dwrapper.data = dwrapper.dim
    dwrapper.dim = np.arange(len(dwrapper.data))
    dwrapper.label = ('dim_of(%s)' %(dwrapper.label[0]),)
