#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <string.h>
#include <sys/termios.h>
#include <pthread.h>

#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
     
#include "gps.h"

#define HEADER_MAX_SIZE 255

#define FIFO_FILE_PATH "/tmp/gpssim.fifo"

/*
  *TODO:* 
*/


static FILE       *gps_file         = NULL;
static int8_t     dev_name[256]     = "/dev/ttyAMA1";
static speed_t    dev_baud          = B115200;
static int32_t    serial_fd         = -1;

static int8_t     mode    = GPS_MODE_SIMULATOR;  

/* thread vars */
static pthread_t            thread;
static int8_t               thread_flag = 0;



int cli_v2x_gps_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  /* Open GPS file descriptor */
  int32_t i                     = 0;
  int8_t  gps_sim_mode[256]     = "";
  
  IS_HELP_ARG("gps start [-mode sim|override]");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  for ( i = 0 ; i < argc; i += 2 ) {
    GET_STRING("-mode", gps_sim_mode, i, "set gps nmea raw data");
  }
  
  gps_file = fopen(FIFO_FILE_PATH, "w+");
  if (!gps_file) {
    cli_print(cli,"ERROR : unable to open gps fd for writing, %s", FIFO_FILE_PATH );
    return CLI_ERROR;
  }
  
  mode = GPS_MODE_SIMULATOR;
  if ( strcmp( (char*) gps_sim_mode , "override") == 0 ) {
    mode = GPS_MODE_QUEUE;
  } 
 
  if  ( mode == GPS_MODE_QUEUE ) {
    int rc  = 0;
    /* activate the thread for  */
    thread_flag = 1;
    rc = pthread_create(&thread, NULL, (void*) &gps_rx_loop, (void*) cli);
    if ( rc != 0 ) {
      cli_print(cli,"ERROR : unable to activate gps rx loop" );
      return CLI_ERROR;
    }
    
  }
  
  return CLI_OK;
}

int cli_v2x_gps_stop( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
   
  if  ( mode == GPS_MODE_QUEUE ) {
    int rc = 0;
    thread_flag = 0;
    usleep(3000);
    rc = pthread_detach(thread);
    if ( rc != 0 ) {
      cli_print(cli,"ERROR : unable to deactivate gps rx loop" );
    }
    
  }
   
  if (gps_file) {
    fclose(gps_file);
    gps_file = NULL;
  }
  
  return CLI_OK;
}

/*
$GPGGA,153727.200,3217.1153,N,03452.3508,E,1,4,2.78,55.7,M,17.5,M,,*69
$GPGSA,A,3,13,07,10,08,,,,,,,,,2.95,2.78,14.34*3F
$GPRMC,153727.200,A,3217.1153,N,03452.3508,E,0.90,82.30,190212,4.0,E,A*30
$GPVTG,82.30,T,,M,0.90,N,1.67,K,A*0D
*/

int cli_v2x_gps_inject( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  int32_t   i                 = 0,
            rc                = CLI_OK;
  int8_t    gps_data[256] = {0};
  
  
  IS_HELP_ARG("gps inject [-nmea {gps nmea data}]");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  for ( i = 0 ; i < argc; i += 2 ) {
    GET_STRING("-nmea", gps_data, i, "set gps nmea injection data");
  }
  
  if ( (rc = gps_sim_write_fifo( cli, gps_file , (char*) gps_data )) != CLI_OK ) {
    cli_print(cli, "ERROR, failed to write GPS simulator file, error %d", rc);
    return CLI_ERROR;
  }
    
  return CLI_OK;
}

int gps_sim_write_fifo ( struct cli_def *cli, FILE *fifo , char *data )
{
 
  if ( !fifo ) {
    cli_print(cli, "ERROR : gps start command not activated" );
    return CLI_QUIT;
  } 
  
  if ( data == NULL ) {
    return CLI_ERROR;
  }

  fwrite(data, 1, strlen(data), fifo);
  fflush(fifo);
  
  return CLI_OK;
}

int cli_v2x_gps_config( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  int32_t   i                 = 0,
            baud              = 9600,
            rc                = CLI_OK;
  
  char      gps_baud_cmd[]    = "$PMTK251,115200*CS";
  FILE      *output_file      = NULL;
  
  if ( (argv[0] != NULL)  && (strcmp(argv[0], "?") == 0) ) {
    cli_print(cli, "usage : gps config [-device_name '/dev/ttyAMA1'] [-device_baud 1200 - 115200]" );
    return CLI_OK;
  }
  
  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  dev_baud = B9600;
  sprintf( (char*) dev_name , "%s" , "/dev/ttyAMA1" );
  for ( i = 0 ; i < argc; i += 2 ) {
    GET_STRING("-device_name", dev_name, i, "set OS device name for serial port");
    GET_INT("-device_baud", baud, i, "set OS device baud rate for serial port");
  }
  
  switch (baud) {
    case 2400:
      dev_baud = B2400; break;
    case 9600:
      dev_baud = B9600; break;
    case 19200:
      dev_baud = B19200; break;
    case 38400:
      dev_baud = B38400; break;
    case 57600:
      dev_baud = B57600; break;
    case 115200:
      dev_baud = B115200; break;
    case 576000:
      dev_baud = B576000; break;
    case 1152000:
      dev_baud = B1152000; break;
    case 4000000:
      dev_baud = B4000000; break;
    default:
      dev_baud = B9600;
      baud = 9600;
  }
  
  /* update gps unit 'FlexTrex' */
   if (FAILED(gps_init_input_interface( cli ))) {
    cli_print(cli,"ERROR : gps_init_input_interface failed, error code %d", rc);
  return CLI_ERROR;
  }
  
  output_file = fdopen(serial_fd, "rw");
  if (!output_file) {
    cli_print(cli,"ERROR : failed open gps serial port %s", dev_name);
    return CLI_ERROR;
  }
  
  if (( rc = fwrite( gps_baud_cmd , strlen(gps_baud_cmd), 1, output_file)) == 0) {
    cli_print(cli,"ERROR: Unable to update GPS parameter");
    return CLI_ERROR;
  }

  fclose(output_file);
  
  return CLI_OK;
}


int gps_init_input_interface( struct cli_def *cli )
{
  struct termios ttyset;
  int rc = 0;
  
  if ( strlen( (char*) dev_name) == 0 ) {
    cli_print(cli, "ERROR : device name for gps channel not set, please call gps set device first" );
    return CLI_ERROR;
  }
  
  if ((serial_fd = open( (char*)dev_name, (O_NOCTTY|O_RDWR))) < 0) {
    cli_print(cli, "device %s, open failed",(char*)dev_name);
    return serial_fd;
  }
  tcgetattr(serial_fd,&ttyset);
  ttyset.c_iflag &= ~(IGNBRK|BRKINT|ISTRIP|INLCR|IGNCR|ICRNL|IXON|PARMRK|INPCK);
  ttyset.c_oflag &= ~OPOST;
  ttyset.c_lflag &= ~(ECHO|ECHONL|ICANON|ISIG|IEXTEN);
  ttyset.c_cflag &= ~(CSIZE | CSTOPB | PARENB | PARODD);
  ttyset.c_cflag = CS8 | CREAD | CLOCAL; 
  
  if (FAILED(rc = cfsetispeed(&ttyset, dev_baud))) {
    cli_print(cli,"Failed setting input device ispeed");
    return rc;
  }
  if (FAILED(rc = cfsetospeed(&ttyset, dev_baud))) {
    cli_print(cli,"Failed setting input device ospeed");
    return rc;
  }
  
  if (FAILED(rc = tcsetattr(serial_fd, TCSANOW, &ttyset))) {
    cli_print(cli,"Failed setting input device TCSANOW");
    return rc;
  }
  if (FAILED(rc = tcflush(serial_fd, TCIOFLUSH))) {
    cli_print(cli,"Failed flushing input device");
    return rc;
  }
  return CLI_OK;
}



void gps_rx_loop( void *args)
{
  FILE    *input_file   = NULL;
  char  buffer[HEADER_MAX_SIZE + 1] = {0};

  struct cli_def *cli = args;
  
  if (FAILED(gps_init_input_interface( cli ))) {
    return;
  }
  
  input_file = fdopen(serial_fd, "rw");
  if (!input_file) {
    cli_print(cli,"ERROR : failed open gps serial port %s", dev_name);
    return;
  }

  while( thread_flag ) {
    
    int msg_len = CLI_OK;
    
    msg_len = get_line(input_file , buffer);
    
    if (msg_len <= CLI_OK) {
      usleep(200000);
    }
    else
    {
      cli_print(cli,"GPS : %s", buffer);
    }
  }
  
  fclose(input_file);
  
  return;
}



int get_line(FILE *fp , char *buffer )
{
  char nmea_line[HEADER_MAX_SIZE + 1] = {0},
         c  = 0;
         
  int32_t i = 0, rc = 0;
  
  if ( buffer == NULL ) {
    return CLI_ERROR;
  }
 
  if ( (rc = fread(&c, 1, 1, fp)) == 0 )  {
    return CLI_ERROR;
  }
  
  if (c != '$') { /* NMEA start header */
    return CLI_ERROR;
  }
  
  nmea_line[i++] = (char)c;
  while (c != '\n' && i < HEADER_MAX_SIZE) {
    if ( (rc = fread(&c, 1, 1, fp)) == 0 )  {
      return CLI_ERROR;
    }
    nmea_line[i++] = (char)c;
  }

  if (i == HEADER_MAX_SIZE) {
    return CLI_ERROR;
  }

  nmea_line[i-1] = 0;
  sprintf( buffer , "%s" ,  nmea_line );
  /* Print line */
  
  return i;
}