
#ifdef __THREADX__


#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "../../common/v2x_cli/v2x_cli.h"


/* registers functions */

unsigned int read_phy(int wlan_index, unsigned int address);
void write_phy(int wlan_index, unsigned int address, unsigned int value);
unsigned int read_mac(int wlan_index, unsigned int address);
void write_mac(int wlan_index, unsigned int address, unsigned int value);
unsigned int read_rf(int wlan_index, unsigned int address);
void write_rf(int wlan_index, unsigned int address, unsigned int value);






#define CCA_REGISTER 0x614
#define CCA_FW_CCA_REG (CCA_REGISTER / 4)
	
int cli_v2x_phy_cca_control_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )
{
  atlk_rc_t      	rc 					= ATLK_OK;
	int						 	cca_cycle 	= 50,
									if_index 		= -1,
									timeout  		= 5000,
									cca_stats	=	1, 
									rx_timeout	=	0,
									total_cycle = 10,
									org_cca_value = 0,
									i = 0;
									
	struct timeval start, current;
  
  /* get user context */
  //user_context *myctx = (user_context *) cli_get_context(cli);
  
	IS_HELP_ARG("hwregs cca -if_idx 1|2 -enable_cycle_percent 0-100 % [-timeout_ms (0-1e6)] [-total_cycle_ms 10000]");

	CHECK_NUM_ARGS /* make sure all parameter are there */
	
	GET_INT("-if_idx", if_index, i, "Specify interface index");
  if ( if_index < 1 || if_index > 2) {
    cli_print(cli, "ERROR : if_index is not optional and must be in range of 1-2");
    return CLI_ERROR;
  }
    
  for ( i = 0 ; i < argc; i += 2 ) {
    GET_INT("-enable_cycle_percent", cca_cycle, i, "Set the time the CCA is enable in cycle, parameter is precent");
    GET_INT("-timeout_ms", timeout, i, "Set time out for CCA loop ");
    GET_INT("-total_cycle_ms", total_cycle, i, "Total cycle time");
  } 
  
	cca_stats = read_phy( if_index , CCA_FW_CCA_REG);
	
	org_cca_value = cca_stats;
	
	/* bit 9	RW	MAC CCA debug mode enable.
			0 – Automatic mode
			1 – Debug mode (bit 10 value is being used as MAC CCA)	0
	*/
	cca_stats |= ( 1 << 9 );
	
	rx_timeout = 0;
	gettimeofday (&start, NULL);	
	
	/* Base cycle is */
	int sleep_time_uSec = ( (cca_cycle / 100.0) * (total_cycle * 10000 /* convert to uSec */ ) );
	int bit_state = 0;
		
	cli_print( cli, "Note : org_cca_value %x, cca_stats : %x, timeout  %d, sleep_time_uSec %d", (int) org_cca_value, (int) cca_stats, (int) timeout, (int) sleep_time_uSec );
	do {
		/* use cycles of 5ms */
		bit_state = !bit_state;
		
		gettimeofday (&current, NULL);
		if ( bit_state) {
			cca_stats |=  ( bit_state << 10 );
		}
		else {
			cca_stats &= ~( 1 << 10 );
		}
		
		cli_print( cli, "Setting phy CCA_FW_CCA_REG to 0x%x at %d, bit_state %d", (int) cca_stats, (int) current.tv_sec, bit_state ); 
		write_phy( if_index, CCA_FW_CCA_REG, cca_stats);
		usleep( sleep_time_uSec );
		
		double elapsedTime = (current.tv_sec - start.tv_sec) * 1000.0;
		if ( elapsedTime > timeout ) {
			rx_timeout = 1;
		}
		
	} while ( !rx_timeout );
	
	write_phy( if_index, CCA_FW_CCA_REG, org_cca_value);

  return rc;
}	



	
int cli_v2x_phy_cca_set( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )
{
	int						 	if_index 		= -1, i = 0, 
									enable	=	1, 
									cca_stats = 0;

  
  /* get user context */
  //user_context *myctx = (user_context *) cli_get_context(cli);
  
	IS_HELP_ARG("cca manual_set -if_idx 1|2 -enable 0|1");

	CHECK_NUM_ARGS /* make sure all parameter are there */
	
	GET_INT("-if_idx", if_index, i, "Specify interface index");
  if ( if_index < 1 || if_index > 2) {
    cli_print(cli, "ERROR : if_index is not optional and must be in range of 1-2");
    return CLI_ERROR;
  }
    
  for ( i = 0 ; i < argc; i += 2 ) {
    GET_INT("-enable", enable, i, "Set the time the CCA is enable");
  } 
  
	if_index -= 1;
	
	cca_stats = read_phy( if_index , CCA_FW_CCA_REG);
	
	if ( enable == 1 ) {
	
		cca_stats |= ( (1 << 9) | (1 << 10) );
		
	}
	else {
		cca_stats &= ~( 1 << 9 );
		cca_stats &= ~( 1 << 10 );
	}
	
	write_phy( if_index, CCA_FW_CCA_REG, cca_stats);
	
  return CLI_OK;
}	

/* 
 int cli_v2x_hwregs(struct cli_def *cli, int argc, char **argv)
 {
   unsigned int address, value;
   int read_iterations = 1;
   int wlan_index, device;
   int write;
   int i;
 
   if (argc < 1) {
     cli_print(cli, "bad command: not enough arguments");
     return CLI_ERROR_ARG;
   }
 
   switch (argv[0][0]) {
   case 'r':
     switch (argc) {
     case 4:
       break;
     case 5:
       sscanf(argv[4], "%d", &read_iterations);
       break;
     default:
       cli_print(cli, "bad command: not enough arguments");
       return CLI_ERROR_ARG;
     }
     write = 0;
     break;
   case 'w':
     if (argc != 5) {
       cli_print(cli, "bad command: not enough arguments");
       return CLI_ERROR_ARG;
     }
     write = 1;
     break;
   default:
     cli_print(cli, "bad command: unknown opcode");
     return CLI_ERROR_ARG;
   }
 
   sscanf(argv[2], "%d", &wlan_index);
   if ((wlan_index != 0) && (wlan_index != 1)) {
     cli_print(cli, "bad command: unknown wlan index");
     return CLI_ERROR_ARG;
   }
 
   device = argv[1][0];
 
   sscanf(argv[3], "%x", &address);
 
   if (write) {
     sscanf(argv[4], "%x", &value);
   }
 
   if (device == 'f') {
     struct wlan_device *wlan_dev;
     wlan_dev = wlan_device_get(wlan_index + 1);
     if (wlan_dev == NULL) {
       cli_print(cli, "bad command: wlan device not valid");
       return CLI_ERROR_ARG;
     }
   }
 
   if (write) {
     switch(device) {
     case 'm':
       write_mac(wlan_index, address, value);
       cli_print(cli, "0x%x", read_mac(wlan_index, address));
       return CLI_OK;
     case 'p':
       write_phy(wlan_index, address, value);
       cli_print(cli, "0x%x", read_phy(wlan_index, address));
       return CLI_OK;
     case 'f':
       write_rf(wlan_index, address, value);
       cli_print(cli, "0x%x", read_rf(wlan_index, address));
       return CLI_OK;
     default:
       cli_print(cli, "bad command: unknown device");
       return CLI_ERROR_ARG;
     }
   } else {
     for (i = 0; i < read_iterations; i++) {
       switch(device) {
       case 'm':
         cli_print(cli, "0x%x", read_mac(wlan_index, address));
         address += 4;
         break;
       case 'p':
         cli_print(cli, "0x%x", read_phy(wlan_index, address));
         address += 1;
         break;
       case 'f':
         cli_print(cli, "0x%x", read_rf(wlan_index, address));
         address += 1;
         break;
       default:
         cli_print(cli, "bad command: unknown device");
         return CLI_ERROR_ARG;
       }
     }
     return CLI_OK;
   }
 }
    
*/


#endif /* __THREADX__ */
