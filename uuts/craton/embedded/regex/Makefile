
OBJS= regex.o test.o

CFLAGS= -Wall
LDFLAGS=
CC= gcc
AR= ar
RANLIB= ranlib

ifeq ($(DEBUG), 1)
CFLAGS+= -g -DDEBUG
else
CFLAGS+= -O2
endif

all: regex.o

lib: regex.o
	$(AR) r libregex.a $<
	$(RANLIB) libregex.a
	
%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

clean:
	-rm -f *.o libregex.a

