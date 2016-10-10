
""" add libraries on atlk server """


DEFAULT_PORT = 8000
DEFAULT_DEBUG_CLI_PORT = 23
DEFAULT_PROMPT = "qa@arm >>" # default prompt to telnet cli

DEFAULT_PROMPT_ARC = 'qa@arc%d >>' # default prompt to telnet cli

DEFAULT_TIMEOUT = 10
DEFUALT_USER_NAME = "root"
DEFUALT_USER_PWD = DEFUALT_USER_NAME
DEFUALT_INTERFACE = 'TELNET'
DEFUALT_CONNECT_RETRIES = 3
DEFAULT_TELNET_PORT = 23
DEFAULT_TELNET_TIMEOUT = 10

# Define globals variables

import time
usleep = lambda x: time.sleep(x/1000000.0)
 

"""
uBoot API constants
"""
STD_CLI_PROMPT = 'ate>'
UBOOT_PROMPT = 'U-Boot>'
NEW_LINE = '\n'
RETURN_CATRIDGE = '\r'
RN = RETURN_CATRIDGE + NEW_LINE


EXIT_OK = 0
EXIT_ERROR = -1
