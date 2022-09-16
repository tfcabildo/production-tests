from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
from subprocess import call
import ctypes
import sys
import os, glob
import shutil 
import time
from datetime import datetime, timedelta
from verify_results import verify_iperf
EEPROM_FD="/sys/devices/soc0/fpga-axi@0/41600000.i2c/i2c-0/i2c-7/7-0050/eeprom"
EEPROM_BIN="CN0506FRU.bin"
fname="results.json"
tx_min=91.0
rx_min=91.0
interface0="eth0"
interface1="eth1"
ip0="192.168.1.6"
ip1="192.168.1.7"
gw=ip0
home="/home/analog"
sim=False
class App(QWidget):
    def __init__(self):
        super(App,self).__init__()
        self.title = 'CN0506 Production Test'
        self.testReminderMessageboxTitle="CN0506 Test Reminder"
        self.testReminderMessageBoxMessage='Please ensure that ethernet cable is connected to the\nCN0506 ports and both DS2 and DS4 LEDs are on\nbefore clicking OK.'
        self.serialNumberInputBoxTitle="Board Serial Number"
        self.serialNumberInputBoxMessage="Enter Serial Number:"
        self.testSuccessMessageBoxTitle="Test Success!"
        self.testSuccessMessageBoxMessage="Board with Serial#: {}\nAll tests PASSED - Ship it"
        self.testFailMessageBoxTitle="Test Failure"
        self.testFailMessageBoxMessage="Board Test Failed!\nBoard with Serial#:{}"
        self.errorNum=0
        self.errorMessage=""
        self.testState=0
        self.showSetupReminder()
        do_test=True
        if(not sim):
            while do_test:
                self.serialNumber=self.getSerialNumber()
                print(self.serialNumber)
                print("Running test. Please wait...")
                ret=self.test()
                do_test=False
                if ret!=0:
                    ans = QMessageBox.question(self,'Retest', "Re-run the test?", QMessageBox.Yes | QMessageBox.No)
                    if ans==QMessageBox.Yes:
                        print("Rerunning test. Please wait...")
                        do_test=True
        else:
            self.showSuccess(self.serialNumber)
            self.showFail(self.serialNumber)
            ans = QMessageBox.question(self,'Retest', "Re-run the test?", QMessageBox.Yes | QMessageBox.No)
        sys.exit()
        
 
    def test(self):

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        # Remove namespace interface
        print("Removing previous namespaces")
        ret=call(["../cn0506tool.sh","remove_ns_interfaces", interface0, interface1])
        # Setup namespace interface
        print("Setting up network namespaces")
        ret=call(["../cn0506tool.sh","setup_ns_interfaces", interface0, interface1, ip0, ip1, gw])
        time.sleep(3)
        #Check links
        test0A=call(["../cn0506tool.sh","check_link",interface0])
        print("PHY A LINK CHECK=" + "OK" if test0A==0 else "failed")
        test0B=call(["../cn0506tool.sh","check_link",interface1])
        print("PHY B LINK CHECK=" + "OK" if test0A==0 else "failed")
        if ((test0A==0) and (test0B==0)): #Both are connected
            # Run server
            print("Running iperf server")
            ret=call(["../cn0506tool.sh","run_ns_iperf_server", ip1])
            # Run Client
            print("Running iperf client")
            ret=call(["../cn0506tool.sh","run_ns_iperf_client", ip0, ip1, fname])
            # Parse and check result
            print("Test Throughput... Please wait.")
            test1=verify_iperf(fname=fname,tx_min=tx_min,rx_min=rx_min)
            # Test Data integrity
            print("Test Data integrity... Please wait.")
            test2=call(["../cn0506tool.sh","test_data_integrity", ip0, ip1, home,"100M"])
            # Remove namespace interface
            print("Finishing test. Removing previous namespaces...")
            ret=call(["../cn0506tool.sh","remove_ns_interfaces", interface0, interface1])
            
            print("Test1=" + "OK" if test1==0 else "failed")
            print("Test2=" + "OK" if test2==0 else "failed")
            if ((test1==0) and (test2==0)): #PASS
                self.showSuccess(self.serialNumber)
                ret=0
            else: #FAIL
                self.showFail(self.serialNumber)
                ret=1
        else: #FAIL
            self.showFail(self.serialNumber)
            ret=1
        QApplication.restoreOverrideCursor()
        return ret

    def showSetupReminder(self):
        QMessageBox.information(self, self.testReminderMessageboxTitle, self.testReminderMessageBoxMessage, QMessageBox.Ok,)

    def getSerialNumber(self):
        sn=""
        notOK=True
        while notOK:
            sn, okPressed = QInputDialog.getText(self, self.serialNumberInputBoxTitle,self.serialNumberInputBoxMessage, QLineEdit.Normal, "")
            if okPressed and sn != '':
                notOK=False
                dateNow=datetime.now()
                date96=datetime(1996,1,1)
                dateDiff=dateNow-date96
                dateDiffMinutes=round(dateDiff.total_seconds()/60)
                print("Manufacturing Date:", round(dateDiff.total_seconds()/60))
                # Write FRU to EEPROM
                if(not sim):
                    ret=call(["fru-dump","-i",EEPROM_BIN,"-s",str(sn),"-d",str(dateDiffMinutes), "-o",EEPROM_FD])
                    if(ret):
                        #EEPROM not writable. Fail.
                        self.showFail(self.serialNumber)
                        exit(1)
            elif not okPressed:
                sys.exit()
        return sn

    def showSuccess(self,serialNumber):
        QMessageBox.information(self, self.testSuccessMessageBoxTitle, self.testSuccessMessageBoxMessage.format(serialNumber), QMessageBox.Ok)
    def showFail(self,serialNumber):
        QMessageBox.critical(self, self.testFailMessageBoxTitle, self.testFailMessageBoxMessage.format(serialNumber), QMessageBox.Ok)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
