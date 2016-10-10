#ifndef __V2X_CPU_LOAD_H__
#define __V2X_CPU_LOAD_H__


int cli_v2x_cpu_load_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_set_thread_name( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );

int cli_v2x_thread_kill( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_thread_resume( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_thread_suspend( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 




#endif