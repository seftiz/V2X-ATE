#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <pthread.h>

#include "../libcli/libcli.h"
#include "../v2x_cli/v2x_cli.h"
#include "nav_api.h"


/* declare float convert to str */
char *ftoa(char *outbuf, float f);

/* Navigation data session */


int cli_v2x_nav_init( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  atlk_rc_t rc = ATLK_OK;
  /* Navigation data session attributes */
  nav_se_attr_t se_attr     = NAV_SE_ATTR_INIT;
  char        str_data[256] = "";
  int32_t     i             = 0;
  nav_op_data_t nav_op;
  
  
  IS_HELP_ARG("nav init -type local|remote [-server_addr ip_address]")
  
  CHECK_NUM_ARGS
 
  i = 0;
  GET_STRING("-type", str_data, i, "Specify session type, local or remote");
  
  if ( strcmp( (char*) str_data,  "local") == 0 ) {
    se_attr.se_type = NAV_SE_LOCAL;
  } 
  else if ( strcmp( (char*) str_data, "remote") == 0 ) {
    in_addr_t addr;
     
    i+=2;
    se_attr.se_type = NAV_SE_IP4_TCP_GPSD_JSON;
    memset ( &str_data , 0 ,sizeof(str_data) );
    GET_STRING("-server_addr", str_data, i, "Remote ip address ");
    addr = inet_addr(str_data);
    if (addr == INADDR_NONE) {
      cli_print(cli,"\"%s\" is not a valid IPv4 address\n", str_data);
      return (EXIT_FAILURE);
    }
    se_attr.server_ip4_addr = addr;
  }
  else {
    se_attr.se_type = NAV_SE_LOCAL;
  }
  
  /* Open navigation data session */
  //nav_op = malloc( sizeof(nav_op_data_t) );
  memset( &nav_op, 0 , sizeof(nav_op_data_t) );
  nav_op.se = NAV_SE_INIT;

  rc = nav_se_open( &(nav_op.se), &se_attr);
  if (atlk_error(rc)) {
    cli_print(cli, "nav_se_open failed (%s)\n", atlk_rc_to_str(rc) );
    goto exit;
  }
  
  cli_set_context( cli, (void*) &nav_op);
 
exit:
  return atlk_error(rc);
}

void nav_rx_loop( void *args )
{
  /* Navigation fix handling loop */
  atlk_rc_t rc = ATLK_OK;
  struct cli_def *cli = args;
  /* Navigation fix rx loop timeout: 1 sec */
  const struct timeval timeout = { .tv_sec = 1, .tv_usec = 0 };
  
  nav_op_data_t *nav_op = (nav_op_data_t*) cli_get_context(cli);

  
  rc = nav_fix_rx_loop(&(nav_op->se), nav_fix_handler, (void*) cli, &timeout );
  if (atlk_error(rc)) {
     cli_print(cli, "ERROR: nav_fix_rx_loop, id:%s\n", atlk_rc_to_str(rc));
  }

  /* Cleanup */
  rc = nav_se_close(&(nav_op->se));
  if (atlk_error(rc)) {
    cli_print(cli, "ERROR: nav_se_close, id:%s\n", atlk_rc_to_str(rc));
  }
  
  return;
}



void print_double(const char *label, double value)
{
  uint32_t integer = (uint32_t)value;
  uint32_t fraction = (uint32_t)(1e6 * (value - integer));
  const char *sign = (value < 0) ? "-" : "";
  printf("%s: %s%u.%06u\n", label, sign, integer, fraction);
}


#define FORMAT_FIELD_TO_LINE(_field_)\
  {\
    char fstr[50] = "";         \
    if (!isnan(_field_)) {      \
      ftoa(fstr, _field_);      \
      strcat( line, fstr);      \
      strcat(line, ",");        \
    }                           \
    else {                      \
      strcat( line, "Nan"); strcat(line, ",");\
    }\
  }

nav_rx_handler_rc_t nav_fix_handler(void *context, const nav_fix_t *fix)
{
  
  struct cli_def *cli     = (struct cli_def *) context;
  nav_op_data_t *nav_op   = (nav_op_data_t*) cli_get_context(cli);
  char  line[400]       = "";
  double posix_time     = 0.0;
  
  posix_time = fix->time.tai_seconds_since_2004 - (double)fix->time.leap_seconds_since_2004 + 1072915200.0;

  uint32_t integer = (uint32_t) posix_time;
  uint32_t fraction = (uint32_t) ( 1000000 * (posix_time - integer) );
  /* Use navigation fix */
 
  
  
  sprintf(line , "%u.%06d,", integer, fraction);
  FORMAT_FIELD_TO_LINE(fix->position_latitude_deg);
  FORMAT_FIELD_TO_LINE(fix->position_longitude_deg);
  FORMAT_FIELD_TO_LINE(fix->position_altitude_m);
  FORMAT_FIELD_TO_LINE(fix->movement_horizontal_direction_deg);
  FORMAT_FIELD_TO_LINE(fix->movement_horizontal_speed_mps);
  FORMAT_FIELD_TO_LINE(fix->movement_vertical_speed_mps);
  FORMAT_FIELD_TO_LINE(fix->error_time_s);
  FORMAT_FIELD_TO_LINE(fix->error_position_horizontal_major_axis_direction_deg);
  FORMAT_FIELD_TO_LINE(fix->error_position_horizontal_semi_major_axis_length_m);
  FORMAT_FIELD_TO_LINE(fix->error_position_horizontal_semi_minor_axis_length_m);
  FORMAT_FIELD_TO_LINE(fix->error_position_altitude_m);
  FORMAT_FIELD_TO_LINE(fix->error_movement_horizontal_direction_deg);
  FORMAT_FIELD_TO_LINE(fix->error_movement_horizontal_speed_mps);
  FORMAT_FIELD_TO_LINE(fix->error_movement_vertical_speed_mps);

  /*

  ftoa(fstr, fix->position_latitude_deg); strcat( line, fstr); strcat(line, ",");
  ftoa(fstr, fix->position_longitude_deg); strcat( line, fstr); strcat(line, ",");
  ftoa(fstr, fix->position_altitude_m); strcat( line, fstr); strcat(line, ",");
  ftoa(fstr, fix->movement_horizontal_direction_deg); strcat( line, fstr); strcat(line, ",");
  ftoa(fstr, fix->movement_horizontal_speed_mps); strcat( line, fstr); strcat(line, ",");
  ftoa(fstr, fix->movement_vertical_speed_mps); strcat( line, fstr);

  */  
  cli_print(cli, "%s", line);
    
  return !(nav_op->thread_flag);
}

int cli_v2x_nav_start( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
  int           rc      = 0;
  nav_op_data_t *nav_op = (nav_op_data_t*) cli_get_context(cli);
  

  nav_op->thread_flag = 1;
  rc = pthread_create(&nav_op->thread, NULL, (void*) &nav_rx_loop, (void*) cli);
  if ( rc != 0 ) {
    cli_print(cli,"ERROR: unable to activate gps rx loop, id:%u", rc );
    return CLI_ERROR;
  }
  return CLI_OK;

}

int cli_v2x_nav_stop( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
    nav_op_data_t *nav_op = (nav_op_data_t*) cli_get_context(cli);
    
    nav_op->thread_flag = 0;
    //usleep(3000);
    //rc = pthread_detach(thread);
    //if ( rc != 0 ) {
    //  cli_print(cli,"ERROR : unable to deactivate gps rx loop" );
    //}
    return CLI_OK;
}
