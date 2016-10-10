import os, sys, time
import logging
from datetime import datetime
import re

from uuts import common as const
from lib import interfaces


log = logging.getLogger(__name__)

# CLI environment prompt
CLI_PROMPT = 'ate>'


# Supported target sub-systems
SUBSYSTEM = { 
    'mac0' : 'm 0', 
    'mac1' : 'm 1',
    'phy0' : 'p 0', 
    'phy1' : 'p 1',
    'rf0' : 'f 0', 
    'rf1' : 'f 1' 
    }


class DebugCli(object):
    """
    Fw CLI implementation 
    """

    def __init__(self, interface, uboot_support = False ):
        if not interface.__class__ in interfaces.INTERFACES.values():
            raise Exception("Received unexpected interface \'%s\'." % interface.__class__)
        
        self.u_boot = None
        self.interface = interface 
        if uboot_support:
            self.u_boot = UBootAPI( self.interface )

    def __del__(self):
        # Ignore any errors
        try:
            self.close()
        except Exception:
            pass

    def close( self ):
        if not self.u_boot is None:
            self.u_boot.close()
            self.u_boot = None

        self._flush()
        self.interface.close()


    def prof_reset(self):
        cmd = "prof reset"
        if ( self.is_connected == True):
            self.interface.write(cmd)

    def prof_display(self):
        cmd = "prof display"
        data = self.interface.write(cmd)
        return data 

    def _get_args(self, what):
        subsystem, address = what
        args = SUBSYSTEM[subsystem]
        return ' '.join([args, '{:x}'.format(address)])

    def _read_prompt(self, timeout_sec = 5 ):
        out = self.interface.read_until(CLI_PROMPT, timeout_sec = timeout_sec )
        if CLI_PROMPT not in out:
            raise IOError('Could not read prompt \'%s\'' % CLI_PROMPT)
        return out

    def _flush(self):
        # Ignore any error
        try:
            data = self.interface.handle.read_very_lazy()
            if len(data):
                log.info( "{}".format(data) )
        except Exception:
            pass

    def get_reg(self, register_name):
        args = self._get_args(register_name)
        cmd = ' '.join(['hwregs', 'r', args, '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt()
        return int(out.split('\r\n')[0], 16)
        #return int(out[len(cmd):-len(CLI_PROMPT)].strip(), 16)

    def set_reg(self, register_name, value):
        args = self._get_args(register_name)
        cmd = ' '.join(['hwregs', 'w', args, "{:x}".format(value), '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt()
        return int(out.split('\r\n')[0], 16)
        #return int(out[len(cmd):-len(CLI_PROMPT)].strip(), 16)

    def _get_output(self, ifindex, samples, timeout_sec = 5):
        cmd = ' '.join(['rxoob', str(ifindex), str(samples), str(timeout_sec)])
        self.interface.write(cmd.encode('ascii') + b"\r\n")
        res = self.interface.read_until(CLI_PROMPT)
        return res
        #return res.split('\r\n')[1]

    def get_rssi(self, ifindex=1, samples=10, timeout_sec=2, raise_exception_on_timeout=True):
        if ifindex not in (1, 2):
            raise ValueError

        output = self._get_output(ifindex, samples, timeout_sec)

        if raise_exception_on_timeout and "Operation timed out" in output:
            raise RuntimeError("Operation timed out")

        #Try extracting results from telnet
        try:
            float_format = "[-+]?(\d+(\.\d*)?|\.\d+)|nan"
            rssi_min = re.search("rssi log scale min: *(" + float_format + ")", output).group(1)
            rssi_avg = re.search("rssi log scale avg: *(" + float_format + ")", output).group(1)
            rssi_max = re.search("rssi log scale max: *(" + float_format + ")", output).group(1)
            rssi_mdev = None
            evm_min = re.search("evm min: *(" + float_format + ")", output).group(1)
            evm_avg = re.search("evm avg: *(" + float_format + ")", output).group(1)
            evm_max = re.search("evm max: *(" + float_format + ")", output).group(1)
            evm_mdev = re.search("evm mdev: *(" + float_format + ")", output).group(1)
        except AttributeError:
            raise RuntimeError("Failed extracting results from the following output: " + output)

        return {'rssi' : (rssi_min, rssi_avg, rssi_max, rssi_mdev),
                'evm'  : (evm_min,  evm_avg,  evm_max,  evm_mdev)}

    def dcoc_read_wfp(self, rf_id):
        cmd = ' '.join(['chan dcoc read wfp {:d}'.format(rf_id), '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt()
        return out.split('\r\nate')[0]

    def dcoc_calibrate(self, rf_id):
        # dcoc calibration
        cmd = ' '.join(['chan dcoc calibrate {:d}'.format(rf_id), '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt()

    def quit_from_registers( self ):
        cmd = ' '.join(['q', '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt()

    def dcoc_wfp_timer(self, rf_id, interval):
        cmd = ' '.join(['chan dcoc wfp timer {:d} {:d}'.format(rf_id, interval), '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt()

    def rx_iq_imbalance_calibrate(self, rf_id):
        # dcoc calibration
        cmd = ' '.join(['rx_iq_imbalance_b0 {:d}'.format(rf_id), '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        out = self._read_prompt(10)
        return out.split('\r\nate')[0]

    def reboot(self):
        # reboot board
        cmd = ' '.join(['reboot', '\r\n'])
        self.interface.write(cmd.encode('ascii'))
        #out = self._read_prompt()

    def get_version(self):
        cmd = ' '.join(['version', '\r\n'])
        self._flush()
        data = self.interface.write( cmd.encode('ascii') )
        if data == cmd:
            data = self._read_prompt()

        if len(data):
            if 'SDK:' in data: # New format
                # SDK: sdk-4.3.0-beta7-mc, U-BOOT: U-Boot 2012.04.01-atk-1.1.3-00526-g19cc217 (Nov 13 2014 - 10:13:42)
                # SDK: sdk-4.5.2-beta1-sc, HSM: N/A, U-BOOT: U-Boot 2012.04.01-atk-1.1.3-00526-g19cc217 (Nov 13 2014 - 10:13:42), GNSS: sta8088-3.1.15-atk22016-2.0.0
                data = data.replace('\r\n', '')
                vers = data.split(',')
                sdk_ver = vers[0].split(':')[1].strip()
                hsm_ver = vers[1].split(':')[1].strip()
                uboot_ver = vers[2].split(':')[1].strip()
                gnss_ver = vers[3 ].split(':')[1].strip()
                versions = {'sdk_ver': sdk_ver, 'uboot_ver' : uboot_ver, 'hsm_ver' : hsm_ver, 'gnss_ver' : gnss_ver }
                return versions

            else: # Old format only fw version
                f = [a for a in data.split('\r\n') if 'sdk' in a]
                if len(f) > 0:
                    return {'sdk_ver': f[0], 'uboot_ver' : ''}
                else:
                    return {'sdk_ver': f, 'uboot_ver' : ''}

    def is_alive(self):
        
        self.interface.write('\r\n\r\n\r\n'.encode('ascii') )
        try:
            data = self._read_prompt( timeout_sec  = 2 )
        except:
            pass
        self._flush()


    def read_cpus_profiling(self):

        data = ''
        start = False
        reads = 0

        while (1):
            line = self.interface.read_until( timeout_sec = 1 )

            if line is '':
                reads += 1

            # End of reading 
            if line is '' and start:
                break
            
            # Starting point
            if '[CPU0]' in line and 'Idle' in line:
                start = True

            if start:
                data += line

            if reads > 30:
                raise EOFError("Unable to read prof")

        a = data.split('\r\n')

        tasks = { 'CPU0' : [], 'CPU1' : [], 'CPU2' : [] }
        for line in a:
            if 'CPU' in line:
                # Start parsing the line
                b = line.split('\t')
                try:
                    tasks[ b[0][1:5] ].append( { 'task' : b[1].strip(), 'cpu_usage' : b[3][:-1] } ) 
                except Exception:
                    pass


        cpu_idle = {'arm' : float( tasks['CPU0'][0]['cpu_usage'] ), 'arc1' :  float( tasks['CPU1'][0]['cpu_usage'] ), 'arc2' : float( tasks['CPU2'][0]['cpu_usage'] ) }
        
        return { 'tasks' : tasks, 'idle' : cpu_idle }            






class UBootAPI(object):
    """
    API to U-Boot environment.

    """

    def __init__(self, interface):

        if not interface.__class__ in interfaces.INTERFACES.values():
            raise Exception("Received unexpected interface \'%s\'." % interface.__class__)

        self.interface = interface 
        self.updated_values = False

    def __del__(self):
        self.close()

    # Check the current prompt of the evk
    def check_prompt(self):
        is_uboot = False
        is_cli = False

        # Send enter and check if we receive 'ate>' or 'U-Boot>'
        self.interface.write(const.RN, False)
        rs = self.interface.read(const.STD_CLI_PROMPT, 1).rstrip()

        if const.STD_CLI_PROMPT in rs:
            is_cli = True 
        # Check if the last letters in the string are U-Boot prompt
        elif rs[-len(const.UBOOT_PROMPT):] == const.UBOOT_PROMPT :
            is_uboot = True

        return (is_cli, is_uboot)


    def reboot(self):
        log.info('Start reboot ...')
        is_cli = False
        is_uboot = False

        for i in range(3):
            (is_cli, is_uboot) = self.check_prompt()

            if is_cli:
                break

            if is_uboot:
                return const.EXIT_OK #  Already inside the U-Boot


        if not is_cli:
             log.Error("Cannot reboot, unable to receive the standard CLI prompt \'%s\'." % const.STD_CLI_PROMPT)
             raise LookupError("Unable to find cli type")
               
        self.interface.write('reboot' + const.RN, check_echo = False)
        self.interface.read('Hit')
        self.interface.write(const.RN, False)
        rs = self.interface.read(const.UBOOT_PROMPT)

        if not const.UBOOT_PROMPT in rs :
            log.Error("Reboot failed, doesn't get the \'U-Boot\' prompt")
            raise LookupError("Unable to find cli type")

        log.info('Reboot unit endded')



    def close(self):

        if self.interface is None:
            return

        #  Make sure we are not staying in the U-Boot when closing the API.
        #  If we are, send reset before leaving.
        ( _ , is_uboot) = self.check_prompt()

        if is_uboot:
            self.reset()

        self.interface = None


    #  Return the U-Boot print output or error in case the U-Boot prompt didn't return
    def print_env(self): 
        d = dict()
        self.interface.write('print')
        rs = self.interface.read(const.UBOOT_PROMPT,20)

        if not const.UBOOT_PROMPT in rs:
            log.Error("Command print doesn't end properly. \'U-Boot\' prompt doesn't return")
            return d

        # Parse the output to dictionary
        for line in rs.splitlines():
            items = line.split('=')
            if len(items) == 2:
                d[items[0]] = items[1]
            elif len(items) > 2:
                d[items[0]] = '='.join(items[1:])

        return d


    # Reset the unit or enter the U-Boot in case fUboot is True
    def reset(self, fUboot = False):

        log.info('Start reset ...')
        if self.updated_values:
            self.save()

        self.interface.write('reset')
        
        if fUboot:
            self.interface.read('Hit')
            self.interface.write(const.RN, False)
            rs = self.interface.read(const.UBOOT_PROMPT)

            if not const.UBOOT_PROMPT in rs:
                raise Exception("Failed enter U-Boot environment while reset.")
                log.Error("Failed enter U-Boot environment while reset.")
                
            log.info('Reset and enter U-Boot environment')
            return 


        rs = self.interface.read(const.STD_CLI_PROMPT, 60)

        if not const.STD_CLI_PROMPT in rs:
            (is_cli, _ ) = self.check_prompt()
            if not is_cli:
                log.Error("Failed reset the unit. CLI prompt doesn't return.")
                raise Exception("Failed reset the unit. CLI prompt doesn't return.")

        log.info('Reset unit endded')



    def set_value(self, key, value):
        command = ' '.join(['set',key,str(value)])
        self.interface.write(command + const.RN)
        self.updated_values = True
        rs = self.interface.read(const.UBOOT_PROMPT)

        if not const.UBOOT_PROMPT in rs :
            log.Error("Set value doesn't end properly. \'U-Boot\' prompt doesn't return")
            raise Exception("Set value doesn't end properly. \'U-Boot\' prompt doesn't return")

    def save(self):
        self.interface.write('save' + const.RN)
        self.updated_values = False
        rs = self.interface.read(const.UBOOT_PROMPT, 10)

        if not const.UBOOT_PROMPT in rs:
            log.Error("Save doesn't end properly. \'U-Boot\' prompt doesn't return")
            raise Exception("Save doesn't end properly. \'U-Boot\' prompt doesn't return")


if __name__ == "__main__":
    import multiprocessing
    def test():
        tftp_srv = None
        interface = None
        uboot = None
    
        try:
            import tftp_server

            tftp_srv = tftp_server.TftpSrv(path_dir='Z:\\SW\\Release\\craton-sdk\\sdk-4.2\\2\\beta9\\pangaea4', listenport=69)
            tftp_srv.start()

            interface_type = 'TELNET'
            cnn_info = { 'host':'trs01', 'port':2056, 'timeout_sec': 10 }
            interface = INTERFACES[interface_type](cnn_info)

            interface.open()

            uboot = UBootAPI(interface)

            rs = uboot.reboot();
            print 'Connected to U-Boot via telnet'
            print rs

            while True:
                print 'What do you want to do ? ',
                command = raw_input()

                if command == 'print':
                    d = uboot.print_env()
                    for i in sorted(d.keys()): 
                        print i+'='+d[i]
                    continue

                elif command == 'save':
                    rs = uboot.save()
                    print rs
                    continue

                elif command == 'reset':
                    rs = uboot.reset()
                    print rs
                    continue

                elif command[:4] == 'set ':
                    command_words = command.split(' ')

                    if len(command_words) == 3:
                        (set,key,value) = command_words
                    elif len(command_words) == 2:
                        (set,key) = command_words
                        value = ''
                    else:
                        print 'You entered incorrect command. Try again !'
                        continue

                    rs = uboot.set_value(key, value)
                    print rs
                    continue

                elif command == 'exit':
                    break

                else:
                    print "Unknown command: %s" % command

        except Exception, e:
            print str(e)
        finally:
            if not uboot is None:
                uboot.close()
    
            if not interface is None:
                interface.close()

            if not tftp_srv is None:
                tftp_srv.stop()

        
        print 'End test function !'


    ##### Testing
    print
    print('Testing U-Boot API')
    print('------------')
    print

    # Create timestamp for log and report file
    scn_time = "%s" % (datetime.now().strftime("%d%m%Y_%H%M%S"))
    """ @var logger handle for loging library """
    log_file =  os.path.join("c:\\temp", "st_log_%s.txt" % (scn_time) )
    print "Note : log file created, all messages will redirect to : \n%s" % log_file
    logging.basicConfig(filename=log_file, filemode='w', level=logging.NOTSET)
    log = logging.getLogger(__name__)
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.DEBUG)

    test()


