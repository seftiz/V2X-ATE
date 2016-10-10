#
# Copyright (C) 2011 ETSI
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Author: ETSI/STF424/Alexandre Berge <alexandre.berge@amb-consulting.com> 
#

#
# EXEC:   program's name
# TARGET: arm, i386
# DEBUG:  0 => none, 1 => low, 2 => medium, 3 => high
#
EXEC=bridge
TARGET=arm
DEBUG=4

#
# NO CHANGE BELOW THIS LINE
#------------------------------------------------------------------
SRCDIR=src
BUILDDIR=obj
CFLAGS=-W -Wall -pedantic #-D_GNU_SOURCE -ansi  
LDFLAGS=-lpthread
SRC=$(notdir $(wildcard ${SRCDIR}/*.c))
OBJ=$(addprefix $(BUILDDIR)/,$(SRC:.c=.o))

# Target handling
ifeq (${TARGET}, arm)
#CC=arm-unknown-linux-gnueabi-gcc 
# Compiler for LINUX    
#CC=/tools/gcc/buildroot/arm-2011.11-7-arm-unknown-linux-uclibcgnueabi-i686-pc-linux-gnu/bin/arm-unknown-linux-uclibcgnueabi-gcc
# Compiler for uUCLINUX
CC=/tools/gcc/sourcery/arm-2011.03-46-arm-uclinuxeabi-i686-pc-linux-gnu/bin/arm-uclinuxeabi-gcc
else
CC=gcc
endif

# DEBUG handling
ifneq (${DEBUG}, 0)
#CFLAGS+=-DDEBUG=${DEBUG}
#CFLAGS+=-ggdb
endif

#------------------------------------------------------------------

all: ${EXEC} Makefile

.PHONY: clean mrproper upload

${EXEC}: ${OBJ} Makefile
	@echo "LNK $@"
	@$(CC) -o $@ $(^:Makefile=) $(LDFLAGS)

${BUILDDIR}/%.o: ${SRCDIR}/%.c Makefile
	@echo " CC $@"
	@$(CC) -o $@ -c $< $(CFLAGS)

clean:
	@rm ${EXEC} ${BUILDDIR}/*.o 2> /dev/null || true

mrproper: clean
	@rm *~ ${SRCDIR}/*~ 2> /dev/null || true

upload: 
	@$(MAKE) clean
	@$(MAKE) TARGET=arm 
	@./uploadToMk2.sh

