#ifndef __ATE_V2X_CLI_LINK_H__
#define __ATE_V2X_CLI_LINK_H__


#include "../../linux/libcli/libcli.h"


int cli_v2x_link_socket_create( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_link_socket_delete( struct cli_def *cli, const char *command, char *argv[], int argc );


int cli_v2x_link_service_create( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_link_service_delete( struct cli_def *cli, const char *command, char *argv[], int argc );

int cli_v2x_link_tx( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_link_rx( struct cli_def *cli, const char *command, char *argv[], int argc );

int cli_v2x_link_reset_cntrs( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_link_print_cntrs( struct cli_def *cli, const char *command, char *argv[], int argc );

int cli_v2x_get_link_socket_addr( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_set_link_socket_addr( struct cli_def *cli, const char *command, char *argv[], int argc );

#endif /* __ATE_V2X_CLI_LINK_H__ */