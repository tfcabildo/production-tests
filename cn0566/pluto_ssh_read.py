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
    print ("STDOUT:%s\nSTDERR:%s\n" %( stdout.read(), stderr.read() ))
    sleep(1)

def print_command(a1,ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command(a1)
    #print ("STDOUT:%s\nSTDERR:%s\n" %( stdout.read(), stderr.read() ))
    print ("STDOUT:%s" %( stdout.read() ))
    sleep(0.5)

def main():
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_connect(s)
    sleep(2)

    print_command('fw_printenv attr_name', s)
    print_command('fw_printenv attr_val', s)
    print_command('fw_printenv compatible', s)
    print_command('fw_printenv mode', s)

if __name__ == '__main__':
    print("\nPackages import done")
    my_ip = 'ip:192.168.2.1'
    print("Connecting with ADALM-Pluto context at %s\n" % (my_ip))

    main()