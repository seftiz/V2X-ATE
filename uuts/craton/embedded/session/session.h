
#ifndef __ATE_V2X_CLI_SESSION_H__
#define __ATE_V2X_CLI_SESSION_H__

#include "../libcli/libcli.h"
#include "../v2x_cli/v2x_cli.h"
#include <atlk/v2x/wave.h>
int cli_v2x_session_open( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_session_close( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 


v2x_se_t *cli_v2x_get_session( int idx ); 


#endif


