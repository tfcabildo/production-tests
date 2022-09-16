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
from time import sleep

#EEPROM Path
eeprom_dir ="/sys/devices/soc0/fpga-axi@0/41620000.i2c/i2c-1/1-0050/eeprom"

#EEPROM Bin file in /home/analog
eeprom_bin ="CN0577FRU.bin"

#Path where eeprom_bin is located
bin_dir = "/home/analog"

#This function is to check if command line input is correct. Only one argument is needed (serial number of board being tested). If input is more than one argument, test code will exit.
def check_input():
    #Total arguments
    n = len(sys.argv)
    if n != 2:
         sys.exit('\nIncorrect syntax! \nExample: python cn0577_prod_test.py 202205100001\n')
    return

#This function gets the serial number of the board from the command line arguments and print it.
def get_serial():
    print("\nSetting up serial number....")
    sn = sys.argv[1]

    #Checking if serial number is valid
    if len(sn) == 10 and sn.isdigit():
        print ("\nSerial number:", int(sn))
    else:
        sys.exit('\nIncorrect serial number! Must be 10 digits.\nExample: 202205100001\n')
    
    return sn

#This function writes the bin file to CN0577 EEPROM and changes the default serial number based on the user input. It uses the FMC FRU utility.
def eeprom_dump(x):
    res1 = ""
    res2 = ""

    #Change directory to bin_dir path
    os.system("cd %s" % (bin_dir))

    #Set serial number from command line argument. Returns 0 if successful
    res1 = os.system("fru-dump -i %s -o %s -s %s" % (eeprom_bin, eeprom_dir, x))

    #Dump FRU Board Information
    res2 = os.system("fru-dump -i %s -o %s -b" % (eeprom_bin, eeprom_dir))
    #print('\n%s' % (res2))

    #Failed writing to eeprom (res1 = 1)
    if (res1):
        print("Writing bin file to CN0577's eeprom has failed")
        sys.exit('\nDumping of bin file to EEPROM failed\n')

    return res2

#This function contains the main test procedure of checking the ADC parameters such as THD, SNR, etc. This will return a 0 or 1 to reflect if board has passed or failed.
def prod_test():
    res1 = ''
    #Insert technical test here: SNR, THD etc.
    #Everytime a parameter is beyond the limit, append the 'failed_test' array

    #Return res1 as 1 or 0 for PASS or FAIL respectively
    return res1

def main():
    failed_tests = []

    #Main test proper
    print("CN0577 Production Test \nTest script starting....")
    check_input()
    s_num = get_serial()
    ret = eeprom_dump(s_num)
    print (ret)
    print("\nRunning test. Please wait...")
    ret = prod_test()

    #Check if board has passed or failed
    if ret == 1 and len(failed_tests) == 0:
        print("\nBoard PASSED!!!")
    else:
        print("Board FAILED the following tests:")
        for failure in failed_tests:
            print(failure)
        print("Note failures and set aside for debug.")

if __name__ == '__main__':
    #If test code is ran locally in FPGA, my_ip is just the localhost. If control will be through a Windows machine/external, need to get IP address of the connected setup through LAN.
    #hardcoded_ip = 'ip:localhost'
    #my_ip = sys.argv[2] if len(sys.argv) >= 3 else hardcoded_ip
    my_ip = "TrishaCabildo"
    print("\nConnecting with CN0577 context at %s" % (my_ip))

    main()
    print('\nTest script has finished.\n')
    exit(0)