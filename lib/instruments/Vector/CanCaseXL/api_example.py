#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="mapl"
__date__ ="$03.03.2010 12:06:07$"



import canlib_xl
import ctypes
import msvcrt
import time




if __name__ == "__main__":

	can = canlib_xl.can_api()

	can_hs=can.open_channel( 0 )

	can_sw=can.open_channel( 1 )

	
	# HBE Event : 0x17d, dlc = 6, data = [0x22, 0x24, 0x42, 0x96, 0x0F, 0xCF]
	msg_id, hbe = ( 0x17d, [0x00, 0x00, 0x00, 0x00, 0x0E, 0x70] )
	
	ok=can_hs.send_msg([0x00, 0x00, 0x00, 0x00, 0x0E, 0x70] , 0x17d )
	msg = can_sw.get_msg()
	print "data sw", msg
	
	can_sw.close()
	can_hs.close()


