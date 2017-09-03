#!/usr/bin/python2.7 -tt
import os, serial, time
import shutil
import telnetlib
import urllib
import logging
import sys
import datetime
from collections import OrderedDict
import argparse

# Define tree for 3 layer array
from collections import defaultdict
def tree(): return defaultdict

def power_up(outlet): 
    
    cmd = 'http://%s@%s/on.cgi?led=%s' % ( power_switch_user_pwd, power_switch_addr, ('0' * outlet + '1').ljust( 22, '0') )
    logging.info('{}\n'.format(cmd))
    urllib.urlopen(cmd).close()  

def power_down(outlet):
    cmd = 'http://%s@%s/off.cgi?led=%s' % ( power_switch_user_pwd, power_switch_addr, ('0' * outlet + '1').ljust( 22, '0') )
    logging.info('{}\n'.format(cmd))
    urllib.urlopen(cmd).close()  

def power_cycle(outlet):
    cmd = 'http://%s@%s/offon.cgi?led=%s' % ( power_switch_user_pwd, power_switch_addr, ('0' * outlet + '1').ljust( 22, '0') )
    logging.info('{}\n'.format(cmd))
    urllib.urlopen(cmd).close()  
  
def tn_connect(targetip = '10.10.1.122'):
    try:
      tnn = telnetlib.Telnet(targetip)
      if True:
        time.sleep(5)
        tmp = tnn.read_until('login:',3)
        tnn.write('user\n')
        time.sleep(0.2)
        tmp = tnn.read_very_eager()
        tmp = tnn.read_until('assword:',2)     # let "P" be capitalized or not
        tnn.write(args.vm_pw + '\n')
        tmp = tnn.read_until(str('$'), 3)
        tmp = tnn.read_very_eager()
    except Exception as e:
        logging.info('{}'.format(e))

    return tnn


def set_gps_gpio():
    global t
    global target_vm_ip
    global location_path
    global args
    rc = 0
    try:
        
        t = tn_connect(target_vm_ip)
        tmp = t.read_until(str('$'), 2)
        logging.info("Changing path to API location:{}\n".format( location_path ))
        t.write(str(location_path + '\n'))
        time.sleep(0.5)
        tmp = t.read_very_eager()
        #Run CLI aplication
        if args.dev_address != None:
          t.write(str('{}\n').format('\nsudo ./diag-cli {} {}\n'.format(args.dev_address, args.interface)))
        else:
          t.write(str('{}\n').format('\nsudo ./diag-cli {}\n'.format(args.interface)))
        time.sleep(0.5)
        tmp = t.read_until(str('user:'), 3)
        tmp = t.read_very_eager()
        t.write(args.vm_pw + '\n')
        time.sleep(5)
        tmp = t.read_until(str('atlk>'), 3)
        tmp = t.read_very_eager()

        if args.dev_address != None:
            logging.info("executing: diagcli {} {}\n".format(args.dev_address, args.interface))
        else:
            logging.info("executing: diagcli {}\n".format(args.interface))

        gpio_iomux_set_bit_factory()
        gpio_dir_val_set_bit_factory()

        t.write(str("quit\n"))

    except Exception as e:
        logging.info('\n{}\n'.format(e))
        t.close()
        rc = -1
    return rc                 


def readBuffer(ser):
    try:
        data = ser.read(1)
        n = ser.inWaiting()
        if n:
            data = data + ser.read(n)
        return data
    except Exception, e:
        logging.info('{}'.format(e))
        return ''   



def open_ser_conn():
    #possible timeout values:
  #    1. None: wait forever, block call
  #    2. 0: non-blocking mode, return immediately
  #    3. x, x is bigger than 0, float allowed, timeout block call
  global args
  ser = serial.Serial()
  ser.port = args.com
  ser.baudrate = 115200
  ser.bytesize = serial.EIGHTBITS #number of bits per bytes
  ser.parity = serial.PARITY_NONE #set parity check: no parity
  ser.stopbits = serial.STOPBITS_ONE #number of stop bits
  #ser.timeout = None          #block read
  ser.timeout = 1            #non-block read
  #ser.timeout = 2              #timeout block read
  ser.xonxoff = False     #disable software flow control
  ser.rtscts = False     #disable hardware (RTS/CTS) flow control
  ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
  ser.writeTimeout = 2     #timeout for write

  try: 
      ser.open()
  except Exception, e:
      logging.info('\nError open serial port: \n' + str(e))
      return -1
  
  ser.flushInput() #flush input buffer, zohar: clear input
  ser.flushOutput()#flush output buffer, zohar: clear output 

  return ser
  
    
def test_board_power_cycle(ser, counter):
  
  time.sleep(1)  #give the serial port sometime to receive the data
  if not ser.isOpen():
    logging.info('\ncannot open serial port\n ')
    ser.close()
    logging.info('\ntrying to reopen...\n ')
    ser = open_ser_conn()
    if ser == -1:
      logging.info('\nfatal serial crash...can\'t recover...terminating test...\n')
      sys.exit(0)
    logging.info('\nserial connection reestablished...continue testing\n ')
  
  try:
      time.sleep(1)  #give the serial port sometime to receive the data
      response = readBuffer(ser)
      logging.info(' \ndevice traces: \n{}'.format(response))
      if response.find(board_is_up_text) == -1:
        logging.info('power cycle break at cycle# {}'.format(counter))
        ser.flushInput() #flush input buffer, zohar: clear input
        ser.flushOutput()#flush output buffer, zohar: clear output 
        ser.close()
        return -1
      else:
         ser.flushInput() #flush input buffer, zohar: clear input
         ser.flushOutput()#flush output buffer, zohar: clear output 
               #and discard all that is in buffer
         return 0
  except Exception, e1:
      logging.info('error communicating...: ' + str(e1))
      ser.close()
      return -1

  
#def  init_gpio(gpio_iomux_dict, gpio_dir_dict, gpio_val_dict, iomux_set_bit_dict, dir_val_set_bit_dict_1st, dir_val_set_bit_dict_2nd, dir_val_set_bit_dict_3rd):
def  init_gpio():
    global gpio_iomux_dict
    global gpio_dir_dict
    global gpio_val_dict
    global iomux_set_bit_dict
    global dir_val_set_bit_dict_1st
    global dir_val_set_bit_dict_2nd
    global dir_val_set_bit_dict_3rd

    gpio_iomux_dict = OrderedDict([('IOMUX_A_GPIO_0',0x48120020), ('IOMUX_A_GPIO_1',0x48121020), ('IOMUX_A_GPIO_2',0x48122020), ('IOMUX_A_M3GPIO',0x40008020),
                       ('IOMUX_B_GPIO_0',0x48120024), ('IOMUX_B_GPIO_1',0x48121024), ('IOMUX_B_GPIO_2',0x48122024), ('IOMUX_B_M3GPIO',0x40008024)])
    

    gpio_dir_dict   = OrderedDict([('DIR_GPIO_0',0x48120010), ('DIR_GPIO_1',0x48121010), ('DIR_GPIO_2',0x48122010), ('DIR_M3GPIO',0x40008010)])


    gpio_val_dict   = OrderedDict([('VAL_GPIO_0',0x48120000), ('VAL_GPIO_1',0x48121000), ('VAL_GPIO_2',0x48122000), ('VAL_M3GPIO',0x40008000)])


    iomux_set_bit_dict = OrderedDict([('gpio 37',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_1'], 'bit':5, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_1'], 'bit':5, 'value':0}]),
                          ('gpio 69',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_2'], 'bit':5, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_2'], 'bit':5, 'value':0}]),
                          ('gpio 70',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_2'], 'bit':6, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_2'], 'bit':6, 'value':0}]),
                          ('gpio 30',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_0'], 'bit':30, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_0'], 'bit':30, 'value':0}]),
                          ('gpio 31',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_0'], 'bit':31, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_0'], 'bit':31, 'value':0}]),
                          ('gpio 14',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_0'], 'bit':14, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_0'], 'bit':14, 'value':0}]),
                          ('gpio 15',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_0'], 'bit':15, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_0'], 'bit':15, 'value':0}]),
                          ('gpio 4',[{'address':gpio_iomux_dict['IOMUX_A_GPIO_0'], 'bit':4, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_GPIO_0'], 'bit':4, 'value':0}]),
                          ('M3 gpio 9',[{'address':gpio_iomux_dict['IOMUX_A_M3GPIO'], 'bit':17, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_M3GPIO'], 'bit':17, 'value':0}]),
                          ('M3 gpio 11',[{'address':gpio_iomux_dict['IOMUX_A_M3GPIO'], 'bit':20, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_M3GPIO'], 'bit':20, 'value':0}]),
                          ('M3 gpio 12',[{'address':gpio_iomux_dict['IOMUX_A_M3GPIO'], 'bit':19, 'value':0}, {'address':gpio_iomux_dict['IOMUX_B_M3GPIO'], 'bit':19, 'value':0}])])


    dir_val_set_bit_dict_1st = OrderedDict([('gpio 37',[{'address':gpio_dir_dict['DIR_GPIO_1'], 'bit':5, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_1'], 'bit':5, 'value':0}]),
                                            ('gpio 69',[{'address':gpio_dir_dict['DIR_GPIO_2'], 'bit':5, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_2'], 'bit':5, 'value':1}]),
                                            ('gpio 70',[{'address':gpio_dir_dict['DIR_GPIO_1'], 'bit':6, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_1'], 'bit':6, 'value':0}]),
                          ('M3 gpio 9',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':17, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':17, 'value':0}]),
                          ('gpio 30',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':30, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':30, 'value':0}]),
                          ('gpio 31',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':31, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':31, 'value':0}]),
                          ('gpio 14',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':14, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':14, 'value':0}]),
                          ('gpio 15',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':15, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':15, 'value':0}]),
                          ('M3 gpio 11',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':20, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':20, 'value':0}]),
                          ('M3 gpio 12',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':19, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':19, 'value':0}]),
                          ('gpio 4',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':4, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':4, 'value':0}])])


    dir_val_set_bit_dict_2nd = OrderedDict([('gpio 37',[{'address':gpio_dir_dict['DIR_GPIO_1'], 'bit':5, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_1'], 'bit':5, 'value':1}]),
                          ('M3 gpio 9',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':17, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':17, 'value':1}]),
                          ('gpio 30',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':30, 'value':0}]),
                          ('gpio 31',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':31, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':31, 'value':1}]),
                          ('gpio 14',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':14, 'value':0}]),
                          ('gpio 15',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':15, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':15, 'value':1}]),
                          ('M3 gpio 11',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':20, 'value':0}]),
                          ('M3 gpio 12',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':19, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':19, 'value':1}]),
                          ('gpio 4',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':4, 'value':0}])])


    dir_val_set_bit_dict_3rd = OrderedDict([('gpio 70',[{'address':gpio_dir_dict['DIR_GPIO_1'], 'bit':6, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_1'], 'bit':6, 'value':1}]),
                          ('gpio 37',[{'address':gpio_dir_dict['DIR_GPIO_1'], 'bit':5, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_1'], 'bit':5, 'value':1}]),
                          ('gpio 70(2)',[{'address':gpio_dir_dict['DIR_GPIO_1'], 'bit':6, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_1'], 'bit':6, 'value':0}]),
                          ('M3 gpio 9',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':17, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':17, 'value':1}]),
                          ('gpio 30',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':30, 'value':0}]),
                          ('gpio 31',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':31, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':31, 'value':1}]),
                          ('gpio 14',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':14, 'value':0}]),
                          ('gpio 15',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':15, 'value':1}, {'address':gpio_val_dict['VAL_GPIO_0'], 'bit':15, 'value':1}]),
                          ('M3 gpio 11',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':20, 'value':0}]),
                          ('M3 gpio 12',[{'address':gpio_dir_dict['DIR_M3GPIO'], 'bit':19, 'value':1}, {'address':gpio_val_dict['VAL_M3GPIO'], 'bit':19, 'value':1}]),
                          ('gpio 4',[{'address':gpio_dir_dict['DIR_GPIO_0'], 'bit':4, 'value':0}])])

    logging.info('______configuration setup_____:\n\n')
    logging.info('iomux registers addresses:\n')
    for k, v in gpio_iomux_dict.items():
        logging.info('{},  {}\n'.format(k, hex(v)))
    logging.info('\n\n')

    logging.info('direction registers addresses:\n')
    for k, v in gpio_dir_dict.items():
        logging.info('{},  {}\n'.format(k, hex(v)))
    logging.info('\n\n')

    logging.info('values registers addresses:\n')
    for k, v in gpio_val_dict.items():
        logging.info('{},  {}\n'.format(k, hex(v)))
    logging.info('\n\n')

    logging.info('iomux setup:\n')
    for k, v in iomux_set_bit_dict.items():
        logging.info('{},  {}\n'.format(k, v))
    logging.info('\n\n')

    logging.info('first direction-value setup:\n')
    for k, v in dir_val_set_bit_dict_1st.items():
        logging.info('{},  {}\n'.format(k, v))
    logging.info('\n\n')

    logging.info('second direction-value setup:\n')
    for k, v in dir_val_set_bit_dict_2nd.items():
        logging.info('{},  {}\n'.format(k, v))
    logging.info('\n\n')

    logging.info('third direction-value setup:\n')
    for k, v in dir_val_set_bit_dict_3rd.items():
        logging.info('{},  {}\n'.format(k, v))
    logging.info('\n\n')


def set_bit(gpio_info):
    global t
    MASK = 1 << gpio_info['bit']

    t.write(str('dbg md {}\n'.format(hex(gpio_info['address']))))
    time.sleep(0.5)
    reg_addr_and_val= t.read_until(str('atlk>'), 3)
    time.sleep(0.5)
    tmp = t.read_very_eager()
    time.sleep(0.5)
    reg_val = (reg_addr_and_val.split('\r\n')[1]).split()[1]

    if gpio_info['value'] == 1:
        reg_new_val = int(reg_val, 16) | MASK
    else:
        reg_new_val = int(reg_val, 16) & ~(MASK)
    logging.info('\n\n\n[set_bit] address: {}, bit: {}, val: {}\n'.format(hex(gpio_info['address']), gpio_info['bit'], gpio_info['value']))
    logging.info('[set_bit read] val: {}\n'.format(reg_val))
    time.sleep(0.5)
    t.write(str('dbg mw {} {}\n'.format(hex(gpio_info['address']), hex(reg_new_val))))
    time.sleep(0.5)
    tmp = t.read_until(str('atlk>'), 3)
    time.sleep(0.5)
    tmp = t.read_very_eager()
    time.sleep(0.5)
    
    logging.info('[set_bit write]: new val  {}\n\n'.format(hex(reg_new_val)))



def gpio_iomux_set_bit_factory():
    global t
    global iomux_set_bit_dict
    for gpio in iomux_set_bit_dict:
        for gpio_info in iomux_set_bit_dict[gpio]:
            logging.info('{}: {}\n'.format(gpio, iomux_set_bit_dict[gpio]))
            set_bit(gpio_info)
            time.sleep(1)


def gpio_dir_val_set_bit_factory():
    global t
    global dir_val_set_bit_dict_1st
    global dir_val_set_bit_dict_2nd
    global dir_val_set_bit_dict_3rd

    for gpio in dir_val_set_bit_dict_1st:
        for gpio_info in dir_val_set_bit_dict_1st[gpio]:
            logging.info('{}: {}\n'.format(gpio, dir_val_set_bit_dict_1st[gpio]))
            set_bit(gpio_info)
            time.sleep(1)

    #for gpio in dir_val_set_bit_dict_3rd:
    #    for gpio_info in dir_val_set_bit_dict_3rd[gpio]:
    #        logging.info('{}: {}\n'.format(gpio, dir_val_set_bit_dict_3rd[gpio]))
    #        set_bit(gpio_info)
    #        time.sleep(1)



    for gpio in dir_val_set_bit_dict_2nd:
        for gpio_info in dir_val_set_bit_dict_2nd[gpio]:
            logging.info('{}: {}\n'.format(gpio, dir_val_set_bit_dict_2nd[gpio]))
            set_bit(gpio_info)
            time.sleep(1)



def parse_params():
  global args
  parser = argparse.ArgumentParser( description='GPS gpio set script' )
  parser.add_argument( '-c', '--com', type=str, required=False, default='COM20', help='comm port for serial connection')
  parser.add_argument( '-p', '--pathcmd', type=str, required=False, default='cd /tftpboot/apps', help='change path commad to diagcli directory')
  parser.add_argument( '-i', '--interface', type=str, required=False, default='eth1', help='eth interface with the device')
  parser.add_argument( '-a', '--address', type=str, required=False, default='10.10.1.113', help='host VM ip address')
  parser.add_argument( '-r', '--reboot', action="store_true",help='with/without power cycly before setup')
  parser.add_argument( '-d', '--dev_address', type=str, required=False, default=None, help='device mac address')
  parser.add_argument( '-v', '--vm_pw', type=str, required=False, default='123', help='device mac address')
  args = parser.parse_args()
    


#initialization and open the port
if __name__ == "__main__":
    global power_switch_user_pwd
    global power_switch_addr
    global board_is_up_text
    global counter
    global target_vm_ip
    global location_path
    global gpio_iomux_dict
    global gpio_dir_dict
    global gpio_val_dict
    global iomux_set_bit_dict
    global dir_val_set_bit_dict_1st
    global dir_val_set_bit_dict_2nd
    global dir_val_set_bit_dict_3rd
    global args
    global t
    
    t = None  

    parse_params()  

    default_port           = 23
    power_switch_connector = 2
    data                   = ''
    expected_test_cycles   = 0
    power_switch_user_pwd  = "{}:{}".format( "snmp", "1234")
    power_switch_addr      = '10.10.0.3'
    board_is_up_text       = 'Created Socket'
    counter                = 0
    target_vm_ip           = args.address
    location_path          = args.pathcmd
    gpio_iomux_dict        = OrderedDict()
    gpio_dir_dict          = OrderedDict()
    gpio_val_dict          = OrderedDict()
    iomux_set_bit_dict     = OrderedDict()
      
    dir_val_set_bit_dict_1st = OrderedDict()
    dir_val_set_bit_dict_2nd = OrderedDict()
    dir_val_set_bit_dict_3rd = OrderedDict()

 #   t = None
    if os.path.exists("c:\\temp\\gps_gpio_conf.log"):
      os.remove("c:\\temp\\gps_gpio_conf.log")

    logging.basicConfig(filename='c:\\temp\\gps_gpio_conf.log', level=logging.INFO)
    logging.info('configuration started:\n')
    
    if args.reboot:
      ser = open_ser_conn()

      time.sleep(2)
      if ser == -1:
          sys.exit(0)

      time.sleep(2)

      logging.info('power up wait 60sec...')
      power_cycle(power_switch_connector)
      time.sleep(60)
      logging.info('################  check power cycle #################\n')
      rc = test_board_power_cycle(ser, counter)
      if rc == -1:
        sys.exit(0)

    #init_gpio(gpio_iomux_dict, gpio_dir_dict, gpio_val_dict, iomux_set_bit_dict, dir_val_set_bit_dict_1st, dir_val_set_bit_dict_2nd, dir_val_set_bit_dict_3rd)
    init_gpio()
    #if set_gps_gpio(iomux_set_bit_dict, dir_val_set_bit_dict_3rd) == -1:
    if set_gps_gpio() == -1:
        logging.info('################  set gps gpio FAILED... #################\n')
        sys.exit(0)
    logging.info('################  set gps gpio PASSED... #################\n')

    time.sleep(2)
    
    
