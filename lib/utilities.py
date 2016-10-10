
from uuts import common
from lib import globals, ssh
import time


# General implementation of Enum
class Enum(tuple): __getattr__ = tuple.index
	
	
# Define general board type supported
BoardsTypes = Enum(['PANAGEA2-51', 'PANAGEA3', 'EVK'])


def timestamp():
   now = time.time()
   localtime = time.localtime(now)
   milliseconds = '%03d' % int((now - int(now)) * 1000)
   return time.strftime('%H:%M:%S.', localtime) + milliseconds


# General utilites
def get_value( json_data, key_name):
    """ Get value from json ctype configuration file """
    try:
        return json_data[key_name]
    except KeyError:
        raise globals.Error('File corrupt, file should contain `%s\' attribute' % (key_name))
    else:
        raise globals.Error("Unknow error getting value from configuration file. key : `%s\'" % (key_name))

    




def start_v2x_cli_external_host( target ):
    return
    external_host = ssh.SSHSession( target, 'user', '1qazxsw2' )
    external_host.exec_command ( "nohup ./v2x-cli &")
    external_host = None



