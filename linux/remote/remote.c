

#include <stdio.h>
#include "../../common/general/general.h"
#include "../../common/v2x_cli/v2x_cli.h"
#include <arpa/inet.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>

#include <atlk/remote.h>
#include <atlk/v2x_remote.h>



/* Remote transport  */
static remote_transport_t *transport = NULL;


remote_transport_t *get_active_cli_transport( void ) {
	return transport;
}



/* Network interface name */
#define NETWORK_INTERFACE_NAME "eth0"

int cli_create_transport( struct cli_def *cli, const char *command, char *argv[], int argc  ) 
{
	/* get user context */
	// user_context *myctx = (user_context *) cli_get_context(cli);
	atlk_rc_t rc = ATLK_OK;
	
	in_addr_t server_ip4_addr;
	  /* Local IPv4 address */
  uint32_t local_ipv4_addr;

	remote_ip_transport_config_t remote_config = REMOTE_IP_TRANSPORT_CONFIG_INIT;	
	char                  str_data[256] = "";

	(void) command;


  IS_HELP_ARG("remote transport create -ip_addr XX.XX.XX.XX [-timeout_ms 1000]");

  CHECK_NUM_ARGS /* make sure all parameter are there */

	remote_config.max_rtt_ms = 1000;


	GET_STRING("-ip_addr", str_data, 0, "Set ip addr "); 
	if ( (server_ip4_addr = inet_addr(str_data)) == INADDR_NONE) {
		cli_print( cli, "ERROR : %s is not valid ip addr", str_data );		
		return CLI_ERROR;	
	}

	if ( argc > 2 ) {
		GET_INT("-timeout_ms", remote_config.max_rtt_ms, 2, "Specify the number of frames to send");
	}
	
	  /* Get local IPv4 address */
  rc = remote_util_local_ipv4_address_get(NETWORK_INTERFACE_NAME , &local_ipv4_addr);
  if (atlk_error(rc)) {
    cli_print( cli , "remote_transport_local_ipv4_address_get: %s\n", atlk_rc_to_str(rc));
    return atlk_error(rc);
  }

  remote_config.local_ipv4_address = local_ipv4_addr;
	remote_config.remote_ipv4_address = server_ip4_addr;
	
	/* Create the transport objects */	
	rc = remote_ip_transport_create(&remote_config, &transport);
	if (atlk_error(rc)) { 	 
		cli_print ( cli, "ERROR : Failed to create transport : %s\n", atlk_rc_to_str(rc));		
		return atlk_error(rc);	
	}

	return CLI_OK;
}