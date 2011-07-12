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
    dwrapper.data = _do_prl_lpn(dwrapper.data, dwrapper.dim, float(f0), int(order))
    dwrapper.label = ('prl_lpn(%s, %s, %s)' %(dwrapper.label[0], f0, order),)

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
## [ ] wg_bolo /home/datasys/bin/h1data_mdsvalue.py "1e3*(maxval(prl_lpn(.ech:wg_bolo,1))-prl_mean(.ech:wg_bolo,-1.1, -0.1 ))"
## [ ] th_sec /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.LOG:THERMAL_SEC"
## [ ] v_main /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:V_MAIN,-0.6, -0.1 )"
## [ ] v_sec /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:V_SEC, -0.6, -0.1)"
## [ ] HDB_del /home/datasys/bin/h1data_mdsvalue.py "first_pulse(.spectroscopy.line_ratio.raw_signals:pulse)"
## [ ] im1 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:I1"
## [ ] gas3_flow /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS3_FLOW"
## [ ] is2 /home/datasys/bin/h1data_mdsvalue_int.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:I2"
## [ ] is1 /home/datasys/bin/h1data_mdsvalue_int.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:I1"
## [ ] mains_droop /home/datasys/bin/h1data_mdsvalue.py "(prl_mean(.OPERATIONS:V240_RMS, -0.6, -0.1) - prl_mean(.OPERATIONS:V2## 40_RMS,-4.1, -3.5))/2.35"
## [ ] rf_drive /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.rf:rf_drive,0,.05)"
## [ ] t_mid /home/datasys/bin/h1data_mdsvalue.py "mean(.operations:i_fault^10*dim_of(.operations:i_fault))/mean(.operations:i## _fault^10)"
## [ ] gas1_Z /home/datasys/bin/h1data_mdsvalue.py "data(.LOG.MACHINE:GAS1_Z)[0]"
## [ ] ech_vb /home/datasys/bin/h1data_mdsvalue.py "maxval(slanted_baseline(.ech:v_beam,200))"
## [ ] gas3_z /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS3_Z"
## [ ] p_iong /home/datasys/bin/h1data_mdsvalue.py "1e6*prl_mean(.operations:iong_300t,-4.1, -3.5)"
## [ ] rftune2 /home/datasys/bin/h1data_mdsvalue.py ".LOG.HEATING:RFTUNE2"
## [ ] i_f_sl /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.operations:i_fault, 0.5,1))"
## [ ] gas2_flow /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS2_FLOW"
## [ ] la_int /home/datasys/bin/h1data_mdsvalue.py "maxval(.SPECTROSCOPY.SURVEY:LARRY)"
## [ ] puff_v /home/datasys/bin/h1data_mdsvalue.py "maxval(.operations:puff_135)-minval(.operations:puff_135)"
## [ ] rf_peak /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.rf:p_fwd_top, 200,1))"
## [ ] is3 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_SEC:I3"
## [ ] t_snap /home/datasys/bin/h1data_mdsvalue.py "0.03"
## [ ] dia_var /home/datasys/bin/h1data_mdsvalue.py "prl_var(.OPERATIONS:DIAMAG, -.06, -.01)"
## [ ] gas2_Z /home/datasys/bin/h1data_mdsvalue.py ".LOG.MACHINE:GAS2_Z"
## [ ] ech_est /home/datasys/bin/h1data_mdsvalue.py "maxval(5*max((slanted_baseline(.ech:v_beam,200)-60),0)*(.ech:i_coll-4))"
## [ ] tt_main /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:TT"
## [ ] ne18_bmax /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.electr_dens.ne_het:ne_centre, 1000,1))"
## [ ] b_p6 /home/datasys/bin/h1data_mdsvalue.py "1e6*.LOG.MACHINE:BASE_PRESS"
## [ ] ech_pulse /home/datasys/bin/h1data_mdsvalue.py "-1"
## [ ] rftune1 /home/datasys/bin/h1data_mdsvalue.py ".LOG.HEATING:RFTUNE1"
## [ ] mag_fllf /home/datasys/bin/h1data_mdsvalue.py "prl_var(prl_lpn(.electr_dens.camac:a14_5:input_4, 15000,1),.005,.075)"
## [ ] rftune4 /home/datasys/bin/h1data_mdsvalue.py ".LOG.HEATING:RFTUNE4"
## [ ] im3 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:I3"
## [ ] im2 /home/datasys/bin/h1data_mdsvalue.py ".OPERATIONS.MAGNETSUPPLY.LCU.SETUP_MAIN:I2"
## [ ] i_f_pk /home/datasys/bin/h1data_mdsvalue.py "maxval(prl_lpn(.operations:i_fault, 10,1))"
## [ ] HDB_num /home/datasys/bin/h1data_mdsvalue.py "pulse_number(.spectroscopy.line_ratio.raw_signals:pulse)"
## [ ] HDB_wid /home/datasys/bin/h1data_mdsvalue.py "pulse_width(.spectroscopy.line_ratio.raw_signals:pulse)"
## [ ] la_trim /home/datasys/bin/h1data_mdsvalue.py ".SPECTROSCOPY.SURVEY:TRIM"
## [ ] i_main /home/datasys/bin/h1data_mdsvalue.py "prl_mean(.OPERATIONS:I_RING,-0.2, -0.1 )"
## [ ] i_sec /home/datasys/bin/mean_mdsvalue.py ".operations:i_sec"
## [ ] i_fault /home/datasys/bin/mean_mdsvalue.py ".operations:i_fault"
## [ ] i_top /home/datasys/bin/mean_mdsvalue.py ".rf:i_top"
## [ ] i_bot /home/datasys/bin/mean_mdsvalue.py ".rf:i_bot"
## [ ] ne18_bar /home/datasys/bin/mean_mdsvalue_check_baseline.py ".electr_dens.ne_het:ne_centre"
## [ ] w_dia /home/datasys/bin/mean_mdsvalue_check_baseline.py ".operations:diamag"
## [ ] rf_power /home/datasys/bin/mean_mdsvalue_check_baseline.py ".rf:p_rf_net"
## [ ] k_h /home/datasys/bin/kappa.py h
## [ ] k_v /home/datasys/bin/kappa.py v
## [ ] k_i /home/datasys/bin/kappa.py i
## [ ] recorded /home/datasys/bin/gettime
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
