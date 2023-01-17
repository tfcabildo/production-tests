import os
import shutil
from time import sleep
 
# Source path
source_fw = r"C:\Users\tcabildo\Downloads\FW\plutosdr-fw-v0.34.zip"
source_frm = r"C:\Users\tcabildo\Downloads\FW\pluto.frm"
 
# Destination path
destination = r"D:/"
 
# Copy the content of source to destination
def copy_file(src1, dest1, fn):
    dest = shutil.copy(src1, dest1)
    print("%s copy done!" % fn)
    return dest

# Eject PlutoSDR Drive to PC
def eject():
    sleep(1)
    os.system('powershell $driveEject = New-Object -comObject Shell.Application; $driveEject.Namespace(17).ParseName("""D:""").InvokeVerb("""Eject""")')

# List files and directories in "/home / User / Desktop" and # Print path of newly created file
def print_info(dest2, fn):
    #print("%s copy done!" % fn)
    print("After copying file: %s" % os.listdir(destination))
    #print(os.listdir(destination))
    print("Destination path: %s \n" % dest2)

def test_flow(src2, fn):
    d = copy_file(src2,destination,fn)
    sleep(5)
    eject()
    sleep(58)
    print_info(d,fn)

def main(my_ip):
    test_flow(source_fw, fn="Pluto.zip")
    sleep(3)
    test_flow(source_frm, fn="pluto.frm")

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main(my_ip)