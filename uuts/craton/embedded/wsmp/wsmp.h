#ifndef __ATE_V2X_CLI_WSMP_H__
#define __ATE_V2X_CLI_WSMP_H__




#include "../libcli/libcli.h"

int cli_v2x_wsmp_sk_open( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_wsmp_sk_close( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_wsmp_send_frame( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );


#endif /* __ATE_V2X_CLI_WSMP_H__ */