import os
from time import sleep
import paramiko

target_host = '192.168.2.1'
rt = 'root'
pw = 'analog'
target_port = 22

def client_connect(ssh_client):
    ssh_client.connect(hostname = target_host, port = target_port, username=rt, password=pw)

def do_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    #print ("STDOUT:%s\nSTDERR:%s\n" %( stdout.read(), stderr.read() ))
    print ("STDOUT:%s" %( stdout.read() ))
    sleep(0.5)

def print_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    print ("STDOUT:%s\nSTDERR:%s\n" %( stdout.read(), stderr.read() ))

def main():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_connect(ssh_client)

    do_command('fw_setenv attr_name compatible', ssh_client)
    do_command('fw_setenv attr_val ad9361', ssh_client)
    do_command('fw_setenv compatible ad9361', ssh_client)
    do_command('fw_setenv mode 2r2t', ssh_client)
    sleep(0.2)
    do_command('reboot', ssh_client)
    sleep(0.5)
    ssh_client.close()

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main()