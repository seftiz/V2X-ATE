import os, sys, time
sys.path.append('u:\\qa\\')
from lib.instruments.Komodo import komodo_if
from array import array
import re


def load_can_data_file(file_name):
	""" 
	This is the example of can bus data file 
	can_id = 0x0c1, dlc = 8, data = [0x93, 0xFD, 0x07, 0xD0, 0x90, 0x2C, 0xDF, 0x40])
	can_id = 0x0c5, dlc = 8, data = [0x93, 0xB4, 0x1E, 0xE0, 0x53, 0xEC, 0xF0, 0x3C], wait = 1)
	"""
	can_data = list()

	file_hwd = open( file_name, "r")
	for line in file_hwd:
		# split to 3 blocks
		base = line[5:-2].split(',',2)
		# extract can_id messages value
		cam_msg = int(base[0].split('=')[1].strip(),16)
		# extract cam data length
		cam_data_len = int(base[1].split('=')[1].strip())
		# Create regular expression
		regex = re.compile("0x[A-F0-9][0-9A-F]+")
		#data = regex.findall(base[2])
		data = re.findall(r'0x[0-9A-F]+', base[2], re.I)
		# convert each ascii hex into its binary value
		cam_data = [int(x, 16) for x in data]
		if cam_data_len != len(cam_data):
				continue
		can_data.append( (cam_msg, cam_data_len, cam_data) )

	file_hwd.close()

	return can_data

    

 
print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)

channel = int(sys.argv[1])

try:
    print "Send frame locally on channel %d" % channel
    can_bus = komodo_if.Komodo()

    if  channel is None:
        channel = komodo_if.KOMODO_IF_CAN_A

    can_bus.configure_port(channel)

    can_bus.power_up(channel)

    can_data = load_can_data_file( "C:/Temp/Marben_Testing/audi_can_data_komodo_gui.kba" )
    i = 0
    while True:
        print "Trans {} can msgs for the {} @ {}".format( len(can_data),  i, time.time() )
        i += 1
        for can_msg in can_data:
            msg_id, _, msg_data = can_msg
            try:
                can_bus.send_frame( channel, msg_id, msg_data )
            except Exception as e:
                pass
except Exception as e:
    raise e
#finally:
#    can_bus.power_down(channel)


