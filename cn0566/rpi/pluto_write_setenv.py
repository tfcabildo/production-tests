import os
from time import sleep
import paramiko
import subprocess

#For SSH client
target_host = '192.168.2.1'
rt = 'root'
pw = 'analog'
target_port = 22

#Password and path for ejecting drive
pw = 'analog'
#path = '/dev/sda1'

def path_finder():
    command = 'findmnt --output=source /media/analog/PlutoSDR'
    a = subprocess.run(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    a1 = a.stdout.decode('ascii')
    path = a1[7:16] #Remove some characters: 'source' and '\n'
    print("PlutoSDR path at %s" % (path))
    return str(path)

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

def pluto_checker(path):
    isExist = os.path.exists(path)
    print("Checking if PlutoSDR exists...", end='')
    while (isExist == False):
        sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nPlutoSDR found!\n")
    sleep(2)

def eject_checker(path):
    isExist = os.path.exists(path)
    print("Ejecting", end='')
    while (isExist == False):
        sleep(1)
        print(".", end='', sep='')
        isExist = os.path.exists(path)
    print("\nPluto detected again!\n")
    sleep(2)

def main():
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
        eject_checker(path)
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        print("Could not connect to SSH host: %s" % (target_host))
    except paramiko.ssh_exception.AuthenticationException as e:
        print("SSH authentication error!")
    except:
        print("Error!")

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main()