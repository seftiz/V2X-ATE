"""
@file      gm_common.py
@brief     Common definitions for GM testing
@author    Moosa Baransi
@version   1.0
@date      09/07/2013
"""

# Abbreviation convension
# CMD = command
# OPT = command option
# RSP = command response 
# RCV = Received frame

UART_CMD_ENABLE_CAN_ID    = "\x03"
UART_RSP_ENABLE_CAN_ID    = "\x43"

UART_OPT_ENABLE_CAN_HS    = "\x02"
UART_OPT_ENABLE_CAN_SW    = "\x01"
UART_OPT_ENABLE_CAN_BOTH  = "\x03"
UART_OPT_ENABLE_CAN_NONE  = "\x00"
UART_OPT_ENABLE_CAN_VALID = [UART_OPT_ENABLE_CAN_HS, UART_OPT_ENABLE_CAN_SW, UART_OPT_ENABLE_CAN_BOTH, UART_OPT_ENABLE_CAN_NONE]


UART_CMD_MONITOR_HS_ID    = "\x04"
UART_CMD_MONITOR_SW_ID    = "\x05"

UART_OPT_MONITOR_ADD      = "\x01"
UART_OPT_MONITOR_DEL      = "\x02"
UART_OPT_MONITOR_DEL_ALL  = "\x03"

UART_RSP_MONITOR_HS       = "\x44"
UART_RSP_MONITOR_SW       = "\x45"

UART_RCV_HS_ID            = "\xA0"
UART_RCV_SW_ID            = "\xA1"

UART_LOGGER_NAME          = "uart_logger"
UART_LOGGER_FILE          = "bridge.log"

CAN_AVAILABLE_HS_MESSAGES = [ "\x00\xC9", "\x00\xF1", "\x01\x20", "\x01\x2A",
                              "\x01\x40", "\x01\x7D", "\x01\xA1", "\x01\xE5",
                              "\x01\xE9", "\x01\xF1", "\x01\xF5", "\x03\xD1",
                              "\x03\xE9"]

UART_OPT_MONITOR_VALID   = [UART_OPT_MONITOR_ADD, UART_OPT_MONITOR_DEL, UART_OPT_MONITOR_DEL_ALL]

GM_FUNCTIONAL_TEST = 0
GM_SANITY_TEST = 1
