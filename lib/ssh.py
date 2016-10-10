import os
import paramiko
import subprocess
import logging

# TODO: use paramiko's transport instead of scp

USER = 'root'
PASS = '123'

log = logging.getLogger(__name__)

class SSHSession(paramiko.SSHClient):
    '''
    Manage a single SSH Session; convenience wrapper around SSHClient. 
    '''
    def __init__(self, target_ip, user = USER, pwd = PASS):
        self._target_ip = target_ip
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(self._target_ip, username=user, password=pwd)
        self._devnull = open(os.devnull, 'w')

    def exec_command(self, command):
        log.info( "SSH TX : %s", command)
        self.streams = self._client.exec_command(command)
        return self.exit_status()

    def read_output(self):
        data = self.streams[1].readlines()
        log.info( "SSH RX : %s", data)
        return data
    
    def status_ready(self):
        while not self.streams[0].channel.exit_status_ready():
            pass

    def exit_status(self):
        return self.streams[0].channel.exit_status

    def copy_from_remote(self, remote, local):
        args = ['scp', 'root@%s:%s' % (self._target_ip, remote), local]
        subprocess.check_call(args, stdout=self._devnull)

    def copy_to_remote(self, local, remote):
        args = ['scp', local, 'root@%s:%s' % (self._target_ip, remote)]
        subprocess.check_call(args, stdout=self._devnull)

    def disconnect(self):
        self._client.close()
        self._devnull.close()

    def __del__(self):
        self.disconnect()



if __name__ == "__main__":

    def check_tcp_dump():
    
        import time

        a = SSHSession( '10.10.0.165', 'root' , '123')
        a.exec_command( '/usr/sbin/tcpdump -i wlan0 -w /root/capture/tests_sdk2_0_tc_bsm_1_090613_150631.pcap')
        print "done!"
    
        while (1):
            time.sleep(0.200)

    def connnet_ub01( user, password ):
        a = SSHSession( 'ub01', user, password )
        a.exec_command( 'cd ~/qa.mc' )
        print read_output

    def test_vmbox():
        import time

        a = SSHSession( '10.10.1.127', 'user' , '123')
        a.exec_command( 'gpsfake -blc{} -o "-G" {}'.format( 0.5, '/media/sf_Z_DRIVE/users/shochats/test.nmea' ) )

        time.sleep(5)
        a.exec_command( '\x003' )
        a.close()


    test_vmbox()
    # connnet_ub01( 'shochats', 'Ahajryk5%' )
