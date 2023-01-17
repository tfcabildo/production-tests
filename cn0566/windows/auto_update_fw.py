import os
import shutil
from time import sleep
import paramiko
 
# Source path
source_fw = r"C:\Users\tcabildo\Downloads\FW\plutosdr-fw-v0.34.zip"
source_frm = r"C:\Users\tcabildo\Downloads\FW\pluto.frm"
 
# Destination path
destination = r"D:/"
 
#SSH Connection Parameters 
target_host = '192.168.2.1'
rt = 'root'
pw = 'analog'
target_port = 22

# Copy the content of source to destination
def copy_file(src1, dest1, fn):
    dest = shutil.copy(src1, dest1)
    print("%s copy done!" % fn)
    return dest

# Eject PlutoSDR Drive to PC
def eject():
    sleep(2)
    os.system('powershell $driveEject = New-Object -comObject Shell.Application; $driveEject.Namespace(17).ParseName("""D:""").InvokeVerb("""Eject""")')

# List files and directories in "/home / User / Desktop" and # Print path of newly created file
def print_info(dest2, fn):
    print("After copying file: %s" % os.listdir(destination))
    print("Destination path: %s \n" % dest2)

def test_flow(src2, fn):
    d = copy_file(src2,destination,fn)
    sleep(5)
    eject()
    sleep(58)
    print_info(d,fn)

def create_client():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh_client

def client_connect(ssh_client):
    ssh_client.connect(hostname = target_host, port = target_port, username=rt, password=pw)

def do_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    #print ("STDOUT:%s\nSTDERR:%s\n" %( stdout.read(), stderr.read() ))
    print ("STDOUT:%s" %( stdout.read() ))
    sleep(0.5)

def print_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    #print ("STDOUT:%s\nSTDERR:%s\n" %( stdout.read(), stderr.read() ))
    print ("STDOUT:%s" %( stdout.read() ))
    sleep(0.5)

def write_to_pluto(s1):
    do_command('fw_setenv attr_name compatible', s1)
    do_command('fw_setenv attr_val ad9361', s1)
    do_command('fw_setenv compatible ad9361', s1)
    do_command('fw_setenv mode 2r2t', s1)
    sleep(0.2)
    do_command('reboot', s1)
    sleep(0.5)
    s1.close()
    print("\n")

def read_attributes(s2):
    sleep(2)
    print_command('fw_printenv attr_name', s2)
    print_command('fw_printenv attr_val', s2)
    print_command('fw_printenv compatible', s2)
    print_command('fw_printenv mode', s2)
    print("\n")

def main(my_ip):
    test_flow(source_fw, fn="Pluto.zip")
    sleep(2)
    test_flow(source_frm, fn="pluto.frm")

    s1 = create_client()
    client_connect(s1)
    write_to_pluto(s1)

    sleep (13)

    s2 = create_client()
    client_connect(s2)
    read_attributes()

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main(my_ip)