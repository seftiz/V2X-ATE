
#ifndef __REMOTE_H__
#define __REMOTE_H__

#include <atlk/remote.h>

int cli_create_transport( struct cli_def *cli, const char *command, char *argv[], int argc );
remote_transport_t *get_active_cli_transport( void );

#endif


