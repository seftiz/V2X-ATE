
#ifndef __ATE_V2X_CLI_GPS_H__
#define __ATE_V2X_CLI_GPS_H__

#include "../libcli/libcli.h"
#include "../v2x_cli/v2x_cli.h"
#include <atlk/v2x/wave.h>


enum {
  GPS_MODE_SIMULATOR  = 0,
  GPS_MODE_QUEUE      = 1
 
};


#define FAILED(rc) ((rc) < 0)

int cli_v2x_gps_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 
int cli_v2x_gps_stop( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 
int cli_v2x_gps_inject( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_gps_config( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ); 

/* Internal */
int gps_sim_write_fifo ( struct cli_def *cli, FILE *fifo , char *data );
int gps_init_input_interface( struct cli_def *cli );
int get_line(FILE *fp , char *buffer );
void gps_rx_loop( void *args);

#endif


