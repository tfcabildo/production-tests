# Copyright (C) 2022 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# AUTHOR: TRISHA CABILDO

import sys
import os
import time
import numpy as np
from adi import cn0579
import time
import sin_params as sp
import m2k_siggen as adalm2k

sin_amp = 5                                     # Amplitude of the m2k input signal (10 Vpp)
sin_freq = 1000                                 # 1kHz input signal
sin_offset = 0                                  # DC offset of input signal
sin_phase = 0                                   # Phase for input signal

vref = 5
n_samples = 4096                                # Number of samples taken
sampling_freq = 4000000                         # Master clock @32 MHz (f_sampling = master_clock / 8)
                                                """sample_rate: Sample rate in samples per second.
                                                Actual sample rates will be the master clock divided by an integer, for example,
                                                the CN0579 has a 32 MHz clock, so available sample rates will be:
                                                32 MHz / 8 = 4 Msps
                                                32 MHz / 9 = 3.556 Msps
                                                32 MHz / 10 = 3.2 Msps
                                                etc.
                                                """

BLACKMAN_HARRIS_92 = 0x30                       # Window type for FFT
def_window_type = BLACKMAN_HARRIS_92            # Window type for FFT
failed_tests = []                               # List for failed tests

# This function is to check if command line input is correct. Only one argument is needed (serial number of board being tested). If input is more than one argument, test code will exit.
def check_input():
    n = len(sys.argv)                           # Number of total arguments on command line
    if n != 2:
         sys.exit('\nIncorrect syntax! \nExample: python cn0579_prod_test.py 202205100001\n')
    return

# This function gets the serial number of the board from the command line arguments and print it.
def get_serial():
    print("\nSetting up serial number....")
    sn = sys.argv[1]

    # Checking if serial number is valid
    if len(sn) == 10 and sn.isdigit():
        print ("Serial number:", int(sn))
    else:
        sys.exit('\nIncorrect serial number! Must be 10 digits.\nExample: 202205100001\n')
    
    return sn

# Creates the object for the CN0579 DUT and sets its buffer size and sampling frequency
def setup_579(my_ip):
    my_cn0579 = adi.cn0579(my_ip)
    my_cn0579.rx_buffer_size = n_samples
    my_cn0579.sampling_freq = sampling_freq
    my_adc.power_mode = "FAST_MODE"
    my_adc.filter_type = "WIDEBAND"
    my_adc.rx_output_type = "SI"

    return my_cn0579

def print_csource(my_cn0579):
    print("Current source CH0: %s" % my_cn0579.CC_CH0)
    print("Current source CH1: %s" % my_cn0579.CC_CH1)
    print("Current source CH2: %s" % my_cn0579.CC_CH2)
    print("Current source CH3: %s" % my_cn0579.CC_CH3)

    return

# Switches current source on/off. A is the channel number, while mode is on or off. Mode = 1 is on and the opposite for off.
def csource_switch(my_cn0579, a, mode):
    if mode = 1:
        time.sleep(1)
        if a = 0:
            my_cn0579.CC_CH0 = 1
        elif a = 1:
            my_cn0579.CC_CH1 = 1
        elif a = 2:
            my_cn0579.CC_CH2 = 1
        else:
            my_cn0579.CC_CH3 = 1
    else:
         if a = 0:
            my_cn0579.CC_CH0 = 0
        elif a = 1:
            my_cn0579.CC_CH1 = 0
        elif a = 2:
            my_cn0579.CC_CH2 = 0
        else:
            my_cn0579.CC_CH3 = 0
    
    time.sleep(2)
    print_csource(my_cn0579)
    return

def read_DC():
    volt_reading, ctx = adalm2k.voltmeter()
    print("DC input: %s" % volt_reading)
    if volt_reading (10.5 < x < 11.3):
            print("DC input PASS")
        else:
            failed_tests.append("DC input FAIL")
            sys.exit('Failed input DC check\n')
    
    time.sleep(2)
    return volt_reading, ctx

def set_shift(vr):
    vshift = ((vr * 0.3) + 2.5) / 1.3
    time.sleep(2)
    print("Calculated Vshift: %s" % vshift)
    return vshift

def print_DAC(my_cn0579):
    print("Channel 0 DAC: %s" % my_cn0579.shift_voltage0)
    print("Channel 1 DAC: %s" % my_cn0579.shift_voltage1)
    print("Channel 2 DAC: %s" % my_cn0579.shift_voltage2)
    print("Channel 3 DAC: %s" % my_cn0579.shift_voltage3)
    return

def set_DAC(vshift, z, my_cn0579):
    d_code = (65536 * vshift) / vref
    time.sleep(2)

    if z = 0:
        my_cn0579.shift_voltage0 = int(d_code)
        print("Setting channel 0 DAC: %s\n" % int(d_code))
    elif z = 1:
        my_cn0579.shift_voltage1 = int(d_code)
        print("Setting channel 1 DAC: %s\n" % int(d_code))
    elif z = 1:
        my_cn0579.shift_voltage2 = int(d_code)
        print("Setting channel 2 DAC: %s\n" % int(d_code))
    else:
        my_cn0579.shift_voltage3 = int(d_code)
        print("Setting channel 3 DAC: %s\n" % int(d_code))

    time.sleep(1)
    print_DAC(my_cn0579)
    return 

def fft_test(my_cn0579, test_in):
    adc_data = my_cn0579.rx()
    time.sleep(1.5)
    # x = np.arange(0, len(data))
    # adc_data = data * vref / (2 ** 24)
    dc = np.average(adc_data)
    time.sleep(1.5)

    if (sin_offset - 0.1) < dc < (sin_offset + 0.1):
        print("DC offset PASS")
    else:
        print("DC offset FAIL")
        failed_tests.append("Failed DC offset test")

    #windowed_fft_mag function takes in the analog data out of the ADC with its DC component. It removes the DC component within the function, thus 'voltage' is used
    fft_data = sp.windowed_fft_mag(adc_data, window_type=BLACKMAN_HARRIS_92)
    time.sleep(1)
    fund_amp, fund_bin = sp.get_max(fft_data)
    time.sleep(1)

    f_base = sampling_freq/n_samples
    time.sleep(1)
    freq_bin_theo = math.floor(sin_freq / f_base)
    time.sleep(1)

     #Compare bin location of theoretical vs actual
    if math.floor(fund_bin) == freq_bin_theo:
        print("%s Frequency bin PASS" % test_in)
    else:
        print("%s Frequency bin FAIL" % test_in)
        failed_tests.append("%s failed frequency bin" % test_in)

    time.sleep(2)

    #Comparing fundamental amplitude of input vs actual
    if (vref - 0.1) < fund_amp < (vref + 0.1):
        print("%s Fundamental amplitude PASS" % test_in)
    else:
        print("%s Fundamental amplitude FAIL" % test_in)
        failed_tests.append("%s failed Fundamental amplitude" % test_in)

    time.sleep(2)

    #Get THD, SNR and SINAD
    parameters = sp.sin_params(voltage)
    snr = parameters[1]
    thd = parameters[2]
    sinad = parameters[3]
    enob = parameters[4]
    sfdr = parameters[5]
    floor = parameters[6]   

    snr_FS_lim = 55
    thd_FS_lim = -40
    sinad_FS_lim = 40
    enob_FS_lim = 7
    sfdr_FS_lim = 40
    floor_FS_lim = -81

    snr_ATT_lim = 43
    thd_ATT_lim = -35
    sinad_ATT_lim = 35
    enob_ATT_lim = 7
    sfdr_ATT_lim = 35
    floor_ATT_lim = -60

    if test_in = "FS test":
        snr_lim = snr_FS_lim
        thd_lim = snr_FS_lim
        sinad_lim = snr_FS_lim
        enob_lim = snr_FS_lim
        sfdr_lim = snr_FS_lim
        floor_lim = snr_FS_lim
    else:
        snr_lim = snr_ATT_lim
        thd_lim = snr_ATT_lim
        sinad_lim = snr_ATT_lim
        enob_lim = snr_ATT_lim
        sfdr_lim = snr_ATT_lim
        floor_lim = snr_ATT_lim

    #print("SNR = ", snr)
    if snr > snr_lim:
        print("%s SNR = %s PASS" % (test_in,snr))
    else:
        print("%s SNR = %s FAIL" % (test_in,snr))
        failed_tests.append("%s SNR fail" % test_in)
    sleep(1)

    #print("THD = ", thd)
    if thd < thd_lim:
        print("%s THD = %s PASS" % (test_in,thd))
    else:
        print("%s THD = %s FAIL" % (test_in,thd))
        failed_tests.append("%s THD fail" % test_in)
    sleep(1)
    
    #print("SINAD = ", sinad)
    if sinad > sinad_lim:
        print("%s SINAD = %s PASS" % (test_in,sinad))
    else:
        print("%s SINAD = %s FAIL" % (test_in,sinad))
        failed_tests.append("%s SINAD fail" % test_in)
    sleep(1)

    #print("ENOB = ", enob)
    if enob < enob_lim:
        print("%s ENOB = %s PASS" % (test_in,enob))
    else:
        print("%s ENOB = %s FAIL" % (test_in,enob))
        failed_tests.append("%s ENOB fail" % test_in)
    sleep(1)

    #print("SFDR = ", sfdr)
    if sfdr > sfdr_lim:
        print("%s SFDR = %s PASS" % (test_in,sfdr))
    else:
        print("%s SFDR = %s FAIL" % (test_in,sfdr))
        failed_tests.append("%s SFDR fail" % test_in)
    sleep(1)

    #print("FLOOR = ", floor)
    if floor > floor_lim:
        print("%s FLOOR = %s PASS" % (test_in,floor))
    else:
        print("%s FLOOR = %s FAIL" % (test_in,floor))
        failed_tests.append("%s FLOOR fail" % test_in)
    sleep(1)

    time.sleep(1)

def channel_tests(my_cn0579, test_type, x):
    csource_switch(my_cn0579, x, 1)                                                                 # Turns on current source for channel x
    volt_reading, libm2k_ctx = read_DC()                                                            # Read DC voltage of the input signal using the M2k voltmeter
    vshift = set_shift(volt_reading)                                                                # Compute for the Vshift
    siggen = adalm2k.main(sin_freq, sin_amp, sin_offset, sin_phase, libm2k_ctx)                     # Turns on M2k output
    set_DAC(vshift, x, my_cn0579)                                                                   # Set output of the DAC to corresponding digital code of the Vshift
    fft_test(my_cn0579, test_type)                                                                  # Compute sinparams
    set_DAC(0, x, my_cn0579)                                                                        # Set output of the DAC to 0
    adalm2k.m2k_close(libm2k_ctx,siggen)                                                            # Turn off M2k for channel x
    csource_switch(my_cn0579, x, 0)                                                                 # Turn off current source for channel x                                                               
    volt_reading, libm2k_ctx = read_DC()                                                            # Read DC voltage of the input signal using the M2k voltmeter
    adalm2k.m2k_close(libm2k_ctx,siggen)                                                            # Turn off M2k for channel x
    return 

def main(my_ip):
    print("CN0579 Production Test \nTest script starting....")

    check_input()
    s_num = get_serial()

    input("Insert test jig to CN0579 according to test procedure....Press enter to continue:")
    my_cn0579 = setup_579(my_ip)

    for x in range(0,4):
        input("Starting FS test for channel %s...Make sure switch is in FS mode. Press enter to continue" % x)
        channel_tests(my_cn0579, q = "FS test")
        time.sleep(2)
        input("Starting Attenuated test for channel %s...Make sure switch is in attenuated mode. Press enter to continue" % x)
        channel_tests(my_cn0579, q = "Attenuated test")
        time.sleep(2)
        print("Channel %s test done\n" % x)

    return 

#If test code is ran locally in FPGA, my_ip is just the localhost. If control will be through a Windows machine/external, need to get IP address of the connected setup through LAN.
if __name__ == '__main__':
    start = time.time()
    print("ADI packages import done")
    hardcoded_ip = 'ip:analog.local'
    my_ip = sys.argv[2] if len(sys.argv) >= 3 else hardcoded_ip
    print("\nConnecting with CN0579 context at %s" % (my_ip))

    while (1):
        main(my_ip)
        print('Production test DONE!!\n')
        print("Test took " + str(time.time() - start) + " seconds.")

         #Check if board has passed or failed
        if len(failed_tests) == 0:
            print("Board PASSED!!!")
        else:
            print("Board FAILED the following tests:")
            for failure in failed_tests:
                print(failure)
            print("\nNote failures and set aside for debug.")
        
        #Prompt user to shutdown, repeat test or quit script
        x = input("Type \'s\' to shut down, \'a\' to test again, or \'q\'to quit:  ")
        if (x == 's'):
            if os.name == "posix":
                os.system("sudo shutdown -h now")
            else:
                print("Sorry, can only shut down system when running locally on DE-10\n")
                break
        elif (x == 'q'):
            exit(0)
        #Any other character than 'q' and 's' will trigger test again
        else:
            time.sleep(1)