#ifndef __ATE_V2X_CLI_CAN_H__
#define __ATE_V2X_CLI_CAN_H__

#include <libcli.h>

#define DEFAULT_CAN_IF_INDEX        0


int cli_v2x_can_service_create( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_service_delete( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_socket_create( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_socket_delete( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_rx( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_tx( struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_tx_load( struct cli_def *cli, const char *command, char *argv[], int argc );

int cli_v2x_can_reset_cntrs(  struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_print_cntrs(  struct cli_def *cli, const char *command, char *argv[], int argc );
int cli_v2x_can_print_rx_rate( struct cli_def *cli, const char *command, char *argv[], int argc );


#endif
