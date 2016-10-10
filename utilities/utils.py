import math
import time
import subprocess
import os,sys
import win32gui
import win32con
import win32com.client
import shelve
import shutil


class Unit(object):
    def _init_(self, target_ip):
        self.ip = target_ip
        
    def connect(self, target_ip = None):
        if target_ip is None:
            print "\nIP address is wrong.."
            sys.exit()
        else:
            self.ip = target_ip
            self.snmp_manager = mibs.create_manager(self.ip)

    def wait_until_awake(self, tov=5 * 60):
        cmd = "ping " + str(self.ip) + " -w 1000 -n 1"
        output = ""
        start_time = time.time()
    
        while "Lost = 0" not in output:
            try:
                output = subprocess.check_output(cmd.split())
            except:
                pass
            if time.time() > start_time + tov:
                raise RuntimeError("ping timed out\n" + cmd + "\n" + output)       

    def set_mib(self,parameter, value):
        #snmp_manager = mibs.create_manager(self.ip)
        try:
            return self.snmp_manager.set(parameter, value)
        except ValueError:
            raise ValueError("Failed settings parameter to SNMPB..")
        snmp_manager.close()

    def get_mib(self, parameter):
        #self.snmp_manager = mibs.create_manager(self.ip)
        try:
            return self.snmp_manager.get(parameter)
        except ValueError:
            raise ValueError("No Access to SNMPB parameters..")
        snmp_manager.close()


    def set_to_rx_mode(self, if_index, reg_num, register_module):
        # Set untested channel to Rx mode only
        register_module.set(('rf' + str(if_index), reg_num), 0x0) # set synthesizer of untested channel to OFF

    def set_to_txrx_mode(self, if_index, reg_num, register_module):
        # Return untested channel to TXRx mode
        register_module.set(('rf' + str(if_index), reg_num), 0x105)

    # Function defines reset uut
    def reset_board(self, plug_id, delay_sec = 35):
        print "Rebooting..."
        powerswitch.reboot_plugs([plug_id])
        time.sleep(delay_sec)    
        self.wait_until_awake()

# Calculation Tools
# dB to <11,3> format conversion
def dB_to_11_3(val):
    val = val * 8
    if val < 0:
        val = val * (-1)
        val = 0x800 - val
    return int(val)

# Evm calculations from 2 Phy input registers
# evm_out_str, no_bins_str must be strings of hexadecimal number
def evm_calc(evm_out_str, no_bins_str):
    evm = 0
    evm_out = int(evm_out_str, 16)
    evm_out = evm_out & bit_mask(28)
    no_bins = int(no_bins_str, 16)
    no_bins = no_bins & bit_mask(17)
    cons_energy = int(no_bins_str, 16)
    cons_energy = (cons_energy>>20) & bit_mask(6)
    denom = no_bins * cons_energy
    if denom !=0 and evm_out !=0:
        calc_evm = (evm_out / 256.0) / denom
        evm += 10.0 * math.log10(calc_evm)
    else:
        print 'Zero values of no_bins recieved'
        evm = 0
    return evm

# Bit mask function
def bit_mask(n):
    return ((1<<n)-1)

# Function for writing to file
def print_and_log(out_file, s):
    #print s
    out_file.write(s + "\n")    
    out_file.flush()

# Function defines user range with floating point step support
def set_range(start, end, step):
    while start <= end:
        yield start
        start += step    


# Function for searching a value in a sorted array    
def binary_search(a, key, imin=0, imax=None):
    """
    Iterative binary search function
    a: can be any iterable object
    """
    if imax is None:
        imax = len(a) - 1       # if max amount not set, get the total

    while imin <= imax:
        # calculate the midpoint
        mid = (imin + imax)//2
        midval = a[mid]

        # determine which subarray to search
        if midval < key:
            imin = mid + 1      # change min index to search upper subarray
        elif midval > key:
            imax = mid - 1      # change max index to search lower subarray
        else:
            return mid          # return index number
    return mid    

def make_window_active(my_title):
    toplist = []
    winlist = []
    def enum_callback(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_callback, toplist)
    program = [(hwnd, title) for hwnd, title in winlist if my_title in title]
    print program
    # just grab the first window that matches
    if len(program)>=1:
        program = program[0]
        # use the window handle to set focus
        shell=win32com.client.Dispatch("Wscript.Shell")
        shell.AppActivate(my_title)
        time.sleep(1)
        handle = win32gui.FindWindow(None,my_title)
        win32gui.SetForegroundWindow(handle)
        time.sleep(0.5)
        win32gui.ShowWindow(handle,win32con.SW_MAXIMIZE)
        #win32gui.SetForegroundWindow(program[0])
        time.sleep(0.5)
        #win32gui.SetFocus(program[0])
        #time.sleep(0.5)
    
def find_string_and_place_status(file_in, file_out, string_to_find):
    with open(file_in, 'r') as inF:
        for line in inF:
            string = string_to_find
            if string in line:
                f = open(file_name, 'w')
                f.write("Found :" +string)
                f.close()
            else:
                f = open(file_out, 'w')
                f.write("Not Found :" +string)
                f.close()

def dict_to_file(dictionary, filename):
    #file = open(filename, "w")
    #dictionary.items().sort() 
    with open(filename, "w") as file:
        for k, v in sorted(dictionary.iteritems()):
            file.write("{}:{}\n".format(k, v))
        file.flush()
        os.fsync(file)
    #file.close()

def file_to_dict(filename):
    dictionary = {}
    #file = open(filename, "r")
    with open(filename, "r") as file:
        for line in file.readlines():
            line = line.strip()
            splitted = line.split(":")
            if len(splitted) != 2:
                continue
            key = splitted[0]            
            value = splitted[1]
            dictionary[key] = value
        #file.flush()
        #os.fsync(file)
    #file.close()    
    return dictionary

def update_dict_in_file(filename, key, value):
    # open file wich contains dictionary
    data_dict = shelve.open(filename)
    for key in data_dict:
        data_dict[key] = value
    data_dict.close()

def make_dir_and_copy (source, destination_dir):
    #create directory
    try:
        #dir = os.path.dirname(destination_dir)
        if not (os.path.exists(destination_dir)):
            os.makedirs(destination_dir)
            print "Created new directory : ", destination_dir           
    except:
        print "Can't create the directoty :", destination_dir

    #copy source directory to new directory
    src_files = os.listdir(source)
    print "\nsrc_files ", src_files
    for file_name in (src_files):
        full_file_name = os.path.join(source, file_name)

        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, destination_dir)
        else:
            print "False, no files to copy"
    return destination_dir