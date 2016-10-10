
#ifndef __ATE_V2X_CLI_NAV_API_H__
#define __ATE_V2X_CLI_NAV_API_H__

#include "../libcli/libcli.h"
#include "../v2x_cli/v2x_cli.h"
#include <atlk/nav.h>



#define FAILED(rc) ((rc) < 0)

typedef struct  {
    pthread_t            thread;
    int8_t               thread_flag;
    nav_se_t             se;
} nav_op_data_t;

int cli_v2x_nav_init( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 
int cli_v2x_nav_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 
int cli_v2x_nav_stop( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );

/* Internal */
void nav_rx_loop( void *args );
nav_rx_handler_rc_t nav_fix_handler(void *context, const nav_fix_t *fix);

#endif

