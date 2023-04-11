#!/usr/bin/env python3
#  Must use Python 3
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

#Author : Trisha Cabildo

# Setup: This code is running locally on a Raspberry Pi + CN0508 

import sys
import time
import os
from time import sleep
import adi

# Channel scale factors
adc_scale = 0.000149011 #Vref=2.5; adc_scale=[2.5/(2^24)]
ldoU2_temp_scale = 1.0 # Degrees C/mV
ldoU3_temp_scale = 1.0 # Degrees C/mV
iout_scale = 0.005 # A/mV
vin_scale =  14.33/1000 # V/mV; vin_scale = 1+(20.0/1.5)
vout_scale =  10.52/1000 # V/mV; vout_sca;e = 1+(20.0/2.1)
ilim_pos_scale =  100.0/(2.5*1000) # Percent
vpot_pos_scale =  100.0/(2.5*1000) # Percent
ldoin_scale =  14.33/1000 # V/mV; vin_scale = 1+(20.0/1.5)

def dac_setter(mydac, setpoint, dac_scale, myadc):
    mydac.channel[0].raw = str(int(setpoint * 1000.0 / (11.0 *dac_scale)))
    time.sleep(0.1)
    vout = (float(myadc.channel[4].raw) * adc_scale) * vout_scale

    return vout

def dac_scale_setter(mydac):
    dac_scale = mydac.channel[0].scale # This is set by the device tree, it's not an actual measured value.
    print("DAC scale factor: " + str(dac_scale))
    
    return dac_scale

def adc_scale_setter(myadc):
    print("Setting scales to 0.000149011 (unity gain)...")
    for i in range(0, 8):
        myadc.channel[i].scale = adc_scale

    return

def device_connect(my_ip):
    try:
        myadc = adi.ad7124(uri=my_ip)
        mydac = adi.ad5686(uri=my_ip) # REMEMBER TO VERIFY POWERDOWN/UP BEHAVIOR
    except:
      print("No device found")
      sys.exit(0)

    return myadc, mydac

def main(my_ip):

    myadc, mydac = device_connect(my_ip)
    dac_scale = dac_scale_setter(mydac)

    print("setting up DAC, setting output to 0.0V...")
    dac_v = 0.0
    vout = dac_setter(mydac, dac_v, dac_scale, myadc)

    myadc.sample_rate = 9600
    print("ADC sample rate set at: 9600")

    adc_scale_setter(myadc)

    print("Reading all voltages...\n")

    ldoU2_temp_init = (float(myadc.channel[0].raw) * adc_scale) * ldoU2_temp_scale
    ldoU3_temp_init = (float(myadc.channel[1].raw) * adc_scale) * ldoU3_temp_scale
    iout = (float(myadc.channel[2].raw) * adc_scale) * iout_scale
    vin = (float(myadc.channel[3].raw) * adc_scale) * vin_scale
    vout = (float(myadc.channel[4].raw) * adc_scale) * vout_scale
    ilim_pos = (float(myadc.channel[5].raw) * adc_scale) * ilim_pos_scale
    vpot_pos = (float(myadc.channel[6].raw) * adc_scale) * vpot_pos_scale
    vldoin = (float(myadc.channel[7].raw) * adc_scale) * ldoin_scale

    print("Initial Board conditions:")
    print("U2 Temperature: " + str(ldoU2_temp_init) + " C")
    print("U3 Temperature: " + str(ldoU3_temp_init) + " C")
    print("Output Current: " + str(iout) + " A")
    print("Input Voltage: " + str(vin) + " V")
    print("Output Voltage: " + str(vout) + " V")
    print("ILIM pot position: " + str(ilim_pos) + " %")
    print("Vout pot position: " + str(vpot_pos) + " %")
    print("LDO input voltage: " + str(vldoin) + " %")

    # Setting output voltage to 10 volts....
    print("Setting output voltage to 10V... ")
    dac_v = 10.0
    vout = dac_setter(mydac, dac_v, dac_scale, myadc)
    print("10V output voltage: %.3f" % (vout) + " V")

    del myadc
    del mydac
    del adi

    return

if __name__ == '__main__':
    
    # This is running on RPi if hardcoded_ip is used. Add the board ip_address at the end of command line when calling out the code if remote access
    hardcoded_ip = 'ip:localhost'
    my_ip = sys.argv[1] if len(sys.argv) >= 2 else hardcoded_ip
    print("Connecting with CN0508 context at %s" % (my_ip))

    while(1):
        testdata = main(my_ip)
        x = input("Type \'s\' to shut down, \'a\' to test again, or \'q\'to quit:  ")
        if(x == 's'):
            if os.name == "posix":
                os.system("shutdown -h now")
            else:
                print("Sorry, can only shut down system when running locally on Raspberry Pi")
            break
        elif(x == 'q'):
            break
        else:
            sleep(0.5)
        # any other character tests again.