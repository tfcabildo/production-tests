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

# Configure Pluto with correct firmware and setenv attributes
# Read all board voltages, current, ambient temperature, and compare against limits

# Run gain calibration, verify signal levels are within some fairly wide limits,
# and that the spread between minimum and maximum gains is within TBD limits.

# Run phase calibration, verify that phase corretionn values are within TBD degrees.

# Also consider having a minimal board-level test just to verify basic functionality,
# with wider test limits. 

from adi import CN0566
from adi import ad9361
import os
import sys
import subprocess
import shutil
import time
import paramiko
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from cn0566_functions import (
    calculate_plot,
    channel_calibration,
    gain_calibration,
    get_signal_levels,
    load_hb100_cal,
    phase_calibration,
)

start = time.time()

# Source and destination path
source_fw = r"/home/analog/Desktop/plutosdr-fw-v0.35.zip"
source_frm = r"/home/analog/Desktop/pluto.frm"
destination = r"/media/analog/PlutoSDR"

# For SSH client
target_host = '192.168.2.1'
rt = 'root'
pw = 'analog'
target_port = 22
pw = 'analog'

# Board limits and failure array
failures = []
#                    temp   1.8V 3.0    3.3   4.5   15?   USB   curr. Vtune
monitor_hi_limits = [60.0, 1.85, 3.015, 3.45, 4.75, 16.0, 5.25, 1.6, 14.0]
monitor_lo_limts = [20.0, 1.75, 2.850, 3.15, 4.25, 13.0, 4.75, 1.2, 1.0]
monitor_ch_names = [
    "Board temperature: ",
    "1.8V supply: ",
    "3.0V supply: ",
    "3.3V supply: ",
    "4.5V supply: ",
    "Vtune amp supply: ",
    "USB C input supply: ",
    "Board current: ",
    "VTune: ",
]

# Calibration limits
channel_cal_limits = 10.0  # Fail if channels mismatched by more than 10 dB
gain_cal_limits = (
    0.50  # Fail if any channel is less than 60% of the highest gain channel
)
phase_cal_limits = [90.0, 90.0, 90.0, 120.0, 90.0, 90.0, 90.0]


def path_finder():
    command = 'findmnt --output=source /media/analog/PlutoSDR'
    a = subprocess.run(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    a1 = a.stdout.decode('ascii')
    path = a1[7:16] #Remove some characters: 'source' and '\n'
    print("PlutoSDR path at %s" % (path))
    return str(path)
 
# Copy the file from source to destination
def copy_file(src1, dest1, fn):
    try:
        dest = shutil.copy(src1, dest1)
        print("%s copied successfully!" % fn)
        return dest
    except shutil.SameFileError:
        print("Source and destination represents the same file.")
    except PermissionError:
        print("Permission denied!")
    except:
        print("Error occurred while copying file.")

# Eject PlutoSDR Drive to PC
def eject(path):
    p = os.system('echo %s|sudo -S sudo eject %s' % (pw,path))
    q = os.path.exists(path)
    if (p == 0 and q == False):
        print("Pluto ejecting...")
    elif (p == 0 and q == True):
        eject()
    else:
        sys.exit("Failed ejecting Pluto!")

def eject_checker(path):
    isExist = os.path.exists(path)
    print("Flashing", end='')
    while (isExist == False):
        time.sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nFlash done!")
    time.sleep(2)

# List files and directories in "/home / User / Desktop" and # Print path of newly created file
def print_info(dest2, fn):
    items = os.listdir(destination)
    print("After copying file: %s" % (items))
    print("Destination path: %s \n" % dest2)

def client_connect(ssh_client):
    ssh_client.connect(hostname = target_host, port = target_port, username=rt, password=pw)

def do_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    print ("Done! : %s" %(a1))
    time.sleep(0.5)
    
def do_list(ssh_client):
    do_command('fw_setenv attr_name compatible', ssh_client)
    do_command('fw_setenv attr_val ad9361', ssh_client)
    do_command('fw_setenv compatible ad9361', ssh_client)
    do_command('fw_setenv mode 2r2t', ssh_client)
    time.sleep(0.2)
    do_command('reboot', ssh_client)
    
def print_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    a1 = stdout.read().decode('ascii')
    print ("%s" % (a1), end='')
    time.sleep(0.5)

def task_list(s):
    print_command('fw_printenv attr_name', s)
    print_command('fw_printenv attr_val', s)
    print_command('fw_printenv compatible', s)
    print_command('fw_printenv mode', s)

def pluto_checker(path):
    isExist = os.path.exists(path)
    print("Checking if PlutoSDR exists...", end='')
    while (isExist == False):
        time.sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nPlutoSDR found!\n")
    time.sleep(2)

def wait_eject(path):
    isExist = os.path.exists(path)
    print("Ejecting", end='')
    while (isExist == False):
        time.sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nPluto detected again!\n")
    time.sleep(2)

def test_flow(src2, path, fn):
    d = copy_file(src2,destination,fn)
    time.sleep(3)
    eject(path)
    eject_checker(path)
    print_info(d,fn)

def pluto_firmware():
    path = path_finder()
    test_flow(source_fw, path, fn="Pluto firmware.zip")
    time.sleep(3)
    test_flow(source_frm, path, fn="Pluto.frm")
    time.sleep(3)

def ssh_write():
    path = path_finder()
    pluto_checker(path)
    
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client_connect(ssh_client)
        print("Connected succesfully! Writing attributes...")
        time.sleep(1)
        do_list(ssh_client)
        time.sleep(2)
        ssh_client.close()
        wait_eject(path)
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        print("Could not connect to SSH host: %s" % (target_host))
    except paramiko.ssh_exception.AuthenticationException as e:
        print("SSH authentication error!")
    except:
        print("Error!")

def ssh_read():
    path = path_finder()
    pluto_checker(path)
    time.sleep(1)
    
    try:
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client_connect(s)
        print("Connected succesfully! Reading attributes...")
        time.sleep(1)
        task_list(s)
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        print("Could not connect to SSH host: %s" % (target_host))
    except paramiko.ssh_exception.AuthenticationException as e:
        print("SSH authentication error!")
    except:
        print("Error!!")

def phaser_main_test(rpi_ip, sdr_ip):
    try:
        x = my_sdr.uri
        print("Pluto already connected")
    except NameError:
        print("Pluto not connected, connecting...")
        from adi import ad9361

    my_sdr = ad9361(uri=sdr_ip)

    time.sleep(0.5)

    try:
        x = my_phaser.uri
        print("cn0566 already connected")
    except NameError:
        print("cn0566 not connected, connecting...")
        from adi.cn0566 import CN0566
        my_phaser = CN0566(uri=rpi_ip, sdr=my_sdr)

    my_phaser.configure(device_mode="rx")  
    use_tx = True

    my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
    my_sdr._rxadc.set_kernel_buffers_count(
    1
    )  # Super important - don't want to have to flush stale buffers
    rx = my_sdr._ctrl.find_channel("voltage0")
    rx.attrs["quadrature_tracking_en"].value = "1"  # set to '1' to enable quadrature tracking
    my_sdr.sample_rate = int(30000000)  # Sampling rate
    my_sdr.rx_buffer_size = int(4 * 256)
    my_sdr.rx_rf_bandwidth = int(10e6)

    # We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
    my_sdr.gain_control_mode_chan0 = "manual"
    my_sdr.gain_control_mode_chan1 = "manual"
    my_sdr.rx_hardwaregain_chan0 = 12
    my_sdr.rx_hardwaregain_chan1 = 12
    my_sdr.rx_lo = int(2.2e9)  # 4495000000  # Recieve Freq
    print ("Loading filter")
    my_sdr.filter = os.getcwd() + "/LTE20_MHz.ftr"  # MWT: Using this for now, may not be necessary.
    rx_buffer_size = int(4 * 256)
    my_sdr.rx_buffer_size = rx_buffer_size
    my_sdr.tx_cyclic_buffer = True
    my_sdr.tx_buffer_size = int(2 ** 16)

    if use_tx is True:
        # To disable rx, set attenuation to a high value and set frequency far from rx.
        my_sdr.tx_hardwaregain_chan0 = int(
            -88
        )  # this is a negative number between 0 and -88
        my_sdr.tx_hardwaregain_chan1 = int(-3)
        my_sdr.tx_lo = int(2.2e9)
    else:
        # To disable rx, set attenuation to a high value and set frequency far from rx.
        my_sdr.tx_hardwaregain_chan0 = int(
            -88
        )  # this is a negative number between 0 and -88
        my_sdr.tx_hardwaregain_chan1 = int(-88)
        my_sdr.tx_lo = int(1.0e9)
    
    print("Using TX output closest to tripod mount, 10.525 GHz for production test.")
    my_phaser.SignalFreq = 10.525e9

    my_sdr.dds_single_tone(
        int(0.5e6), 0.9, 1
    ) 

    #  Configure CN0566 parameters.
    #     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
    #     accessed through other methods.

    my_phaser.lo = int(my_phaser.SignalFreq) + my_sdr.rx_lo

    # MWT: Do NOT load in cal values during production test. That's what we're doing, after all :)
    # But running a second time with saved cal values may be useful in development.
    # my_phaser.load_gain_cal('gain_cal_val.pkl')
    # my_phaser.load_phase_cal('phase_cal_val.pkl')

    # Averages decide number of time samples are taken to plot and/or calibrate system. By default it is 1.
    my_phaser.Averages = 8


    print("Reading voltage monitor...")
    monitor_vals = my_phaser.read_monitor()

    for i in range(0, len(monitor_vals)):
        if not (monitor_lo_limts[i] <= monitor_vals[i] <= monitor_hi_limits[i]):
            print("Fails ", monitor_ch_names[i], ": ", monitor_vals[i])
            failures.append(
                "Monitor fails " + monitor_ch_names[i] + ": " + str(monitor_vals[i])
            )
        else:
            print("Passes ", monitor_ch_names[i], monitor_vals[i])

    print(
        "Calibrating SDR channel mismatch, gain and phase - place antenna at mechanical\
            boresight in front of the array, then press enter...\n\n"
    )

    print("Getting signal levels...")
    sig_levels = get_signal_levels(my_phaser)
    print(sig_levels)
    if min(sig_levels) < 80.0:
        print("Low signal levels!! Double-check hardware setup, then re-run test.")
        sys.exit()

    print("\nCalibrating SDR channel mismatch, verbosely...")
    channel_calibration(my_phaser, verbose=True)

    print("\nCalibrating Gain, verbosely, then saving cal file...")
    gain_calibration(my_phaser, verbose=True)  # Start Gain Calibration

    print("\nCalibrating Phase, verbosely, then saving cal file...")
    phase_calibration(my_phaser, verbose=True)  # Start Phase Calibration

    print("Done calibration")

    for i in range(0, len(my_phaser.ccal)):
        if my_phaser.ccal[i] < channel_cal_limits:
            print("Channel cal failure on channel ", i, ", ", my_phaser.gcal[i])
            failures.append("Channel cal falure on channel " + str(i))

    for i in range(0, len(my_phaser.gcal)):
        if my_phaser.gcal[i] < gain_cal_limits:
            print("Gain cal failure on element ", i, ", ", my_phaser.gcal[i])
            failures.append("Gain cal falure on element " + str(i))

    for i in range(0, len(my_phaser.pcal) - 1):
        delta = my_phaser.pcal[i + 1] - my_phaser.pcal[i]
        if abs(delta) > phase_cal_limits[i]:
            print("Phase cal failure on elements ", i - 1, ", ", i, str(delta))
            failures.append(
                "Phase cal falure on elements "
                + str(i - 1)
                + ", "
                + str(i)
                + ", delta: "
                + str(delta)
            )

    return my_sdr, my_phaser

def debugger_plot(my_sdr, my_phaser):
    while do_plot == True:

        start_1 = time.time()
        my_phaser.set_beam_phase_diff(0.0)
        time.sleep(0.25)
        data = my_sdr.rx()
        data = my_sdr.rx()
        ch0 = data[0]
        ch1 = data[1]
        f, Pxx_den0 = signal.periodogram(
            ch0[1:-1], 30000000, "blackman", scaling="spectrum"
        )
        f, Pxx_den1 = signal.periodogram(
            ch1[1:-1], 30000000, "blackman", scaling="spectrum"
        )

        plt.figure(1)
        plt.clf()
        plt.plot(np.real(ch0), color="red")
        plt.plot(np.imag(ch0), color="blue")
        plt.plot(np.real(ch1), color="green")
        plt.plot(np.imag(ch1), color="black")
        np.real
        plt.xlabel("data point")
        plt.ylabel("output code")
        plt.draw()

        plt.figure(2)
        plt.clf()
        plt.semilogy(f, Pxx_den0)
        plt.semilogy(f, Pxx_den1)
        plt.ylim([1e-5, 1e6])
        plt.xlabel("frequency [Hz]")
        plt.ylabel("PSD [V**2/Hz]")
        plt.draw()

        # Plot the output based on experiment that you are performing
        print("Plotting...")

        plt.figure(3)
        plt.ion()
        #    plt.show()
        (
            gain,
            angle,
            delta,
            diff_error,
            beam_phase,
            xf,
            max_gain,
            PhaseValues,
        ) = calculate_plot(my_phaser)
        print("Sweeping took this many seconds: " + str(time.time() - start))
        #    gain,  = my_phaser.plot(plot_type="monopulse")
        plt.clf()
        plt.scatter(angle, gain, s=10)
        plt.scatter(angle, delta, s=10)
        plt.show()

        plt.pause(0.05)
        time.sleep(0.05)
        print("Total took this many seconds: " + str(time.time() - start_1))

        do_plot = False
        print("Exiting Loop")

def main(rpi_ip, sdr_ip):
    start = time.time()
    pluto_firmware()
    ssh_write()
    time.sleep(6)
    ssh_read()
    print("\nPluto configuration done!")

    my_sdr, my_phaser = phaser_main_test(rpi_ip, sdr_ip)
    print("Test took " + str(time.time() - start) + " seconds.")    

    return my_sdr, my_phaser
    
if __name__ == '__main__':
    if os.name == "nt":  # Assume running on Windows
        rpi_ip = "ip:phaser.local"  # IP address of the remote Raspberry Pi
        # sdr_ip = "ip:pluto.local"  # Pluto IP, with modified IP address or not
        sdr_ip = "ip:phaser.local:12345"  # Context Forwarding in libiio 0.24!
        print("Running on Windows, connecting to ", rpi_ip, " and ", sdr_ip)
    elif os.name == "posix":
        rpi_ip = "ip:localhost"  # Assume running locally on Raspberry Pi
        sdr_ip = "ip:192.168.2.1"  # Historical - assume default Pluto IP
        print("Running on Linux, connecting to ", rpi_ip, " and ", sdr_ip)
        print("Packages import done")
    else:
        print("Can't detect OS")

    #my_ip = 'ip:192.168.2.1'
    #print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    my_sdr, my_phaser = main(rpi_ip, sdr_ip)

    if len(failures) == 0:
        print("\nWooHoo! BOARD PASSES!!\n")
    else:
        print("\nD'oh! BOARD FAILS!\n")
        for failure in failures:
            print(failure)
        print("\n\n")

    ser_no = input("Please enter serial number of board, then press enter.\n")
    filename = str("results/CN0566_" + ser_no + "_" + time.asctime() + ".txt")
    filename = filename.replace(":", "-")
    filename = os.getcwd() + "/" + filename

    with open(filename, "w") as f:
        f.write("Phaser Test Results:\n")
        f.write("\nMonitor Readings:\n")
        f.write(str(monitor_vals))
        f.write("\nSignal Levels:\n")
        f.write(str(sig_levels))
        f.write("\nChannel Calibration:\n")
        f.write(str(my_phaser.ccal))
        f.write("\nGain Calibration:\n")
        f.write(str(my_phaser.gcal))
        f.write("\nPhase Calibration:\n")
        f.write(str(my_phaser.pcal))
        if len(failures) == 0:
            f.write("\nThis is a PASSING board!\n")
        else:
            f.write("\nThis is a FAILING board!\n")

    do_plot = (
        False  # Do a plot just for debug purposes. Suppress for actual production test.
    )
    debugger_plot(my_sdr, my_phaser)
