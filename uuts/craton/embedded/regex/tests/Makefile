

CFLAGS= -Wall -g
LDFLAGS= -g
CC=gcc

SPENCER_OBJS= ../regex.o test_spencer.o
PATFILES_OBJS= ../regex.o test_patfiles.o

all: test_spencer test_patfiles

test_spencer: $(SPENCER_OBJS)
	$(CC) $(LDFLAGS) $(SPENCER_OBJS) -o test_spencer 

test_patfiles: $(PATFILES_OBJS)
	$(CC) $(LDFLAGS) $(PATFILES_OBJS) -o test_patfiles

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

clean:
	-rm -f *.o test_spencer

