
#include "../../common/general/general.h"
#include "../../common/v2x_cli/v2x_cli.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#ifdef __THREADX__
#include <nxd_bsd.h>
#endif

#include "ecc.h"
#include "../../linux/remote/remote.h"

#ifdef __linux__
#include <atlk/remote.h>
#include <atlk/ecc_remote.h>
#include <atlk/ecc_service.h>
#endif


/* Shared ECC service */
static ecc_service_t *ecc_service = NULL;

static unsigned int 			m_ecc_sign_responses = 0,
													m_ecc_sign_requests = 0,
													m_ecc_verify_requests = 0,
													m_ecc_verify_responses = 0;
													





int cli_v2x_ecc_service_create( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  atlk_rc_t 		rc 						= ATLK_OK;
  char          str_data[256] = "hw";
  int32_t       i             = 0;
  
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  (void) myctx; /* not used  */
  IS_HELP_ARG("can service create -type hw|remote [-server_addr ip_address]")
  CHECK_NUM_ARGS
  GET_STRING("-type", str_data, i, "Specify service type, local or remote");
	
  if ( strcmp( (char*) str_data,  "hw") == 0 ) {
#if defined(__THREADX__)

	/* Get ECC HW service */
		rc = ecc_default_service_get(&ecc_service);
		if (atlk_error(rc)) {
			cli_print( cli, "ecc_default_service_get : %s\n", atlk_rc_to_str(rc));
			goto error;
		}
#else
		cli_print( cli, "ERROR : HW implementation is not implemented");
#endif

  } 
  else if ( strcmp( (char*) str_data, "remote") == 0 ) {
#ifdef __linux__
		  rc = ecc_remote_service_create( get_active_cli_transport(), NULL, &ecc_service);
			if (atlk_error(rc)) {
				cli_print(cli, "ecc_remote_service_create: %s\n", atlk_rc_to_str(rc));
				goto error;  
			}
#endif 
  }
  else {
    cli_print( cli, "ERROR : unknown mode of can api");
  }
  syslog( LOG_DEBUG, "ecc_service pointer is %p", (void*) ecc_service );

	return CLI_OK;
	
error:
  return atlk_error(rc);
}

int cli_v2x_ecc_service_delete( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
	(void) myctx; /* not used  */

  IS_HELP_ARG("can service delete")

  ecc_service_delete(ecc_service);
  ecc_service = NULL;
	
	return CLI_OK;
}

int cli_v2x_ecc_curve_type_get( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  char          action[20] = ""; 
  
   /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  
  IS_HELP_ARG("ecc curve get -action sign|verify|all");

  CHECK_NUM_ARGS /* make sure all parameter are there */
	GET_STRING("-action", action,0, "Select action either verify or signing");
	if ( IS_SIGN || IS_ALL ) {
    cli_print ( cli, "ECC sign curve type : %d" , myctx->ecc_info.signing_request.context.curve );
	}
  
  if ( IS_VERIFY || IS_ALL ) {
  	cli_print ( cli, "ECC verify curve type : %d" ,  myctx->ecc_info.verification_request.context.curve );
  }

  return CLI_OK;
}

int cli_v2x_ecc_curve_type_set( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{

 	ecc_curve_t 	user_curve 		= -1;
  int 					curve         = 1;
  char          action[20]    = "";

  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  
  IS_HELP_ARG("ecc curve set -action sign|verify|all -curve 224|256");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
	GET_STRING_VALUE("-action", action, "Select action either verify or signing");
	GET_NUMERIC_VALUE("-curve", curve, "Select curve value");
	
	if ( (strlen(action) == 0) || (curve == -1) ) { 
		cli_print( cli, "ERROR, Missing parameter for action or cur");
		return CLI_ERROR;
	}
	
	if (curve == 224) {
		user_curve = ECC_CURVE_P224;
	} 
	else if (curve == 256) {
		user_curve = ECC_CURVE_P256;
	} 
	else {
		cli_print( cli, "ERROR : curve ilegeal curve value");
		return CLI_ERROR;
	}
  
	if ( IS_SIGN || IS_ALL ) {
		myctx->ecc_info.signing_request.context.curve = user_curve;
	}
 	if ( IS_VERIFY || IS_ALL ) {
    myctx->ecc_info.verification_request.context.curve = user_curve;
  }

  return CLI_OK;
}

int cli_v2x_ecc_socket_create( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  atlk_rc_t     rc 						= ATLK_OK;
  char          action[20]    = "";

  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  
  IS_HELP_ARG("ecc socket create -action sign|verify");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
	GET_STRING("-action", action, 0, "Select action either verify or signing");
	if ( strlen(action) == 0) { 
		cli_print( cli, "ERROR, Missing parameter for action or cur");
		return CLI_ERROR;
	}
	
	if ( IS_SIGN || IS_ALL ) {
		/* Create ECC signing socket */
    myctx->ecc_info.signing_socket = NULL;
    rc = ecc_socket_create(ecc_service, &myctx->ecc_info.signing_socket);
		if (atlk_error(rc)) {
			cli_print( cli, "ecc_signing_socket_create : %s\n", atlk_rc_to_str(rc));
			goto error;
		}
	}
	
	if ( IS_VERIFY || IS_ALL ) {
		/* Create ECC verification socket */
    myctx->ecc_info.verification_socket = NULL;
    rc = ecc_socket_create(ecc_service, &myctx->ecc_info.verification_socket);
		if (atlk_error(rc)) {
			cli_print(cli, "ecc_verification_socket_create: %s\n", atlk_rc_to_str(rc));
			goto error;
		}	
	}

error:
  return atlk_error(rc);
}


int cli_v2x_ecc_socket_delete( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  atlk_rc_t     rc 						= ATLK_OK;
  char          action[20]    = "";

  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  
  IS_HELP_ARG("ecc socket delete -action sign|verify");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
	GET_STRING("-action", action, 0, "Select action either verify or signing");
	if ( strlen(action) == 0) { 
		cli_print( cli, "ERROR, Missing parameter for action or cur");
		return CLI_ERROR;
	}
	
	if ( IS_SIGN || IS_ALL ) {
		/* Create ECC signing socket */
		rc = ecc_socket_delete(myctx->ecc_info.signing_socket);
		if ( atlk_error(rc) ) {
			cli_print( cli, "ecc_signing_socket_create : %s\n", atlk_rc_to_str(rc));
			goto error;
		}
	}
	
	if ( IS_VERIFY || IS_ALL ) {
    /* Delete ECC verification socket */
    rc = ecc_socket_delete(myctx->ecc_info.verification_socket);
    if (atlk_error(rc)) {
      cli_print(cli, "ecc_verification_socket_delete: %s\n", atlk_rc_to_str(rc));
      goto error;
    }
	}

error:
  return atlk_error(rc);
}
int cli_v2x_ecc_sign_private_key( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  char          sign_key_str[100] = "",
                hex_arr[38]       = "";
  int           i                 = 0;              
  size_t				msg_size          = 0;

                
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc sign key -private_key 360c3ae1cc12dd1f43fa4286827e9848d8eb6093ab98c5a8b23000c9dd1d3489");
  
  /* If no arguments then its get */
  if ( argc == 0 ) {
    cli_print(cli, "Private key : " ECC_SCALAR_FMT, ECC_SCALAR_FMT_ARGS( (long unsigned int) myctx->ecc_info.signing_request.params.sign_params.private_key) ); 
    return CLI_OK; 
	}
  
  GET_STRING("-private_key", sign_key_str, 0, "Select action either verify or signing");

 
  
  msg_size = (size_t) (strlen(sign_key_str) / 2);
  if ( msg_size != 32 ) { 
    cli_print(cli, "Error, private key length is illegal, should be 64 chars" ); 
    return CLI_ERROR;
  }
  
  hexstr_to_bytes_arr(sign_key_str, strlen(sign_key_str), (uint8_t*)hex_arr, &msg_size);
  
  if ( msg_size != (PRIVATE_KEY_LEN * sizeof(int)) ) {
    cli_print ( cli, "ERROR : unable to convert key value, expected msg_size %d, received %d",(int)(PRIVATE_KEY_LEN * sizeof(int)), (int) msg_size);
    return CLI_ERROR;
  }

  int *pos = (int*) hex_arr; 
  for ( i=0; i < PRIVATE_KEY_LEN ; i++, pos++ ) {
    myctx->ecc_info.signing_request.params.sign_params.private_key.value[i] = htonl(*pos);
  }

  return CLI_OK;
}

int cli_v2x_ecc_sign_request_send( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  uint32_t      request_id        = 0;
  char          hash_key_str[100] = "",
                hex_arr[36]       = "";
  
  size_t				msg_size          = 0;
  int           i                 = 0;
  atlk_rc_t     rc                = ATLK_OK;
  
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc sign request -id 1-N -hash 6e43d9322536c7535efbc81edc214974780fe2f78bd0b2a2c93126c68495a379");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  /* Get parameters */
  GET_INT("-id", request_id, 0, "Select action either verify or signing");
	GET_STRING("-hash", hash_key_str, 2, "Select action either verify or signing");
  
  
  if ( request_id <= 0 ) {
    cli_print ( cli, "ERROR : request id is illegal" );
    return CLI_ERROR;
  }
  
  if ( strlen(hash_key_str) != 64 ) {
    cli_print ( cli, "ERROR : hash value is illegal" );
    return CLI_ERROR;
  }
  /* Get Hash value */
  myctx->ecc_info.signing_request.context.request_id = request_id;
 
  msg_size = (size_t) (strlen(hash_key_str) / 2);

  hexstr_to_bytes_arr(hash_key_str, strlen(hash_key_str), (uint8_t*)hex_arr, &msg_size);
  
  if ( msg_size != (HASH_DATA_LEN * sizeof(int)) ) {
    cli_print ( cli, "ERROR : unable to convert key value" );
    return CLI_ERROR;
  }
  
  int *pos = (int *) hex_arr; 
  for ( i=0; i < HASH_DATA_LEN ; i++, pos++ ) {
		myctx->ecc_info.signing_request.params.sign_params.digest.value[i] = htonl(*pos);
  }
  
  /* Send ECC signing request */
  rc = ecc_request_send( myctx->ecc_info.signing_socket, &myctx->ecc_info.signing_request, NULL );
  if (atlk_error(rc)) {
    cli_print( cli, "ecc_signing_request_send: %s\n", atlk_rc_to_str(rc));
    goto error;
  }
  
  /* Print ECC signing request ID */
  cli_print( cli, "Sent ECC signing request with ID %llu.\n",(long long unsigned int)myctx->ecc_info.signing_request.context.request_id );
  m_ecc_sign_requests++;
  myctx->ecc_info.cnt_sign_requests++;
  
error:
  return rc;
}

int cli_v2x_ecc_sign_response_receive( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  atlk_rc_t                 rc                = ATLK_OK;
  ecc_response_t    signing_response  = ECC_RESPONSE_INIT;
   
  /* Timeout variables */
  uint32_t                  timeout_ms        = 5000;
  struct timeval            start, current;
  int32_t                   rx_timeout	      =	0;

  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc sign get-response [-timeout_ms n]");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  /* Get parameters */
  GET_INT("-timeout_ms", timeout_ms, 0, "Define timeout for first frame (mSec)");

  rx_timeout = 0;
  gettimeofday (&start, NULL);	
  
  do {
    
    rc = ecc_response_receive( myctx->ecc_info.signing_socket, &signing_response, NULL );
    if (atlk_error(rc)) {
      gettimeofday (&current, NULL);	
      double elapsedTime = (current.tv_sec - start.tv_sec) * 1000.0;
      if ( elapsedTime > timeout_ms ) {
        rx_timeout = 1;
      }
      else {
        usleep( 1000 );
      }
    }
    else {
      rx_timeout = 2;
    }
    
  } while ( !rx_timeout );

  if ( rx_timeout == 1 ) {
      cli_print(cli, "ERROR : rx time out : %s\n", atlk_rc_to_str(rc));
      goto error;
  }  
  m_ecc_sign_responses++;
  myctx->ecc_info.cnt_sign_responses++;
  
  /* ECC signing response content */
  ecc_scalar_t s_scalar = signing_response.result.sign_result.s_scalar;
  ecc_scalar_t x_coordinate = signing_response.result.sign_result.R_point.x_coordinate;

 /* Print ECC signing response content */
  cli_print( cli, "ECC signature for request ID %llu:", (long long unsigned int) signing_response.context.request_id);
  cli_print( cli, "r: " ECC_SCALAR_FMT "", ECC_SCALAR_FMT_ARGS((long unsigned int) x_coordinate) );
  cli_print( cli, "s: " ECC_SCALAR_FMT "", ECC_SCALAR_FMT_ARGS( (long unsigned int) s_scalar) );
  
error:
  return rc;
}

int cli_v2x_ecc_verification_set_public_key( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  char          verfication_key_x_str[100] = "",
                verfication_key_y_str[100] = "",
                point_type[20] = "",
                hex_arr[38] = "";
  int           i           = 0,
                *pos        = NULL;
                
  size_t				msg_size = 0;

                
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc verification key -x 360c3a... -y 360c3a....");

  /* Handle GET */
  if ( argc  == 0 ) {
     cli_print(cli, "Public key :"); 
    cli_print(cli, "x : " ECC_SCALAR_FMT, ECC_SCALAR_FMT_ARGS( (long unsigned int) myctx->ecc_info.verification_request.params.verify_params.public_key.x_coordinate) ); 
    cli_print(cli, "y : " ECC_SCALAR_FMT, ECC_SCALAR_FMT_ARGS( (long unsigned int) myctx->ecc_info.verification_request.params.verify_params.public_key.y_coordinate) ); 
    return CLI_OK; 
	}
  
  for ( i = 0 ; i < argc; i += 2 ) {  
    GET_STRING("-x", verfication_key_x_str, i, "Set x point of public key");
    GET_STRING("-y", verfication_key_y_str, i, "Set y point of public key");
    GET_STRING("-point_type", point_type, i, "Set point type");

  }
  
  /* Get x cordinate */
  if ( strlen(verfication_key_x_str) > 0 ) {
  
    memset ( hex_arr, 0 , sizeof(hex_arr) );

    msg_size = (size_t) (strlen(verfication_key_x_str) / 2);
    hexstr_to_bytes_arr(verfication_key_x_str, strlen(verfication_key_x_str), (uint8_t*)hex_arr, &msg_size);

    if ( msg_size != (PRIVATE_KEY_LEN * sizeof(int)) ) {
      cli_print ( cli, "ERROR : unable to convert key value" );
      return CLI_ERROR;
    }

    pos = (int*) hex_arr; 
    for ( i=0; i < PRIVATE_KEY_LEN ; i++, pos++ ) {
      myctx->ecc_info.verification_request.params.verify_params.public_key.x_coordinate.value[i] = htonl(*pos);
    }
  }

  /* Get Y cordinate */
  if ( strlen(verfication_key_y_str) > 0 ) {
    
    memset ( hex_arr, 0 , sizeof(hex_arr) );
    msg_size = (size_t) (strlen(verfication_key_y_str) / 2);

    hexstr_to_bytes_arr(verfication_key_y_str, strlen(verfication_key_y_str), (uint8_t*)hex_arr, &msg_size);
    if ( msg_size != (PRIVATE_KEY_LEN * sizeof(int)) ) {
      cli_print ( cli, "ERROR : unable to convert key value" );
      return CLI_ERROR;
    }
    
    pos = (int*) hex_arr; 
    for ( i=0; i < PRIVATE_KEY_LEN ; i++, pos++ ) {
      myctx->ecc_info.verification_request.params.verify_params.public_key.y_coordinate.value[i] = htonl(*pos);
    }
  }
  
  if ( strlen(point_type) > 0 ) {
    /* TBD */
    cli_print ( cli, "Unsupported action, system is supporting ECC_POINT_UNCOMPRESSED" );
  } 
  else {
    myctx->ecc_info.verification_request.params.verify_params.public_key.point_type = ECC_POINT_UNCOMPRESSED;
  }

  return CLI_OK;
}



int cli_v2x_ecc_verification_set_signature( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  char          signature_key_r_str[100] = "",
                signature_key_s_str[100] = "",
                hex_arr[38] = "";
  int           i           = 0,
                *pos        = NULL;
                
  size_t				msg_size = 0;

                
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc verification signature -r 360c3a... -s 360c3a....");

  /* Handle GET */
  if ( argc  == 0 ) {

    cli_print(cli, "signature :"); 
    cli_print(cli, "r : " ECC_SCALAR_FMT, ECC_SCALAR_FMT_ARGS((long unsigned int)myctx->ecc_info.verification_request.params.verify_params.signature.r_scalar) ); 
    cli_print(cli, "s : " ECC_SCALAR_FMT, ECC_SCALAR_FMT_ARGS((long unsigned int)myctx->ecc_info.verification_request.params.verify_params.signature.s_scalar) ); 
    return CLI_OK; 
	} 
 
  
  for ( i = 0 ; i < argc; i += 2 ) {  
    GET_STRING("-r", signature_key_r_str, i, "Set x point of public key");
    GET_STRING("-s", signature_key_s_str, i, "Set y point of public key");

  }
  
  /* Get R cordinate */
  if ( strlen(signature_key_r_str) > 0 ) {
  
    memset ( hex_arr, 0 , sizeof(hex_arr) );

    msg_size = (size_t) (strlen(signature_key_r_str) / 2);
    hexstr_to_bytes_arr(signature_key_r_str, strlen(signature_key_r_str), (uint8_t*)hex_arr, &msg_size);

    if ( msg_size != (SIGNATURE_KEY_LEN * sizeof(int)) ) {
      cli_print ( cli, "ERROR : unable to convert key value" );
      return CLI_ERROR;
    }

    pos = (int*) hex_arr; 
    for ( i=0; i < SIGNATURE_KEY_LEN ; i++, pos++ ) {
      myctx->ecc_info.verification_request.params.verify_params.signature.r_scalar.value[i] = htonl(*pos);
    }
  }

  /* Get S cordinate */
  if ( strlen(signature_key_s_str) > 0 ) {
    
    memset ( hex_arr, 0 , sizeof(hex_arr) );
    msg_size = (size_t) (strlen(signature_key_s_str) / 2);

    hexstr_to_bytes_arr(signature_key_s_str, strlen(signature_key_s_str), (uint8_t*)hex_arr, &msg_size);
    if ( msg_size != (SIGNATURE_KEY_LEN * sizeof(int)) ) {
      cli_print ( cli, "ERROR : unable to convert key value" );
      return CLI_ERROR;
    }
    
    pos = (int*) hex_arr; 
    for ( i=0; i < SIGNATURE_KEY_LEN ; i++, pos++ ) {
      myctx->ecc_info.verification_request.params.verify_params.signature.s_scalar.value[i] = htonl(*pos);
    }
  }
 
  return CLI_OK;
}

int cli_v2x_ecc_verification_request_send( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  uint32_t      request_id        = 0;
  char          hash_key_str[100] = "",
                hex_arr[36]       = "";
  int           i           = 0,
                *pos        = NULL;
  
  
  size_t				msg_size          = (HASH_DATA_LEN * sizeof(int));
  atlk_rc_t     rc                = ATLK_OK;
  
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc verification request -id N -hash 360c...");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  /* Get parameters */
  GET_INT("-id", request_id, 0, "Select action either verify or signing");
	GET_STRING("-hash", hash_key_str, 2, "Select action either verify or signing");
  
  /* Get Hash value */
  myctx->ecc_info.verification_request.context.request_id = request_id;
  hexstr_to_bytes_arr(hash_key_str, strlen(hash_key_str), (uint8_t*)hex_arr, &msg_size);
  if ( msg_size != (HASH_DATA_LEN * sizeof(int)) ) {
    cli_print ( cli, "ERROR : unable to convert key value" );
    return CLI_ERROR;
  }
  
  pos = (int*) hex_arr; 
  for ( i=0; i < 32 ; i++, pos++ ) {
		myctx->ecc_info.verification_request.params.sign_params.digest.value[i] = hex_arr[i];
  }
	
	myctx->ecc_info.verification_request.params.sign_params.digest.value_size = (HASH_DATA_LEN * sizeof(int));
	/*	
	cli_print( cli, "SHA-256 hash digest computed:\n");
	cli_print( cli, "  Digest: " SHA_DIGEST_FMT "\n", SHA_DIGEST_FMT_ARGS(myctx->ecc_info.verification_request.digest));
	*/
	
  
  /* Send ECC signing request */
  rc = ecc_request_send( myctx->ecc_info.verification_socket, &myctx->ecc_info.verification_request, NULL );
  if (atlk_error(rc)) {
    cli_print( cli, "ecc_signing_request_send: %s\n", atlk_rc_to_str(rc));
    goto error;
  }
  
  /* Print ECC signing request ID */
  cli_print( cli, "Sent ECC signing request with ID %llu.\n", (long long unsigned int)myctx->ecc_info.signing_request.context.request_id );
  m_ecc_verify_requests++;
  myctx->ecc_info.cnt_verification_requests++;
  
error:
  return rc;
}

int cli_v2x_ecc_verification_get_response( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )  
{
  atlk_rc_t                 		 rc                = ATLK_OK;
  ecc_response_t    verify_response  = ECC_RESPONSE_INIT;
   
  /* Timeout variables */
  uint32_t                  timeout_ms        = 5000;
  //struct timeval            start, current;
  //int32_t                   rx_timeout	      =	0;

	atlk_wait_t 							wait = ATLK_WAIT_INIT;
	
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
    
  IS_HELP_ARG("ecc verify get-response [-timeout_ms n]");

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  /* Get parameters */
  GET_INT("-timeout_ms", timeout_ms, 0, "Define timeout for first frame (mSec)");

	if (timeout_ms == 20000) {
		wait = atlk_wait_forever;

	}
	else if ( timeout_ms == 5000 ) {
		
		wait.wait_type = ATLK_WAIT_INTERVAL;
		wait.wait_usec = MAX_RTT_USEC;
	}

  rc = ecc_response_receive( myctx->ecc_info.verification_socket, &verify_response, &wait );
  if (atlk_error(rc)) {
		cli_print( cli, "ecc_verification_response_receive: %s\n", atlk_rc_to_str(rc));
		goto error;
	}

	if (verify_response.rc == ECC_OK) {
		m_ecc_verify_responses++;
		myctx->ecc_info.cnt_verification_responses++;

		cli_print( cli, "ECC request %d is %d", 
(int) verify_response.context.request_id, verify_response.rc);
	}

	/*
	
  rx_timeout = 0;
  gettimeofday (&start, NULL);	

  do {
    
    rc = ecc_verification_response_receive( myctx->ecc_info.verification_socket, &verify_response, NULL );
    if (atlk_error(rc)) {
      gettimeofday (&current, NULL);	
      double elapsedTime = (current.tv_sec - start.tv_sec) * 1000.0;
      if ( elapsedTime > timeout_ms ) {
        rx_timeout = 1;
      }
      else {
        usleep( 1000 );
      }
    }
    else {
      rx_timeout = 2;
    }
    
  } while ( !rx_timeout );

  if ( rx_timeout == 1 ) {
      cli_print(cli, "ERROR : rx time out : %s\n", atlk_rc_to_str(rc));
      goto error;
  }  
  */
   
error:
  return rc;
}

