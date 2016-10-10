"""
@file      hdlc.py
@brief     High-Level Data Link Control (HDLC) procotol implementation for wrapping/unwrapping 
           data going on the UART interface
@author    Moosa Baransi
@version   1.0
@date      09/07/2013
"""

import logging
from gm_common import UART_LOGGER_NAME

HDLC_SOH = 0xC0
HDLC_EOT = 0xFE
HDLC_DLE = 0x7D
HDLC_XOR_VAL = 0x20

hdlc_special_char_list = [HDLC_SOH, HDLC_EOT, HDLC_DLE]

def hdlc_encode(buffer):
    cs = _hdlc_calc_cs(buffer)
    new_buf = chr(HDLC_SOH)
    for ch in buffer:
        och = ord(ch)
        if och in hdlc_special_char_list:
            new_buf += chr(HDLC_DLE)
            new_buf += chr(och ^ HDLC_XOR_VAL)
        else:
            new_buf += chr(och)
    new_buf += chr(cs)
    new_buf += chr(HDLC_EOT)
    return new_buf

def hdlc_decode(buffer):
    buffer = buffer[1:] # exclude SOH
    new_buf = ""
    need_xor = False
    cs = 0
    logger = logging.getLogger(UART_LOGGER_NAME)

    for ch in buffer:
        och = ord(ch)
        if och == HDLC_EOT:
            if cs == 0xFF:
                return new_buf[:-1]
            logger.error("CS error")
            return None

        if och == HDLC_DLE:
            need_xor = True
        else:
            if need_xor:
                new_buf += chr(ord(ch) ^ HDLC_XOR_VAL)
                need_xor = False
            else:
                new_buf += (ch)
            cs += ord(new_buf[-1]) ^ 0xAA
            cs &= 0xFF # cs is a one byte variable
    logger.error("No EOT was seen")
    return None

def _hdlc_calc_cs(buffer):
    cs = 0
    for ch in buffer:
        cs += ord(ch) ^ 0xAA
        cs &= 0xFF # cs is a one byte variable
    cs = 0xFF - (cs ^ 0xAA)
    return cs
