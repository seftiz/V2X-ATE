"""
@file cli_if.py
@brief Handle low level target interface connection.
@author    	Shai Shochat
@version	1.0
@date		18/01/2013
"""

import telnetlib

import socket
import time
import logging 
from uuts import common
from lib import globals, interfaces



""" @var logger reference for logging library, defined in v2x_cli.py"""
log = logging.getLogger(__name__)


class QaCliInterface(object):
    """
    @class QaCliInterface
    @brief low level telnet connection class
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self):
        self._host = None
        self.timeout = common.DEFAULT_TIMEOUT # set default timeout 
        self.port = common.DEFAULT_PORT
        self.prompt = common.DEFAULT_PROMPT # default prompt to telnet cli
        self.interface_type = 'TELNET'

    def __del__( self ):
        """Destructor -- close the connection."""
        try:
            self._host.close()
        except Exception as e:
            pass

    def interface( self ):
        """ Return the underlying telnet object contained by the class """
        return self._host

    def close(self ):
        self._host.close()

    def disconnect(self):
        if self._host is None:
            raise globals.Error('ERROR : system is not connected to any host')
        try:
            self.send_command("exit", False)
        except Exception:
            pass
        
    def connect(self, server, port = common.DEFAULT_PORT, timeout = common.DEFAULT_TIMEOUT, retries = 1 ):
        """ Connect to server with telnet protocl with desire port
            @param[in] server unit address as ip 
            @param[in] port port for telnet connection.
            @param[in] timeout timeout for telnet connection.
        """
        self.timeout = timeout
        self.port = port
        cnn_info = { 'host':server, 'port':port, 'timeout_sec': self.timeout }

        for retry in range(retries):
            try:
                host = interfaces.INTERFACES[self.interface_type]( cnn_info ) 
            except socket.gaierror as e:
                raise globals.Error('%s could not be found.' % server )
            except socket.error as e:
                raise globals.Error('Connection refused by %s.' % server)
            except socket.timeout as e:
              log.warning('Timed out connecting to %s, retrying to connect ' % server)
              time.sleep(5)
              if retry == (retries-1):
                raise globals.Error('Timed out connecting to %s' % server)
              continue
            except:
                raise globals.Error('unknown error connecting server %s' % server)
            else:
                self._host = host
                self._host.open()
                break;

        self.server_addr = server
        log.info("connected to cli on {}, port {}".format( server, port ) )

    def _read_until(self, data, timeout):
        """ Read data until prompt """
        try:
            data = self._host.read_until ( data, timeout )
        except EOFError as e:
            raise globals.Error('ERROR : EOF rasied, no data to read from server')
        except Exception as e:
            raise globals.Error('ERROR : Error reading from unit, {}'.format( e) )

        return data

    def read_until_prompt(self , timeout = -1):
        """ Read data until prompt """
        timeout = self.timeout if timeout == -1 else timeout
        return self._read_until( self.prompt, timeout )

    def read_line(self):
        """ Read data until New Line """
        return self._read_until( '\r', self.timeout )



    def send_command(self, cmd, read_prompt = True ):
        """ Send data to target via telnet
		@param[in] cmd Data to be sent 
		@note The function add NEWLINE (\\n) and Cattrige return (\\r)
		"""
        
        data = ''
        if self._host is None:
            raise globals.Error('ERROR : system is not connected to any host')

        if isinstance(cmd, unicode):
            cmd = str(cmd)

        # log.info("CLI {}, TIME {} TX : {}".format( self.server_addr,  "%f" % ( time.clock() ), "\n".join([b for b in cmd.splitlines() if len(b) > 0])  ) )
        rs = self._host.write(cmd , read_prompt )
        return ( rs if read_prompt else '' )

    
    def login(self, user = common.DEFUALT_USER_NAME, pwd = common.DEFUALT_USER_PWD ):
        """ Send data to target via telnet
        @param[in] user User name for V2X CLI.
        @param[in] pwd Password for user name.
        """
        data = self._host.read_until("Username:", 2)
        if data == '':
            raise globals.Error('ERROR : EOF rasied, no data to read from server') 
        else:
            self._host.write("%s" % user)
            self._host.read_until("Password:", 2)   
            self._host.write("%s" % pwd)

if __name__ == "__main__":
  
  # Test some command in telent connection
  tn = telnetlib.Telnet( "10.10.0.165" , 8000)
  
  print tn.read_until("Username:", 2)
  tn.write("root\n\r")
  print tn.read_until("Password:", 2)
  tn.write("root\n\r")

  print tn.read_until("v2x >>",2)
  """
  tn.write("gps start -mode queue\n\r")
  
  while 1:
	str = ''
	str = tn.read_until("\n")
	if str == '':
		continue
	print str
		
  # tn.write("session open\n\r")
  # print tn.read_until("v2x >>",2)

  # tn.write("wsmp open\n\r")
  # print tn.read_until("v2x >>",2)

  # tn.write("wsmp send_frame\n\r")
  # print tn.read_until("v2x >>",2)

  print "Script ended"
  """

