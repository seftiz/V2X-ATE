
#ifndef __V2X_CLI_H__
#define __V2X_CLI_H__

#if	defined(__THREADX__) && defined(__CRATON_ARM)
#include <libcli.h>
#elif defined(__THREADX__) && !defined(__CRATON_ARM)
#include "../../threadx/cli_arc/libcli/libcli.h"
#elif defined (__linux__)

#include "../../linux/libcli/libcli.h"
#include <pthread.h>
#include <syslog.h>
#endif

#include <atlk/sdk.h>
#include <atlk/v2x.h>
#include <atlk/v2x_service.h>
#ifdef __THREADX__
#include <atlk/nav_service.h>
#include <atlk/can_service.h>
#endif

#include <atlk/ecc_service.h>
#include "../queue.h"

#ifdef __linux__
#include <atlk/remote.h>
#include <atlk/v2x_remote.h>
#include <atlk/mib_remote.h>
#endif

#ifdef __THREADX__
#include <tx_api.h>
#include <atlk/can_service.h>
#include <craton/imq.h>
#include <craton/syslog.h>
#endif

/* Define user context variables for the cli */

#include "list.h"
#ifdef __THREADX__	
typedef struct  {

// #ifdef __THREADX__	
	TX_THREAD    								nav_thread;
// #elif defined (__linux__)
	// pthread_t     							nav_thread;
// #endif
	uint8_t                     nav_thread_stack[1024];
	int8_t                      loop_flag;
	nav_fix_subscriber_t        *nav_hwd;
	nav_service_t 							*nav_service;
	
} nav_op_data_t;
#endif
typedef struct {
	unsigned int		link_rx_packets;
	unsigned int		link_tx_packets;
#ifdef __THREADX__
	unsigned int		can_rx_packets;
	unsigned int		can_tx_packets;

	unsigned int		can_rx_frames_rate;
#endif
} cli_cntrs;
#ifdef __THREADX__
typedef struct {
	/* Shared CAN socket */
	can_socket_t 			*can_socket;
	/* CAN session filter */
	can_socket_config_t     can_params;
	/* Internal filter allocation for changes */
	can_id_filter_t 		*filter_array;
} can_params_t;
#endif


typedef struct {
		
	/* Session verification information */

	ecc_socket_t *verification_socket;
	ecc_request_t verification_request;
	int32_t                    cnt_verification_responses;
	int32_t				       			 cnt_verification_requests;

	/* Session signing information */
	ecc_socket_t 		*signing_socket;
	ecc_request_t 		signing_request;
	int32_t               		cnt_sign_responses;
	int32_t				  					cnt_sign_requests;
		
} ecc_params_t;


#define CLITEST_PORT                8000
#define MODE_CONFIG_INT             10

#define USERNAME					"root"
#define PASSWORD					"root"


#define MAX_CLIENT_SUPPORTED 20

/** Set cli thread priority and time slice */
#define CLI_THREAD_PRIO 21
#define CLI_THREAD_TIME_SLICE 50

/** Defualt startup value for QA units */
#define RF_IF_1_ASSIGN_FREQ 		5890
#define RF_IF_2_ASSIGN_FREQ 		5920
#define RF_DEFUALT_POWER				-15


#define NX_THREAD_PRIO 1
#define MAIN_THREAD_PRIO 2
#define MAIN_THREAD_TIME_SLICE 50
#define MAIN_THREAD_STACK_SIZE (1 << 15)
#define MAIN_BUF_SIZE 500


#define CLI_THREAD_STACKSIZE 1024*16

typedef struct _arc_imq_buffer {
  struct list_head list;
  struct list_head rx;
  int rx_msg_in_queue;
  struct list_head tx;
  int tx_msg_in_queue;
  
} cli_queue_t;


#if defined(__CRATON_ARC1) || defined(__CRATON_ARC2)
#include "../circular_queue.h"
#endif

typedef struct cli_thread_info_struct {

	int												is_active;
#if defined(__CRATON_ARC1) || defined(__CRATON_ARC2)
	circular_queue_t      		buffer; 
#endif
	struct list_head 					list;
	int												socket;
	int												idx;
	uint8_t      		      		stack[CLI_THREAD_STACKSIZE];
#ifdef __THREADX__	
	TX_THREAD    							thread;
#elif defined (__linux__)
	pthread_t     						thread;
#endif

} cli_thread_info_t;




typedef struct {
  
	struct list_head 		list;
	int									idx;
	v2x_socket_t 				*v2x_socket; /** Link layer socket */
#ifdef __THREADX__
	can_params_t				can_info;
#endif
	ecc_params_t				ecc_info;
#ifdef __THREADX__	
	nav_op_data_t   		nav_info;
#endif	
	unsigned int  			tbd1;
	cli_cntrs		  			cntrs;
	char			  	 			user_context_name[12];
#if defined(__CRATON_ARC1) || defined(__CRATON_ARC2)
	imq_socket_t 				*imq_data_socket;
#endif
	cli_thread_info_t	*cli_thread;


} user_context;
 

#define MAX_TX_MSG_LEN		1024 * 2

#if defined (__GNUC__) || defined (__linux__)
	#define UNUSED(d) d __attribute__ ((unused))
#elif defined(__CRATON_ARM) 
  #define UNUSED(d) d
#endif


#define __USE_API_DEFAULTS__

#define str(x) #x
#define xstr(x) str(x)

#define GET_VALUE(_parameter_,_var_,_idx_,_user_msg_,_fmt_) {  \
    if ( (argv[_idx_] != NULL) && (strcmp(argv[_idx_], _parameter_) == 0) ) {           \
      unsigned int value = 0;                           \
      int rc = 0;                               \
      int par_idx = (_idx_+1);                          \
      if (!argv[par_idx] && !&argv[par_idx]) {          \
          cli_print(cli, _user_msg_);                   \
          return CLI_OK;                                \
      }                                                 \
      rc = sscanf(argv[par_idx], _fmt_, &value);              \
      if ( rc > 0 ) { \
        _var_ = value;                                   \
        /*cli_print( cli, "DEBUG : Processed parameter %s, value %d" , _parameter_ , value );*/\
      } \
      else { \
        cli_print( cli, "ERROR : Processed parameter %s, value #_fmt_ failed" , _parameter_ , value );\
      }\
    }                                                   \
}

#define GET_INT(_parameter_,_var_,_idx_,_user_msg_) GET_TYPE_INT(_parameter_,_var_,int, _idx_,_user_msg_,"%d")
#define GET_HEX(_parameter_,_var_,_idx_,_user_msg_) GET_TYPE_INT(_parameter_,_var_, unsigned int, _idx_,_user_msg_,"%x")
/*
#define GET_HEX(_parameter_,_var_,_idx_,_user_msg_) {  \
	if ( (argv[_idx_] != NULL) && (strcmp(argv[_idx_], _parameter_) == 0) ) { \
      unsigned int value = 0;                           \
      int par_idx = (_idx_+1);                          \
      if (!argv[par_idx] && !&argv[par_idx]) {          \
          cli_print(cli, _user_msg_);                   \
          return CLI_OK;                                \
	        }                                           \
      sscanf(argv[par_idx], "%x", &value);              \
      _var_ = value;                                    \
	  cli_print( cli, "DEBUG : Processed parameter %s, value 0x%x" , _parameter_ , value );\
	}                                                   \
}
*/

#define GET_TYPE_INT(_parameter_,_var_,_var_type_, _idx_,_user_msg_,_fmt_str_) {  \
    if ( (argv[_idx_] != NULL) && (strcmp(argv[_idx_], _parameter_) == 0) ) {           \
      _var_type_ value = 0;                           \
      int par_idx = (_idx_+1);                          \
      if (!argv[par_idx] && !&argv[par_idx]) {          \
          cli_print(cli, _user_msg_);                   \
          return CLI_OK;                                \
      }                                                 \
      sscanf(argv[par_idx], _fmt_str_, &value);              \
      _var_ = value; \
	  cli_print( cli, "DEBUG : Processed parameter %s, value " #_fmt_str_ , _parameter_ , value );\
    }                                                   \
}


#define GET_STRING(_parameter_,_var_,_idx_,_user_msg_) {  \
    if ( (argv[_idx_] != NULL) && (strcmp(argv[_idx_], _parameter_) == 0) ) {           \
      int par_idx = (_idx_+1);                          \
      if (!argv[par_idx] && !&argv[par_idx]) {          \
          cli_print(cli, _user_msg_);                   \
          return CLI_OK;                                \
      }     											\
	  memset( _var_, 0 , sizeof(_var_) );\
	  sscanf(argv[par_idx], "%s", (char*) &_var_);    	\
	  cli_print( cli, "DEBUG : Processed parameter %s, value %s" , _parameter_ , _var_ );\
    }                                                   \
}

#define GET_STRING_VALUE(_parameter_,_var_,_user_msg_) {  \
    int j = 0; \
    for ( j = 0; j < argc; j++) { \
      if ( (argv[j] != NULL) && (strcmp(argv[j], _parameter_) == 0) ) {           \
        int par_idx = (j+1);                          \
        if (!argv[par_idx] && !&argv[par_idx]) {          \
            cli_print(cli, _user_msg_);                   \
            return CLI_OK;                                \
        }     											\
        memset( _var_, 0 , sizeof(_var_) );\
        sscanf(argv[par_idx], "%s", (char*) &_var_);    	\
        /*cli_print( cli, "DEBUG : Processed parameter %s, value %s" , _parameter_ , _var_ );*/\
      }                                                   \
   } \
}

#define GET_NUMERIC_VALUE(_parameter_,_var_,_user_msg_) {  \
    int j = 0; \
    for ( j = 0; j < argc; j++) { \
      int value = 0;                           \
      if ( (argv[j] != NULL) && (strcmp(argv[j], _parameter_) == 0) ) {           \
        int par_idx = (j+1);                          \
        if (!argv[par_idx] && !&argv[par_idx]) {          \
            cli_print(cli, _user_msg_);                   \
            return CLI_OK;                                \
        }     											\
        sscanf(argv[par_idx], "%d", &value);              \
        _var_ = value;                                   \
        /*cli_print( cli, "DEBUG : Processed parameter %s, value %d" , _parameter_ , value );*/\
      }                                                   \
   } \
}


#define CHECK_NUM_ARGS \
	if ( (argc % 2) != 0 ) { \
      cli_print(cli, "Error : number of argument is mismatch" ); \
      return CLI_ERROR_ARG; \
	}

#define IS_HELP_ARG(_err_usage_)\
  if ( (argv[0] != NULL) && (strcmp(argv[0], "?") == 0) ) {\
    cli_print(cli, "usage : %s" , _err_usage_ );\
    return CLI_OK;\
  }
  
  
#define IF_ID_MIN 1
#define IF_ID_MAX 2

#define ERR_VALUE (-1)

#define ENUM2STR(x) #x


#endif /* __V2X_CLI_H__ */


