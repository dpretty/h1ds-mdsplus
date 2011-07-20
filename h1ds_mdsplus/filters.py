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


def mean(dwrapper):
    """TODO: test for 2+ dimensional arrays"""
    dwrapper.data = np.mean(dwrapper.data)
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

def dim_range(dwrapper, min_val, max_val):
    """Reduce range of signal."""
    _min_val = float(http_arg(dwrapper, min_val))
    _max_val = float(http_arg(dwrapper, max_val))
    min_e, max_e = np.searchsorted(dwrapper.dim, [_min_val, _max_val])
    dwrapper.data = dwrapper.data[min_e:max_e]
    dwrapper.dim = dwrapper.dim[min_e:max_e]
    dwrapper.label = ('dim_range(%s, %s, %s)' %(dwrapper.label[0], min_val, max_val),)

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
## Other                                                              ##
########################################################################

def dim_of(dwrapper):
    """Return the dim of the data as the data."""

    dwrapper.data = dwrapper.dim
    dwrapper.dim = np.arange(len(dwrapper.data))
    dwrapper.label = ('dim_of(%s)' %(dwrapper.label[0]),)


########################################################################
## summdb filters TODO list...
##
##
## [X] tt_sec /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:TT"
## [X] rga_imax /home/datasys/bin/h1data_mdsvalue.py "maxval(.operations:rga_i)"
## [X] th_main /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.LOG:THERMAL_MAIN"
## [X] i_ring /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:I_RING,-0.1, -0.05 )"
## [X] la_slit /home/datasys/bin/h1data_mdsvalue.py ".SPECTROSCOPY.SURVEY:SLIT_WIDTH"
## [X] ech_ib /home/datasys/bin/h1data_mdsvalue.py "maxval(.ech:i_coll)"
## [X] gas1_M /home/datasys/bin/h1data_mdsvalue.py "data(.LOG.MACHINE:GAS1_Z)[1]"
## [X] mains /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:V240_RMS,-4.1, -3.5)*2.4/2.35"
## [X] mag_fl1 /home/datasys/bin/h1data_mdsvalue.py "prl_var(.electr_dens.camac:a14_5:input_4, .005, .075)"
## [X] rfptop /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.rf:p_fwd_top, 20,1))"
## [X] la_dial /home/datasys/bin/h1data_mdsvalue.py ".SPECTROSCOPY.SURVEY:DIAL"
## [X] hxray_0 /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.operations:HXRAY_0, 1,1))"
## [X] wg_bolo /home/datasys/bin/h1data_mdsvalue.py "1e3*(maxval(prl_lpn(.ech:wg_bolo,1))-prl_mean(.ech:wg_bolo,-1.1, -0.1 ))"
## [X] th_sec /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.LOG:THERMAL_SEC"
## [X] v_main /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:V_MAIN,-0.6, -0.1 )"
## [X] v_sec /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:V_SEC, -0.6, -0.1)"
## [X] HDB_del /home/datasys/bin/h1data_mdsvalue.py "first_pulse(.spectroscopy.line_ratio.raw_signals:pulse)"
## [X] im1 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:I1"
## [X] gas3_flow /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS3_FLOW"
## [X] is2 /home/datasys/bin/h1data_mdsvalue_int.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:I2"
## [X] is1 /home/datasys/bin/h1data_mdsvalue_int.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:I1"
## [X] mains_droop /home/datasys/bin/h1data_mdsvalue.py "(prl_mean(.OPERATIONS:V240_RMS, -0.6, -0.1) - prl_mean(.OPERATIONS:V2## 40_RMS,-4.1, -3.5))/2.35"
## [X] rf_drive /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.rf:rf_drive,0,.05)"
## [X] t_mid /home/datasys/bin/h1data_mdsvalue.py "mean(.operations:i_fault^10*dim_of(.operations:i_fault))/mean(.operations:i## _fault^10)"
## [X] gas1_Z /home/datasys/bin/h1data_mdsvalue.py "data(.LOG.MACHINE:GAS1_Z)[0]"
## [X] ech_vb /home/datasys/bin/h1data_mdsvalue.py "maxval(slanted_baseline(.ech:v_beam,200))"
## [X] gas3_z /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS3_Z"
## [X] p_iong /home/datasys/bin/h1data_mdsvalue.py "1e6*prl_mean(.operations:iong_300t,-4.1, -3.5)"
## [X] rftune2 /home/datasys/bin/h1data_mdsvalue.py ".LOG.HEATING:RFTUNE2"
## [X] i_f_sl /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.operations:i_fault, 0.5,1))"
## [X] gas2_flow /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS2_FLOW"
## [X] la_int /home/datasys/bin/h1data_mdsvalue.py "maxval(.SPECTROSCOPY.SURVEY:LARRY)"
## [X] puff_v /home/datasys/bin/h1data_mdsvalue.py "maxval(.operations:puff_135)-minval(.operations:puff_135)"
## [X] rf_peak /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.rf:p_fwd_top, 200,1))"
## [X] is3 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:I3"
## [X] t_snap /home/datasys/bin/h1data_mdsvalue.py "0.03"
## [X] dia_var /home/datasys/bin/h1data_mdsvalue.py "prl_var(.OPERATIONS:DIAMAG, -.06, -.01)"
## [X] gas2_Z /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS2_Z"
## [X] ech_est /home/datasys/bin/h1data_mdsvalue.py "maxval(5*max((slanted_baseline(.ech:v_beam,200)-60),0)*(.ech:i_coll-4))"
## [X] tt_main /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:TT"
## [X] ne18_bmax /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.electr_dens.ne_het:ne_centre, 1000,1))"
## [X] b_p6 /home/datasys/bin/h1data_mdsvalue.py "1e6*.LOG.MACHINE:BASE_PRESS"
## [X] ech_pulse /home/datasys/bin/h1data_mdsvalue.py "-1"
## [X] rftune1 /home/datasys/bin/h1data_mdsvalue.py ".LOG.HEATING:RFTUNE1"
## [X] mag_fllf /home/datasys/bin/h1data_mdsvalue.py "prl_var(prl_lpn(.electr_dens.camac:a14_5:input_4, 15000,1),.005,.075)"
## [X] rftune4 /home/datasys/bin/h1data_mdsvalue.py ".LOG.HEATING:RFTUNE4"
## [X] im3 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:I3"
## [X] im2 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:I2"
## [X] i_f_pk /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.operations:i_fault, 10,1))"
## [X] HDB_num /home/datasys/bin/h1data_mdsvalue.py "pulse_number(.spectroscopy.line_ratio.raw_signals:pulse)"
## [X] HDB_wid /home/datasys/bin/h1data_mdsvalue.py "pulse_width(.spectroscopy.line_ratio.raw_signals:pulse)"
## [X] la_trim /home/datasys/bin/h1data_mdsvalue.py ".SPECTROSCOPY.SURVEY:TRIM"
## [X] i_main /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:I_RING,-0.2, -0.1 )"

## [X] i_sec /home/datasys/bin/mean_mdsvalue.py ".operations:i_sec"
## [X] i_fault /home/datasys/bin/mean_mdsvalue.py ".operations:i_fault"
## [X] i_top /home/datasys/bin/mean_mdsvalue.py ".rf:i_top"
## [X] i_bot /home/datasys/bin/mean_mdsvalue.py ".rf:i_bot"

## [X] ne18_bar /home/datasys/bin/mean_mdsvalue_check_baseline.py ".electr_dens.ne_het:ne_centre"
## [X] w_dia /home/datasys/bin/mean_mdsvalue_check_baseline.py ".operations:diamag"
## [X] rf_power /home/datasys/bin/mean_mdsvalue_check_baseline.py ".rf:p_rf_net"

## [X] k_h /home/datasys/bin/kappa.py h
## [X] k_v /home/datasys/bin/kappa.py v
## [X] k_i /home/datasys/bin/kappa.py i
## [X] recorded /home/datasys/bin/gettime
## [ ] lcu_gas_1_flow /home/datasys/bin/gas_flow.py 1
## [ ] lcu_gas_2_flow /home/datasys/bin/gas_flow.py 2
## [ ] lcu_gas_3_flow /home/datasys/bin/gas_flow.py 3
## [ ] lcu_gas_4_flow /home/datasys/bin/gas_flow.py 4
## [ ] lcu_gas_5_flow /home/datasys/bin/gas_flow.py 5
## [ ] shunt_kh /home/datasys/bin/shunt_kh.py
##
##
########################################################################
########################################################################
