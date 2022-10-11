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
import math
from adi import ltc2387
import libm2k  
import sin_params as sp
import m2k_siggen as sig_gen

#EEPROM Path
eeprom_dir ="/sys/devices/soc0/fpga-axi@0/41620000.i2c/i2c-1/1-0050/eeprom"

#EEPROM Bin file in /home/analog
eeprom_bin ="CN0577FRU.bin"

#Path where eeprom_bin is located
bin_dir = "/home/analog"

#Failed test array
failed_tests = []

sin_offset = 2.048              #DC offset of input signal (LTC2387 takes 0 to 4.096V)
sin_amp = 2.048                 #Amplitude of the differential input signal (Vpp / 2)
sin_phase = 180                 #Phase for the differential input
sin_freq = 20000                #20kHz input signal
n_samples = 256000              #Number of samples taken
sampling_freq = 10000000        #Master clock @120 MHz (f_sampling = master_clock / 12)
vref = 4.096                    #From REFBUF pin of LTC2387

#Window type for FFT
BLACKMAN_HARRIS_92 = 0x30
def_window_type = BLACKMAN_HARRIS_92

#This function is to check if command line input is correct. Only one argument is needed (serial number of board being tested). If input is more than one argument, test code will exit.
def check_input():
    n = len(sys.argv)                   # Number of total arguments on command line
    if n != 2:
         sys.exit('\nIncorrect syntax! \nExample: python cn0577_prod_test.py 202205100001\n')
    return

#This function gets the serial number of the board from the command line arguments and print it.
def get_serial():
    print("\nSetting up serial number....")
    sn = sys.argv[1]

    #Checking if serial number is valid
    if len(sn) == 10 and sn.isdigit():
        print ("Serial number:", int(sn))
    else:
        sys.exit('\nIncorrect serial number! Must be 10 digits.\nExample: 202205100001\n')
    
    return sn

#This function writes the bin file to CN0577 EEPROM and changes the default serial number based on the user input. It uses the FMC FRU utility.
def eeprom_dump(x):
    res1 = ''

    #Change directory to bin_dir path
    os.system("cd %s" % (bin_dir))

    #Set serial number from command line argument. Returns 0 if successful
    res1 = os.system("fru-dump -i %s -o %s -s %s" % (eeprom_bin, eeprom_dir, x))
    print('\n%s' % (res1))

    #Dump FRU Board Information
    #res2 = os.system("fru-dump -i %s -o %s -b" % (eeprom_bin, eeprom_dir))
    #print('\n%s' % (res2))

    #Failed writing to eeprom (res1 = 1)
    if (res1):
        sys.exit('Dumping of bin file to eeprom FAILED\n')

#This function gets the rms noise with the inputs to the ADC shorted to ground
def get_noise(shorted_input_data):
    noise = shorted_input_data * vref * 2 / (2 ** 18)               #Convert output digital code to voltage
    measured_noise = np.std(noise)
    print("Measured Noise: ", measured_noise) 

    if measured_noise < 0.4:
        print("RMS noise test PASS")
    else:
        print("RMS noise test FAIL")
        failed_tests.append("Failed rms noise test")

    input("Remove connections to input. Press any key to continue")

#This function sets up the ADC
def setup_adc(my_ip):
    my_adc = adi.ltc2387(uri=my_ip)
    my_adc.rx_buffer_size = n_samples
    my_adc.sampling_frequency = sampling_freq

    data = my_adc.rx()
    time.sleep(2)
    get_noise(data)

    return my_adc

#This function takes the fft and checks the ADC parameters such as frequency bin, fundamental amplitude, THD, SNR and SINAD if within limits
def sinparam_test(voltage,test_in):
    #windowed_fft_mag function takes in the analog data out of the ADC with its DC component. It removes the DC component within the function, thus 'voltage' is used
    fft_data = sp.windowed_fft_mag(voltage,window_type=BLACKMAN_HARRIS_92)
    fund_amp, fund_bin = sp.get_max(fft_data)

    f_base = sampling_freq/n_samples
    freq_bin_theo = math.floor(sin_freq / f_base)

    #Compare bin location of theoretical vs actual
    if math.floor(fund_bin) == freq_bin_theo:
        print("%s Frequency bin PASS" % test_in)
    else:
        print("%s Frequency bin FAIL" % test_in)
        failed_tests.append("%s failed frequency bin" % test_in)

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

    print("SNR = ", snr)
    if snr > 43:
        print("%s SNR PASS" % test_in)
    else:
        print("%s SNR fail" % test_in)
        failed_tests.append("%s failed SNR" % test_in)
    
    print("THD = ", thd)
    if thd < -45:
        print("%s THD PASS" % test_in)
    else:
        print("%s THD fail" % test_in)
        failed_tests.append("%s failed THD" % test_in)
    
    print("SINAD = ", sinad)
    if sinad > 42:
        print("%s SINAD PASS" % test_in)
    else:
        print("%s SINAD fail" % test_in)
        failed_tests.append("%s failed SINAD" % test_in)

    time.sleep(2)

#This function extracts the DC component of the output and checks if it is within limits. After, it calls the sinparam_test function.
def fft_test(sn,my_ip,my_adc,test_in):
    ser_no = sn
    data = my_adc.rx()

    x = np.arange(0, len(data))
    voltage = data * vref / (2 ** 17)                   # Since LTC2387 is using bipolar operation and inputs are > 0, total number of levels = 2^ (N-1)
    dc = np.average(voltage)                            # Extract DC component
    if (sin_offset - 0.1) < dc < (sin_offset + 0.1):    # Limits based on LTC2387 datasheet Vcm limits
        print("DC offset PASS")
    else:
        print("DC offset FAIL")
        failed_tests.append("Failed DC offset test")
    ac = voltage - dc                                   # Extract AC component

    sinparam_test(voltage,test_in)

def main(my_ip):
    print("CN0577 Production Test \nTest script starting....")

    #Checking input, getting serial number and writing SN to eeprom
    check_input()
    s_num = get_serial()
    eeprom_dump(s_num)
    
    #RMS Noise Test
    print("\nShort the input to ground")
    adc_info = setup_adc(my_ip)

    #Setup M2k to output differential input to DUT
    input("Connect provided test jig to input of DUT. Press any key to continue...")
    libm2k_ctx,siggen = sig_gen.main(sin_freq, sin_amp, sin_offset, sin_phase)

    #Full scale test
    input("Please switch on S1 and S2 on test jig. Full scale test starting. Press any key to continue..")
    fft_test(s_num,my_ip,adc_info,q="FS input")

    #Attenuated scale test
    input("Switch on S3 and S4 on test jig. Attenuated test starting. Press any key to continue..")
    fft_test(s_num,my_ip,adc_info,q="Attenuated input")

    return libm2k_ctx,siggen

#If test code is ran locally in FPGA, my_ip is just the localhost. If control will be through a Windows machine/external, need to get IP address of the connected setup through LAN.
if __name__ == '__main__':
    print("ADI packages import done")
    hardcoded_ip = 'ip:localhost'
    my_ip = sys.argv[2] if len(sys.argv) >= 3 else hardcoded_ip
    print("\nConnecting with CN0577 context at %s" % (my_ip))

    while (1):
        ctx,siggen = main(my_ip)
        print('Test DONE!!\n')
        sig_gen.m2k_close(ctx, siggen)  #Close m2k
        
        #Check if board has passed or failed
        if len(failed_tests) == 0:
            print("\nBoard PASSED!!!")
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
                print("Sorry, can only shut down system when running locally on Zedboard\n")
                break
        elif (x == 'q'):
            exit(0)
        #Any other character than 'q' and 's' will trigger test again
        else:
            time.sleep(1)
    