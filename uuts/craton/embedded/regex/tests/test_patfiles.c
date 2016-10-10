#include <stdio.h>
#include <string.h>

#include "../regex.h"

void test_pat_file(char * fname);

// Test the second line of every file passed on command line
int main(int argc, char ** argv)
{
	char linebuf[4096];
	argc--;
	while (argc)
	{
		struct regex reg;
		FILE * f = fopen(argv[argc], "r");
		printf("Compiling File: %s\n", argv[argc]);
		fgets(linebuf, 4095, f);
		fgets(linebuf, 4095, f);
		linebuf[strlen(linebuf) - 1] = '\0';
		if ( regcomp(&reg, linebuf, REG_EXTENDED|REG_NOSUB) != REG_SUCCESS)
		{
			printf("FAILED TO COMPILE(%s): %s\n", argv[argc], linebuf);
		}
		else
		{
			printf("COMPILED(%s): %s\n", argv[argc], linebuf);
		}
		argc--;
		
	}
	return 0;
}


