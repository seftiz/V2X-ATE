#include "../../common/general/general.h"
#include "../../common/v2x_cli/v2x_cli.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <atlk/can.h>
#include "can.h"

/* CAN service */
static can_service_t *can_service = NULL;

static unsigned int 	m_can_rx_packets = 0;
static unsigned int 	m_can_tx_packets = 0;


/* CAN bus service init */
int cli_v2x_can_service_create( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
  atlk_rc_t 		rc 						= ATLK_OK;
  char          str_data[256] = "hw";
  int32_t       i             = 0;
  
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) myctx; /* not used  */
  (void) command;

  IS_HELP_ARG("can service create -type hw|remote [-server_addr ip_address]")
  CHECK_NUM_ARGS
  GET_STRING("-type", str_data, i, "Specify service type, local or remote");

  if (can_service != NULL) {
	  cli_print(cli, "INFO : CAN service is already up");
	  return CLI_OK;
  }

  if ( strcmp( (char*) str_data,  "hw") == 0 ) {

		/* Get CAN service instance */
	  rc = can_default_service_get(&can_service);
	  if (atlk_error(rc)) {
		  cli_print(cli, "can_default_service_get: %s\n", atlk_rc_to_str(rc));
		  goto error;
		}
  } 
  else if ( strcmp( (char*) str_data, "remote") == 0 ) {
    cli_print( cli, "ERROR : Remote can is not implemented");
  } 
  else {
    cli_print( cli, "ERROR : unknown mode of can api");
  }
	
	return CLI_OK;
	
error:
  return atlk_error(rc);
}

int cli_v2x_can_service_delete( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
	/* get user context */
	user_context *myctx = (user_context *) cli_get_context(cli);
	(void) myctx; /* not used  */
  (void) command;
  (void) argv;
  (void) argc;

	IS_HELP_ARG("can service delete")

  can_service_delete(can_service);
  can_service = NULL;

	return CLI_OK;
}

/* CAN bus service init */
int cli_v2x_can_socket_create( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
  atlk_rc_t 	rc = ATLK_OK;
  int32_t		  i = 0,
				      filter_count	= 0;
  int 			  filter_idx;
  int 			  filter_start = 0;
  int			    device_id = -1;

	/* get user context */
	user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;

	if (myctx->can_info.can_socket != NULL) {
		cli_print(cli, "ERROR : can_socket_create - socket was already opened for device_id 0x%x", myctx->can_info.can_params.device_id);
		return CLI_ERROR;
	}

	IS_HELP_ARG("can socket create [ -device_id 0|1|0xFFU ] -filter_count 0|N [can_id_1 0x1 can_id_mask_1 0xFFFFFFFFU .... can_id_N 0x1 can_id_mask_N 0xFFFFFFFFU]")
	CHECK_NUM_ARGS

//  myctx->can_info.can_params.device_id = CAN_DEVICE_ID_NA;
	myctx->can_info.can_params.filter_array_ptr = NULL;
	
			//CAN_SOCKET_CREATE_PARAMS_INIT;

	GET_HEX("-device_id", device_id, 0, "Specify can device id");
	if (device_id == -1) {
		myctx->can_info.can_params.device_id = (can_device_id_t) CAN_DEVICE_ID_NA;
		cli_print(cli, "DEBUG : Processed parameter device_id, using default value 0x%x", CAN_DEVICE_ID_NA); \
	}
	else {
		myctx->can_info.can_params.device_id = (can_device_id_t) device_id;
		filter_start = 2;
	}


	GET_INT("-filter_count", filter_count, filter_start, "Specify filter fields");
	if ( filter_count != (argc-(2+filter_start)) ) {
		cli_print(cli, "ERROR : Mismatch count of filter, count %d, number of filter args is %d", (int)filter_count, (argc - (2 + filter_start)));
		goto error;
	}
	
	if ( filter_count > 0 ) {
		myctx->can_info.can_params.filter_array_size = filter_count;
		myctx->can_info.filter_array = calloc(filter_count, sizeof(can_id_filter_t));
  
		for ( i=2,filter_idx=0 ; i < argc; i += 2, filter_idx++ ) {

      char 	filter_can_name[20] = "",
            filter_can_mask_name[20] = "";

			sprintf(filter_can_name, "-can_id_%d", filter_idx+1);
			sprintf(filter_can_mask_name, "-can_id_mask_%d", filter_idx+1);
						
			/* CAN_ID_FILTER_ONE_ID */
			
			GET_TYPE_INT(filter_can_name, myctx->can_info.filter_array[filter_idx].can_id, unsigned int, i, "Specify the number of frames to send", "%x");
			GET_TYPE_INT(filter_can_mask_name, myctx->can_info.filter_array[filter_idx].can_id_mask, unsigned int, i, "Specify the number of frames to send", "%x");
		} 
	}
	else {
		/* Initilize no filter */
		myctx->can_info.can_params.filter_array_size = 1;
		myctx->can_info.filter_array = calloc(myctx->can_info.can_params.filter_array_size, sizeof(can_id_filter_t));
		myctx->can_info.filter_array[0].can_id = 0;
		myctx->can_info.filter_array[0].can_id_mask = 0;
	}
	
	myctx->can_info.can_params.filter_array_ptr = myctx->can_info.filter_array;
	if (myctx->can_info.can_params.filter_array_ptr == NULL) {
		cli_print( cli, "ERROR : filter_array not initilized properly" );
		goto error;
	}
	
	/* Create CAN socket */
	rc = can_socket_create(can_service, &myctx->can_info.can_socket, &myctx->can_info.can_params);
	if (atlk_error(rc)) {
		cli_print( cli, "ERROR : can_socket_create: %s\n", atlk_rc_to_str(rc));
		goto error;
	}

	return CLI_OK;
	
error:
  return atlk_error(rc);
}


/* CAN bus service init */
int cli_v2x_can_socket_delete( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
	/* get user context */
	user_context *myctx = (user_context *)cli_get_context(cli);
	(void) command;
  (void) argv;
  (void) argc;


	IS_HELP_ARG("can socket delete")
	
 
		if (myctx->can_info.filter_array != NULL) {
			free(myctx->can_info.filter_array);
			myctx->can_info.filter_array = NULL;
	}
  
	if (myctx->can_info.can_socket != NULL) {
		can_socket_delete(myctx->can_info.can_socket);
		myctx->can_info.can_socket = NULL;
	}

	
	return CLI_OK;
}

int cli_v2x_can_rx( struct cli_def *cli, const char *command, char *argv[], int argc )
{
	atlk_rc_t   rc			= ATLK_OK;
	int32_t     frames   	= 1,
					    i        	= 0,
					    print_frms	=	0,
              timeout_msec = -1;
	uint8_t 	  data[CAN_DATA_SIZE_MAX];
	size_t 		  data_size = sizeof(data);
	can_id_t 	  can_id = 0;
	ULONG			  start_time = 0, cur_time = 0;
  atlk_wait_t atlk_wait = atlk_wait_forever;


	/* get user context */
	user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;


	IS_HELP_ARG("can socket rx [-frames 1- ...] [-print (0|1)] [-timeout_ms (0-1e6)]");
	CHECK_NUM_ARGS /* make sure all parameter are there */
    
	for ( i = 0 ; i < argc; i += 2 ) {
		GET_INT("-frames", frames, i, "Specify the number of can frames to receive");
    GET_INT("-print", print_frms, i, "Set frames printing");
    GET_INT("-timeout_ms", timeout_msec, i, "Set timeout in msec");
  }

  if (timeout_msec != -1) {
    atlk_wait.wait_type = ATLK_WAIT_INTERVAL;
    atlk_wait.wait_usec = timeout_msec * 1000;
  }

	start_time = tx_time_get();

	i = 0;
	while (i < frames) {
		memset( data, 0, sizeof(data) );
    rc = can_receive(myctx->can_info.can_socket, data, &data_size, &can_id, &atlk_wait);
    if (rc == ATLK_E_NOT_READY){
      cli_print(cli, "can_receive: return with timeout, no frames was received for %d msec.", (int) timeout_msec);
      return atlk_error(rc);
    }

    if (atlk_error(rc)) {
			cli_print(cli, "can_receive: %s", atlk_rc_to_str(rc));
			continue;
		}
    
		i++;
    myctx->cntrs.can_rx_packets ++;
		m_can_rx_packets ++;

		if ( print_frms ) {
			cli_print( cli, "TIME : %u, CAN RX %d : ID = 0x%x, DLC = %d, Data[0:7] = 0x%02x, 0x%02x, 0x%02x, 0x%02x, 0x%02x, 0x%02x, 0x%02x, 0x%02x", 
                (unsigned int) tx_time_get(), (int) i, (unsigned int)can_id, (int) data_size, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]);
		}
	}

	if (frames > 1) {
		cur_time = tx_time_get();
		double elapsed_time = (cur_time - start_time) / 1000;
		myctx->cntrs.can_rx_frames_rate = (int32_t) frames / elapsed_time;

    printf("Received %d frames in average rate of %d frames per second, elapsed_time=%d\n", (int)frames, (int)myctx->cntrs.can_rx_frames_rate, (int)elapsed_time);
	}

	return atlk_error(rc);
}

int cli_v2x_can_tx( struct cli_def *cli, const char *command, char *argv[], int argc )
{
	int32_t     num_frames 		= 1;     /* total num frames to send */
	int32_t     rate_hz 		= 0;     /* rate of sending frames, 0 Max speed   */
	int32_t     data_size		= 0; 
	can_id_t	  can_id			= 0x50;
								
	size_t		  msg_size = 0;
	char        can_data[CAN_DATA_SIZE_MAX * 2 + 1] = { 0 },
				      hex_arr[CAN_DATA_SIZE_MAX + 2] = { 0 };
                
	atlk_rc_t   rc = ATLK_OK;
	int			    i;
  
	ULONG		    start_time = 0, cur_time = 0;

	/* get user context */
	user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;


	IS_HELP_ARG("can socket tx [-frames 1- ...] [-rate_hz 1 - ...] [-can_id 0x1 -can_data '000102030405' | -data_size 8]");

	CHECK_NUM_ARGS /* make sure all parameter are there */
    
	for ( i = 0 ; i < argc; i += 2 ) {
		GET_INT("-frames", num_frames, i, "Specify the number of frames to send");
		GET_INT("-rate_hz", rate_hz, i, "Specify the rate of frames to send");
		GET_INT("-data_size", data_size, i, "Sets the payload length instead of tx data parameter");
		GET_HEX("-can_id", can_id, i, "Specify the can id of frame");
	} 
   
	GET_STRING_VALUE("-can_data", can_data,"Define data to send over the link layer");

  msg_size = (size_t)(strlen(can_data) / 2);
  rc = hexstr_to_bytes_arr(can_data, strlen(can_data), (uint8_t*)hex_arr, &msg_size);
  if (atlk_error(rc)) {
    cli_print(cli, "ERROR : cli_v2x_can_tx - cannot convert hexstr to buffer, error= %s\n", atlk_rc_to_str(rc));
    goto error;
  }

  //cli_print(cli, "DEBUG : can_send - id=0x%x, dlc=%d, data=%s", (int)can_id, (int)data_size, can_data); 

  for (i = 0; i < num_frames; i++) {
		start_time = tx_time_get();
		rc = can_send(myctx->can_info.can_socket, hex_arr, data_size, can_id, NULL);
		if (atlk_error(rc)) {
			cli_print(cli, "ERROR : can_send: %s\n", atlk_rc_to_str(rc));
			goto error;
		}
		else {

			myctx->cntrs.can_tx_packets++;
			m_can_tx_packets++;

			/* Calc blocking time for can send */
			cur_time = tx_time_get();
			ULONG elapsedTime = cur_time - start_time;

			/* Sleep between transmissions 1000/rate_hz msec*/
			if ((num_frames >= 1) && (rate_hz >= 1)){
				int sleep_time_mSec = ((1000 - elapsedTime) / rate_hz);
				if (sleep_time_mSec > 0)
					tx_thread_sleep(sleep_time_mSec);
			}
		}
	}

error:
	return rc;
}

int cli_v2x_can_tx_load(struct cli_def *cli, const char *command, char *argv[], int argc)
{
	int32_t     num_frames = 10000;     /* total num frames to send */
	int32_t     rate_hz = 0;     /* rate of sending frames, 0 Max speed */
	int32_t     err_part = 0,     /* part of erroneous frames in percentages */
				      err_cycle = 0;
	can_id_t	  can_id = 0x100;
	size_t		  data_size = 0;
	char        can_data1[CAN_DATA_SIZE_MAX * 2 + 1] = "5555555555555555", /* '01010101010...'*/
			        can_data2[CAN_DATA_SIZE_MAX * 2 + 1] = "AAAAAAAAAAAAAAAA", /* '10101010101...'*/
				      hex_arr[CAN_DATA_SIZE_MAX + 2] = { 0 };

	atlk_rc_t   rc = ATLK_OK;
	int			    i = 0;
	ULONG		    start_time = 0, cur_time = 0, err_tx = 0;

//	struct timeval start, current;

	/* get user context */
	user_context *myctx = (user_context *)cli_get_context(cli);
  (void) command;
 
	IS_HELP_ARG("can socket tx load [-frames 10000- ...] [-rate_hz 0 - ...] [-err_part 0 - ...]");

	CHECK_NUM_ARGS /* make sure all parameter are there */

	for (i = 0; i < argc; i += 2) {
		GET_INT("-frames", num_frames, i, "Specify the number of frames to send");
		GET_INT("-rate_hz", rate_hz, i, "Specify the rate of frames to send");
		GET_INT("-err_part", err_part, i, "Specify the part of the erroneous frames");
	}

	if (err_part != 0)
		err_cycle = 100 / err_part;

	for (i = 0; i < num_frames; i++) {
		
		start_time = tx_time_get();
		data_size = i % 9;

		if (i % 2) {
			can_id = 0x100; /* Standard CAN id */
      rc = hexstr_to_bytes_arr(can_data1, data_size*2, (uint8_t*)hex_arr, &data_size);
      if (atlk_error(rc)) {
        cli_print(cli, "ERROR : cli_v2x_can_tx_load - cannot convert hexstr to buffer, error= %s\n", atlk_rc_to_str(rc));
        // goto error;
        continue;
      }
    }
		else {
			can_id = 0x100 | (1 << CAN_ID_EXTENDED_BIT); /* Extended CAN id */
      rc = hexstr_to_bytes_arr(can_data2, data_size*2, (uint8_t*)hex_arr, &data_size);
      if (atlk_error(rc)) {
        cli_print(cli, "ERROR : cli_v2x_can_tx_load - cannot convert hexstr to buffer, error= %s\n", atlk_rc_to_str(rc));
				continue;
        // goto error;
      }
    }

		if (err_cycle && (i % err_cycle == 0)) {
			/* Send error message */
			rc = can_send(myctx->can_info.can_socket, hex_arr, -2, can_id, NULL);
		}
		else {
			/*
			cli_print(cli, "DEBUG : can_send No.=%d - id=0x%x, dlc=%d, data=0x%x 0x%x 0x%x 0x%x 0x%x 0x%x 0x%x 0x%x", i, (int)can_id, (int)data_size, 
							    hex_arr[0], hex_arr[1], hex_arr[2], hex_arr[3], hex_arr[4], hex_arr[5], hex_arr[6], hex_arr[7]);
			*/
			rc = can_send(myctx->can_info.can_socket, hex_arr, data_size, can_id, NULL);
			if (atlk_error(rc)) {
				cli_print(cli, "ERROR : can_send (Frame No. %d): %s\n", (int)i, atlk_rc_to_str(rc));
				err_tx ++;
				// goto error;
				continue;
		  }

			myctx->cntrs.can_tx_packets++;
			m_can_tx_packets++;
    }

		/* Calc blocking time for can send */
		cur_time = tx_time_get();
		ULONG elapsedTime = cur_time - start_time;
		/* Sleep between transmissions 1000/rate_hz msec*/
		if ((num_frames >= 1) && (rate_hz >= 1)){
			int sleep_time_mSec = ((1000 - elapsedTime) / rate_hz);
			if (sleep_time_mSec > 0)
				tx_thread_sleep(sleep_time_mSec);
    }
	}

//error:

	printf("Send %d frames, with %u errors.\n", (int) i, (unsigned int) err_tx );
	cli_print(cli, "DEBUG : can_send repeated for %d frames", (int) i);

	return rc;
}

int cli_v2x_can_reset_cntrs( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
	/* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;
  (void) argv;
  (void) argc;


	myctx->cntrs.can_rx_packets = 0;
	myctx->cntrs.can_tx_packets = 0;
	m_can_rx_packets = 0;
	m_can_tx_packets = 0;
	myctx->cntrs.can_rx_frames_rate = 0;

	return ATLK_OK;
}

int cli_v2x_can_print_cntrs( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
 /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) command;
  (void) argv;
  (void) argc;

	cli_print(cli, "TX : module = %u, session = %u", m_can_tx_packets, myctx->cntrs.can_tx_packets ); 
	cli_print(cli, "RX : module = %u, session = %u", m_can_rx_packets, myctx->cntrs.can_rx_packets );

	printf("TX : module = %u, session = %u\n", m_can_tx_packets, myctx->cntrs.can_tx_packets);
	printf("RX : module = %u, session = %u\n", m_can_rx_packets, myctx->cntrs.can_rx_packets);


	return ATLK_OK;
}

int cli_v2x_can_print_rx_rate(struct cli_def *cli, const char *command, char *argv[], int argc)
{
	/* get user context */
	user_context *myctx = (user_context *)cli_get_context(cli);
  (void) command;
  (void) argv;
  (void) argc;

	cli_print(cli, "RX average frames rate = %u", myctx->cntrs.can_rx_frames_rate);
	printf("RX average frames rate = %u\n", myctx->cntrs.can_rx_frames_rate);

	return ATLK_OK;
}

int cli_v2x_get_can_socket_addr(struct cli_def *cli, const char *command, char *argv[], int argc )
{
	/* get user context */
	user_context *myctx = (user_context *)cli_get_context(cli);
  (void) command;
  (void) argv;
  (void) argc;

	cli_print(cli, "Can : %x", (unsigned int)myctx->can_info.can_socket);
	return CLI_OK;
}

int cli_v2x_set_can_socket_addr(struct cli_def *cli, const char *command, char *argv[], int argc)
{
	unsigned int    addr = 0;
	int							i = 0;


	/* get user context */
	user_context *myctx = (user_context *)cli_get_context(cli);
  (void) command;
 
	IS_HELP_ARG("can set -addr 0xNNNNN");

	CHECK_NUM_ARGS /* make sure all parameter are there */

	for (i = 0; i < argc; i += 2) {
		GET_TYPE_INT("-addr", addr, unsigned int, i, "Address of current session ", "%x");
	}

	if (addr == 0) {
		cli_print(cli, "ERROR : address is incorrect %x\n", (int)addr);
		return CLI_ERROR;
	}
	else {
		can_socket_t   *can_socket = NULL;

		can_socket = (can_socket_t*)addr;
		cli_print(cli, "Copy CAN : %x", (unsigned int)can_socket);
		myctx->can_info.can_socket = can_socket;

	}

	return CLI_OK;
}
