import os
import sys
import subprocess
import shutil
from time import sleep
 
# Source path
source_fw = r"/home/analog/Desktop/plutosdr-fw-v0.35.zip"
source_frm = r"/home/analog/Desktop/pluto.frm"
 
# Destination path
destination = r"/media/analog/PlutoSDR"

#Password and path for ejecting drive
pw = 'analog'
#pluto_path = '/dev/sdb1'
 
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
        sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nFlash done!")
    sleep(2)

# List files and directories in "/home / User / Desktop" and # Print path of newly created file
def print_info(dest2, fn):
    items = os.listdir(destination)
    print("After copying file: %s" % (items))
    print("Destination path: %s \n" % dest2)

def test_flow(src2, path, fn):
    d = copy_file(src2,destination,fn)
    sleep(3)
    eject(path)
    eject_checker(path)
    print_info(d,fn)

def main(my_ip):
    path = path_finder()
    test_flow(source_fw, path, fn="Pluto firmware.zip")
    sleep(3)
    test_flow(source_frm, path, fn="Pluto.frm")

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main(my_ip)