import sys
import numpy
import time, logging


log = logging.getLogger(__name__)

def calculate_new_slope_and_intercept(current_slope, current_intercept, ymeasured1, ymeasured2, yexpected1 = 10, yexpected2 = 20):
    print "debug: current_slope:", current_slope
    print "debug: current_intercept", current_intercept
    print "debug: ymeasured1", str(ymeasured1)
    print "debug: ymeasured2", str(ymeasured2)

    milli_current_intercept = float(current_intercept) / 1000
    milli_current_slope = float(current_slope) / 1000

    xexpected1 = (yexpected1 - milli_current_intercept) / milli_current_slope
    xexpected2 = (yexpected2 - milli_current_intercept) / milli_current_slope

    a = (ymeasured2 - ymeasured1) / (xexpected2 - xexpected1)
    b = ymeasured1 - a * xexpected1
    
    new_slope = int(round(a * 1000))
    new_intercept = int(round(b * 1000))

    print "debug: new_slope:", new_slope
    print "debug: new_intercept", new_intercept
    return new_slope, new_intercept

def adjust_tssi_calibration(ip, port, plug_id, macIf, ymeasured10, ymeasured20):
    #Find uboot parameter names
    assert(macIf in (0, 1))
    slope_field = "tssi_" + str(macIf) + "_pslope"
    intercept_field = "tssi_" + str(macIf) + "_pintercept"
    
    #Get current slope and intercept from uboot
    u = uboot(ip, port, plug_id)
    u.enter_uboot()
    d = u.get_dict()
    current_slope = d[slope_field]
    current_intercept = d[intercept_field]
    
    
    #Calculate new slope and intercept
    new_slope, new_intercept = calculate_new_slope_and_intercept(current_slope = current_slope,
                                                                 current_intercept = current_intercept,
                                                                 ymeasured1 = ymeasured10,
                                                                 ymeasured2 = ymeasured20)
    
    #Save new slope and intercept in uboot
    u.set_dict({slope_field : new_slope, intercept_field : new_intercept})
    del u
    
    return new_slope, new_intercept

#def adjust_tx_power(ip = 0, port = 0, plug_id = 0, macIf = 0, detector_meas = None, tx_power_dbm = None):
def adjust_tx_power( macIf = 0, detector_meas = None, tx_power_dbm = None):
    mean_list = []
    chunk_size = 4      # group of 4 values
    res = calculate_pant_vector(detector_meas, tx_power_dbm)
    splitted_list = list(chunks(res,chunk_size))
    for i in range(len(splitted_list)):
        # Remove 0 from calculation
        if i == splitted_list[0][0]:
            chunk_size = chunk_size-1
        else:
            chunk_size = 4
        mean_list.append(sum(splitted_list[i])/chunk_size)
    '''
    for k in mean_list:
        print k
    '''
    pant_lut_vector_list = []
    LOW_LIMIT = -7
    HIGH_LIMIT = 40
    for value in mean_list:
        if ( LOW_LIMIT > (value) ):
            pant_lut_vector_list.append( LOW_LIMIT )
        elif ( (value) > HIGH_LIMIT ):
            pant_lut_vector_list.append( HIGH_LIMIT )
        else:
            pant_lut_vector_list.append( int( round(value) ) )
            #print "Current value {}".format(float(format(value,'0.2f')))
    #print "Final vector_list: {:s}".format(pant_lut_vector_list)

    final_vector = ','.join(str(x) for x in pant_lut_vector_list)
    #log.debug("pant_lut_vector_list = ",str(pant_lut_vector_list)[1:-1].replace(" ",""))  # ','.join(str(x) for x in pant_lut_vector_list))
    #log.debug("pant_lut_vector_list = {}".format(final_vector))

    # return cleaned result, without [] and spaces, equivalent to ','.join(str(x) for x in pant_lut_vector_list)
    #return str(pant_lut_vector_list)[1:-1].replace(" ","")
    return final_vector

#  Split sequence into equal n size chunks
def chunks(seq, n):
    return (seq[i:i+n] for i in xrange(0, len(seq), n))

def calculate_pant_vector(detector_meas, tx_power_dbm):
    x = range(0,1024)
    y = []      # y is list of collect calculations of selected polinom p(x)

    # Calculate least squares polynomial fit
    # Returns a vector of coefficients p that minimises the squared error
    p_coef_min_sq = numpy.poly1d( numpy.polyfit( detector_meas, tx_power_dbm, deg=5 ) )
    
    # Calculate natural logarithm function y = A*ln(x) + B
    # Returns a vector of polinom coefficients
    p_coef_log = numpy.polyfit( numpy.log(detector_meas), tx_power_dbm, deg=1 )

    # Select polinom and perform calculations
    for i in x:
        if i in range( int(round(detector_meas[-1])), int(round(detector_meas[0])) ):
            #log.debug( "polinom 5deg, y = {:s}".format(str(p_coef_min_sq)))
            # Using calculated least squares polynomial fit
            y.append(p_coef_min_sq(i))
        else:
            # Using natural logarithm function y = A*ln(x) + B
            if i == 0:
                y.append(0)
            else:
                y.append(p_coef_log[0]* numpy.log(i) + p_coef_log[1])
            #log.debug("polinom 1deg, y = {:s}".format(str(p_coef_log)))
        #print p(i)
    return y
