
#ifndef __ATE_V2X_CLI_NAV_API_H__
#define __ATE_V2X_CLI_NAV_API_H__

#include <libcli.h>
#include "../v2x_cli/v2x_cli.h"


#define FAILED(rc) ((rc) < 0)



int cli_v2x_nav_init( struct cli_def *cli, const char *command, char *argv[], int argc ); 
int cli_v2x_nav_start( struct cli_def *cli, const char *command, char *argv[], int argc ); 
int cli_v2x_nav_stop( struct cli_def *cli, const char *command, char *argv[], int argc );

/* Internal */
// void nav_rx_loop( ULONG args );
void print_nav_fix_data( void *context, const nav_fix_t *fix);


#endif

