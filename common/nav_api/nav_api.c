

#include "../v2x_cli/v2x_cli.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "nav_api.h"

/* declare float convert to str */
char *ftoa(char *outbuf, float f);

static int rx_loop = 0;


/* Navigation data session */
int cli_v2x_nav_init( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
  atlk_rc_t rc = ATLK_OK;
  char          str_data[256] = "local";
  int32_t       i             = 0;
  
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;
  
  IS_HELP_ARG("nav init -type local|remote [-server_addr ip_address]")
  CHECK_NUM_ARGS
 
  i = 0;
  GET_STRING("-type", str_data, i, "Specify session type, local or remote");
  
  if ( strcmp( (char*) str_data,  "local") == 0 ) {

		/* Get NAV current service - local*/ 
		myctx->nav_info.nav_service = NULL;
		rc = nav_default_service_get(&myctx->nav_info.nav_service);
		if (atlk_error(rc)) {
			cli_print( cli, "nav_local_service_get: %s", atlk_rc_to_str(rc));
			goto error;
		}
		if (myctx->nav_info.nav_service == NULL) {
			goto error;
		}
    /* Create nav subscriber */ 
    rc = nav_fix_subscriber_create(myctx->nav_info.nav_service, &myctx->nav_info.nav_hwd);
    if (atlk_error(rc)) {
      cli_print( cli, "nav_fix_subscriber_create: %s", atlk_rc_to_str(rc) );
      goto error;
    }
    
  } 
  else if ( strcmp( (char*) str_data, "remote") == 0 ) {
    cli_print( cli, "ERROR : Remote nav is not implemented");
  } 
  else {
    cli_print( cli, "ERROR : unknown mode of nav api");
  }
	
	return CLI_OK;
error:
  return atlk_error(rc);
}

#define NAV_THREAD_PRIO 10
#define NAV_THREAD_TIME_SLICE 50

int cli_v2x_nav_start( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
  //ULONG         trv;
  atlk_rc_t rc = ATLK_OK;
  nav_fix_t nav_fix = NAV_FIX_INIT;

  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;
  (void) argv;
  (void) argc;
  
	myctx->nav_info.loop_flag = 1;
   
  while (myctx->nav_info.loop_flag) {
    
    // Receive new navigation fix, if any
    rc = nav_fix_receive( myctx->nav_info.nav_hwd, &nav_fix, NULL);
    if (atlk_error(rc) && (rc != ATLK_E_NOT_READY)) {
      cli_print(cli,"nav_se_fix_rx: %s\n", atlk_rc_to_str(rc));
    }
    else if ( rc == ATLK_E_NOT_READY ) {
      usleep(1e5); /* Sleep 100 mSec */
    }
    else {
      print_nav_fix_data( cli, &nav_fix );
    }
    usleep(1e4); /* Sleep 10 mSec */
  }

  return CLI_OK;
}

int cli_v2x_nav_stop( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;
  (void) argv;
  (void) argc;
  (void) myctx;
	
  rx_loop = 0;
	myctx->nav_info.loop_flag = 0;

  return CLI_OK;
}


void print_nav_fix_data( void *context, const nav_fix_t *fix)
{
  
  struct cli_def *cli     = (struct cli_def *) context;
  char  line[400]         = "";
  double posix_time       = 0.0;
  
  posix_time = nav_time_to_posix_time (&fix->time);
  /* Use navigation fix */
  sprintf(line , "%f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\n", posix_time, 
                fix->position_latitude_deg,
                fix->position_longitude_deg,
                fix->position_altitude_m,
                fix->movement_horizontal_direction_deg,
                fix->movement_horizontal_speed_mps,
                fix->movement_vertical_speed_mps,
                fix->error_time_s,
                fix->error_position_horizontal_major_axis_direction_deg,
                fix->error_position_horizontal_semi_major_axis_length_m,
                fix->error_position_horizontal_semi_minor_axis_length_m,
                fix->error_position_altitude_m,
                fix->error_movement_horizontal_direction_deg,
                fix->error_movement_horizontal_speed_mps,
                fix->error_movement_vertical_speed_mps);
  
  cli_print(cli, "%s", line);
}


/*
int create_udp_client( struct cli_def *cli, char *server_ip , int port, int *socket )
{
  struct sockaddr_in si_other;
  int s, i, slen=sizeof(si_other);

  if ( (s=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP))== -1 ) {
    cli_print(cli,"nav_se_fix_rx: %s\n", atlk_rc_to_str(rc));
		return CLI_ERROR;
	}

  memset( (char *) &si_other, 0, sizeof(si_other));
  si_other.sin_family = AF_INET;
  si_other.sin_port = htons(port);
  if (inet_aton(server_ip, &si_other.sin_addr)==0) {
    cli_print(cli, "inet_aton() failed\n");
    return CLI_ERROR;
  }
	
	return CLI_OK;
}

int send_udp_data ( int socket, 

  for (i=0; i<NPACK; i++) {
    printf("Sending packet %d\n", i);
    sprintf(buf, "This is packet %d\n", i);
    if (sendto( s, buf, BUFLEN, 0, &si_other, slen)==-1)
      diep("sendto()");
  }

  close(s);
  return CLI_OK;
}
*/
