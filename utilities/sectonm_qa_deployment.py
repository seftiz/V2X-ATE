import os, sys
import shutil
import argparse
import subprocess
import time
import paramiko
import glob
from scp import SCPClient


# from subprocess import call

def main():

   
   ''' create ssh connection to linux VM '''
   vm_client = paramiko.SSHClient()
   vm_client.load_system_host_keys()
   vm_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   vm_client.connect('10.10.1.132',  22, 'user', '1qazxsw2')
   
   ''' create private 'channel' for async remote executions: '''
   ''' this channel will activate the linux QA cli application that will implement the tester FW API requests''' 
   transport = vm_client.get_transport()
   channel = transport.open_session()
   
   ''' kill previous active host cli application if any '''
   stdin, stdout, stderr = vm_client.exec_command( 'killall /home/user/sectonm-automation-host-cli' )
   print stdout.readlines()
   print stderr.read()

   
   ''' remove previous host cli application'''
   stdin, stdout, stderr = vm_client.exec_command( 'rm /home/user/sectonm-automation-host-cli' )
   print stdout.readlines()
   print stderr.read()
   
   ''' copy the new host QA cli application (new - means host QA cli application that is based on the tested new FW API)'''
   scp = SCPClient(transport)
   scp.put(r'\\fs01\docs\ATE\ftp\sectonm-automation-host-cli')
   print "\nsectonm-automation-host-cli copied to VM\n"
   
   ''' set executible rights to the host QA cli application '''
   stdin, stdout, stderr = vm_client.exec_command( 'chmod u+x /home/user/sectonm-automation-host-cli' )
   print stdout.readlines()
   print stderr.read()
   
   ''' execute the host QA cli application using the private 'channel' so the main automation script (i.e., this script...)
       could continue with the rest of the actions (i.e., activate the tests...)'''
   try:
    channel.exec_command("/home/user/sectonm-automation-host-cli")
    print "executing /home/user/sectonm-automation-host-cli"
    print stdout.readlines()
    print stderr.read()
   except paramiko.SSHException:
    print "\n\n!!! Error executing sectonm-automation-host-cli !!!\n\n"
    pass
    

   ''' finaly...start testing...'''
   try:
    print "executing qa.py"
    subprocess.check_call(r'python ".\qa.py" -t sc -sa -q')
    print stdout.readlines()
    print stderr.read()
   except Exception as e:
    print str(e)
    pass
    
    
    time.sleep(20)
   ''' kill active host cli application if any '''
   stdin, stdout, stderr = vm_client.exec_command( 'killall /home/user/sectonm-automation-host-cli' )
   print stdout.readlines()
   print stderr.read()
 
   vm_client.close()
   print "\nssh closed\n"
   
   ''' save new log to workspace and check for 'fail' or 'error' status '''
   try: 
     files=glob.glob('*.html')
     for filename in files:
       print "removing: " + filename
       os.remove(filename)
     newest = max(glob.iglob(r'c:\Temp\*.[Hh][Tt][Mm][Ll]'), key=os.path.getctime)
     print "copy: " + newest
     shutil.copy2(newest, os.getcwd())
     with open(newest) as f:
       content = f.readlines()
       for line in content:
         if line.find("class='failCase'") != -1 or line.find("class='errorCase'") != -1:
           raise Exception('execution failed')
   except Exception as e:
     print str(e)
     pass

if __name__ == "__main__":
    main()

