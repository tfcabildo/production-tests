import pluto_script
import pluto_ssh_read
import pluto_ssh_write
from time import sleep

my_ip = 'ip:192.168.2.1'

pluto_script.main(my_ip)
pluto_ssh_write.main()
sleep(13)
pluto_ssh_read.main()