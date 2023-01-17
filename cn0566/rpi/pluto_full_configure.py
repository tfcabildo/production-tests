import os
import sys
import subprocess
import shutil
from time import sleep
import paramiko
 
# Source path
source_fw = r"/home/analog/Desktop/plutosdr-fw-v0.35.zip"
source_frm = r"/home/analog/Desktop/pluto.frm"
 
# Destination path
destination = r"/media/analog/PlutoSDR"

#Password and path for ejecting drive
pw = 'analog'

#For SSH client
target_host = '192.168.2.1'
rt = 'root'
pw = 'analog'
target_port = 22

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

def client_connect(ssh_client):
    ssh_client.connect(hostname = target_host, port = target_port, username=rt, password=pw)

def do_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    print ("Done! : %s" %(a1))
    sleep(0.5)
    
def do_list(ssh_client):
    do_command('fw_setenv attr_name compatible', ssh_client)
    do_command('fw_setenv attr_val ad9361', ssh_client)
    do_command('fw_setenv compatible ad9361', ssh_client)
    do_command('fw_setenv mode 2r2t', ssh_client)
    sleep(0.2)
    do_command('reboot', ssh_client)
    
def print_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    a1 = stdout.read().decode('ascii')
    print ("%s" % (a1), end='')
    sleep(0.5)

def task_list(s):
    print_command('fw_printenv attr_name', s)
    print_command('fw_printenv attr_val', s)
    print_command('fw_printenv compatible', s)
    print_command('fw_printenv mode', s)

def pluto_checker(path):
    isExist = os.path.exists(path)
    print("Checking if PlutoSDR exists...", end='')
    while (isExist == False):
        sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nPlutoSDR found!\n")
    sleep(2)

def wait_eject(path):
    isExist = os.path.exists(path)
    print("Ejecting", end='')
    while (isExist == False):
        sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nPluto detected again!\n")
    sleep(2)

def test_flow(src2, path, fn):
    d = copy_file(src2,destination,fn)
    sleep(3)
    eject(path)
    eject_checker(path)
    print_info(d,fn)

def pluto_firmware():
    path = path_finder()
    test_flow(source_fw, path, fn="Pluto firmware.zip")
    sleep(3)
    test_flow(source_frm, path, fn="Pluto.frm")
    sleep(3)

def ssh_write():
    path = path_finder()
    pluto_checker(path)
    
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client_connect(ssh_client)
        print("Connected succesfully! Writing attributes...")
        sleep(1)
        do_list(ssh_client)
        sleep(2)
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
    sleep(1)
    
    try:
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client_connect(s)
        print("Connected succesfully! Reading attributes...")
        sleep(1)
        task_list(s)
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        print("Could not connect to SSH host: %s" % (target_host))
    except paramiko.ssh_exception.AuthenticationException as e:
        print("SSH authentication error!")
    except:
        print("Error!!")

def main(my_ip):
    pluto_firmware()
    ssh_write()
    sleep(6)
    ssh_read()
    print("\nPluto configuration done!")

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main(my_ip)
