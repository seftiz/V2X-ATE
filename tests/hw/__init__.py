ISO_TIME_FMT = '%Y-%m-%dT%H:%M:%S'


import sys, os, time
import unittest

import inspect
import re
import argparse
import socket
import math
import numpy
import subprocess
import win32gui, win32con
import csv
import ConfigParser
import logging
import telnetlib
from os.path import isfile, join
from os import listdir
from time import ctime
#from hw import hw_setup_config

#pysdk_version = hw_setup_config['QA_SDK_VERSION']  # get updated sdk version

#pysdk = r'\\fs01\docs\SW\qa-sdk' + '\\' + pysdk_version + r'\python'
#print "\n\npysdk: ", pysdk
#sys.path.append(pysdk)