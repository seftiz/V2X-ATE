#include <stdio.h>
#include <string.h>

#include "../regex.h"

void test_spencer_file(char * fname, int * test_count, int * test_pass);

int main(int argc, char ** argv)
{
	int test_count;
	int test_pass;
	test_spencer_file("spencer1.tests", &test_count, &test_pass);
	printf("TEST: %s: Count(%d) Passed(%d)\n", "spencer1.tests", test_count, test_pass);
	return 0;
}

void test_spencer_file(char * fname, int * test_count, int * test_pass)
{
	FILE * f;
	char line_buf[4096];
	int ret_code;
	char * expression;
	char * match_string;
	struct regex reg;

	*test_count = 0;
	*test_pass = 0;

	f = fopen(fname, "r");
	if ( !f ) {
		printf("Can't Load spencer1.tests\n");
		return;
	}
	// ret_code will be 0, 1, 3 
	// 0 = MATCHES
	// 1 = DOESN'T MATCH
	// 2 = ERROR COMPILEING
	while( fscanf(f, " %d%s", &ret_code, line_buf) ) {
		expression = strtok(line_buf, "@");
		match_string = strtok(NULL, "@");
		int match_result = 0;
		int compile_result = 0;
		(*test_count)++;
		//printf("Test(%d): %s\n", *test_count, expression);
		compile_result = regcomp(&reg, expression, REG_EXTENDED|REG_NOSUB);
		// If it doesn't compile and it shouldn't have
		if ( compile_result != REG_SUCCESS && ret_code == 2) {
			(*test_pass)++;
			printf("PASSED(%d): %d, %s, %s\n", *test_count, ret_code, expression, match_string);
			continue;
		}
		// If it doesn't compile and but it should have
		if ( compile_result != REG_SUCCESS && ret_code != 2)
		{
			printf("FAILED(%d): %d, %s, %s, %s\n", *test_count, ret_code, expression, match_string, "Compile Failed");
			continue;
		}
		// If it doesn't compile and the test file is crazy
		if ( compile_result != REG_SUCCESS )
		{
			printf("FAILED(%d): %d, %s, %s, %s\n", *test_count, ret_code, expression, match_string, "Compile Failed Skipping");
			continue;
		}
		match_result = regexec(&reg, match_string, 0, NULL, 0);
		if ( match_result  == REG_SUCCESS && ret_code == 0) {
			(*test_pass)++;
			printf("PASSED(%d): %d, %s, %s\n", *test_count, ret_code, expression, match_string);
			continue;
		}
		if ( match_result == REG_NOMATCH && ret_code == 1) {
			(*test_pass)++;
			printf("PASSED(%d): %d, %s, %s\n", *test_count, ret_code, expression, match_string);
			continue;
		}

		printf("FAILED(%d): %d, %s, %s\n", *test_count, ret_code, expression, match_string);
	}
}


