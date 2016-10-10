/* Copyright (C) 2014 Autotalks Ltd. */

#include <stdio.h>
#include <assert.h>
#include <inttypes.h>
#include <unistd.h>
#include <tx_api.h>
#include <craton/imq.h>
#include <craton/syslog.h>

#include "socket_imq_bridge.h"

#include "../../common/v2x_cli/v2x_cli.h"
#include "../../common/circular_queue.h"

#include "../../threadx/can/can.h"
#include "../../common/link/link.h"
#include "../../common/nav_api/nav_api.h"

#include   "tx_api.h"


/* Managment & Data IMQ */
static imq_socket_t imq_service[TOTAL_CLI_IMQ] = { IMQ_SOCKET_INIT };
static imq_socket_t imq_socket[TOTAL_CLI_IMQ] = { IMQ_SOCKET_INIT };


#define ARC_MAIN_THREAD_STACK_SIZE		1024 * 32

static TX_THREAD    arc_cli_thread;
static uint8_t      arc_cli_thread_stack[ARC_MAIN_THREAD_STACK_SIZE];
struct list_head    cli_thread_list;
int                 thread_cnt;


/* Thread for gathering all cli to one imq channel */
static TX_THREAD    imq_rx_cli_thread;
static uint8_t      imq_rx_cli_thread_stack[CLI_THREAD_STACKSIZE];


static void imq_2_queue_rx_thread( ULONG input );
static void arc_cli_thread_entry(ULONG input);
void connection_handler( ULONG thread_desc );
int create_cli_struct( struct cli_def **cli );
void threads_garbage_collector( void ); 
void create_delete_threads( ULONG thread_desc ) ;


void craton_user_init(void)
{
  ULONG       trv   = TX_SUCCESS;
  atlk_rc_t   rc    = ATLK_OK;
  int         i     = 0;

  imq_service_config_t config = IMQ_SERVICE_CONFIG_INIT;

  printf( "NOTE : craton_user_init starting on arc %d\n", ARC_ID );

  /* Bind Managment IMQ server */
  for ( i = 0; i < TOTAL_CLI_IMQ; i++ ) { 
    syslog( LOG_DEBUG, "Bind IMQ on arc %d on service %d\n", ARC_ID, (IMQ_IDX_START + i) );
    rc = imq_bind( &imq_service[i], (IMQ_IDX_START + i) );
    if ( atlk_error(rc) ) {
      syslog( LOG_ERR, "imq_bind on arc %d : %s\n", ARC_ID, atlk_rc_to_str(rc) );
      return;
    }
  }
 
  /* Set socket configuration parameters */
  config.server_to_client_config.queue_mtu = IMQ_CLI_QUEUE_MTU;
  config.server_to_client_config.queue_length = IMQ_CLI_QUEUE_LENGTH;
  config.client_to_server_config.queue_mtu = IMQ_CLI_QUEUE_MTU;
  config.client_to_server_config.queue_length = IMQ_CLI_QUEUE_LENGTH;
  config.service_name = "qa_cli_bridge";

  /* Listen on IMQ echo server socket */
  for ( i = 0; i < TOTAL_CLI_IMQ; i++ ) { 
    rc = imq_listen(&imq_service[i], &config);
    if (atlk_error(rc)) {
      syslog( LOG_ERR, "imq_listen on arc %d : %s\n", ARC_ID, atlk_rc_to_str(rc) );
      return;
    }
  }

	INIT_LIST_HEAD(&cli_thread_list);

  /* Create IMQ echo server thread */
  trv = tx_thread_create(&arc_cli_thread, "arc_cli_thread",
  												// create_delete_threads , 0,
                         arc_cli_thread_entry, 0,
                         arc_cli_thread_stack,
                         sizeof(arc_cli_thread_stack),
                         SOCK_TO_IMQ_THREAD_PRIO,
                         SOCK_TO_IMQ_THREAD_PRIO,
                         TX_NO_TIME_SLICE, TX_AUTO_START);
  if (trv != TX_SUCCESS) {
    printf( "arc_cli_thread for arc %d failed, trv=0x%lx\n", ARC_ID, trv);
    return;
  }
  
  printf( "ARC %d was initilized succsesfuly !\n" , ARC_ID );
  return;
	/* for compilation only */
	arc_cli_thread_entry(0);

}


int qa_idle_timeout(struct cli_def *cli)
{
  cli_print(cli, "Custom idle timeout");
  return CLI_QUIT;
}

int qa_check_auth(const char *username, const char *password)
{
  if (strcmp(username, USERNAME) != 0)
    return CLI_ERROR;
  if (strcmp(password, PASSWORD) != 0)
    return CLI_ERROR;
  return CLI_OK;
}

int show_version( struct cli_def *cli, const char *command, char *argv[], int argc ) 
{
  (void)command;
  (void)argv;
  (void)argc;
  
  cli_print( cli, "Version : 3.2" );
  return CLI_OK;
}


int qa_check_enable(const char *password)
{
  return !strcmp(password, PASSWORD);
}

int create_cli_struct( struct cli_def **cli )
{
  struct cli_command    *c = NULL; 
  struct cli_command    *d = NULL; 
  
  char   cli_hostname[100] = {0};

  sprintf( cli_hostname, "qa@arc%d >", ARC_ID );

  *cli = cli_init();

  cli_set_hostname(*cli, cli_hostname );
  cli_set_banner(*cli, "Autotalks - Confidence of Knowing Ahead.\nWelcome to Auto-talks V2X cli\n\n");

  cli_protocol(*cli, CLI_PROTOCOL_TELNET /* CLI_PROTOCOL_IMQ */ );

  // cli_regular(*cli, regular_callback);
  cli_regular_interval(*cli, 5); // Defaults to 1 second
  cli_set_idle_timeout_callback(*cli, 0, qa_idle_timeout); /* 5 Minutes idle timeout */

  cli_register_command(*cli, NULL, "show", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, NULL);

#if	defined(__CRATON_ARC1)

  /* link commands */
  c = cli_register_command(*cli, NULL, "link", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "send message frame via SDK");
  d = cli_register_command(*cli, c, "service", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Set management mibs");
  cli_register_command(*cli, d, "create", cli_v2x_link_service_create, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "open link new socket");
  cli_register_command(*cli, d, "delete", cli_v2x_link_service_delete, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "close link socket");
  d = cli_register_command(*cli, c, "socket", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Set management mibs");
  cli_register_command(*cli, d, "create", cli_v2x_link_socket_create, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "open link new socket");
  cli_register_command(*cli, d, "delete", cli_v2x_link_socket_delete, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "close link socket");
	cli_register_command(*cli, d, "tx", cli_v2x_link_tx, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Transmit Data via link socket");
  cli_register_command(*cli, d, "rx", cli_v2x_link_rx, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Receive Data via link socket");
  cli_register_command(*cli, d, "set", cli_v2x_set_link_socket_addr, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Receive Data via link socket");
  cli_register_command(*cli, d, "get", cli_v2x_get_link_socket_addr, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Receive Data via link socket");
	
	d = cli_register_command(*cli, c, "counters", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Counters");
	cli_register_command(*cli, d, "reset", cli_v2x_link_reset_cntrs, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Reset Internal link counters");
  cli_register_command(*cli, d, "print", cli_v2x_link_print_cntrs, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "print Internal link counters");

  cli_register_command(*cli, c, "reset_cntrs", cli_v2x_link_reset_cntrs, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Reset Internal link counters");
  cli_register_command(*cli, c, "print_cntrs", cli_v2x_link_print_cntrs, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "print Internal link counters");

#endif

  /* handle POTI command */
  c = cli_register_command(*cli, NULL, "nav", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Navigation API operations");
  cli_register_command(*cli, c, "init", cli_v2x_nav_init, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "init nav api");
  cli_register_command(*cli, c, "start", cli_v2x_nav_start, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "start nav api handler");
  cli_register_command(*cli, c, "stop", cli_v2x_nav_stop, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "start nav api handler");


  /* can */
	d = cli_register_command(*cli, NULL, "can", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "can bus implementation");
  c = cli_register_command(*cli, d, "service", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Set service");
  cli_register_command(*cli, c, "create", cli_v2x_can_service_create, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Create can service");
  cli_register_command(*cli, c, "delete", cli_v2x_can_service_delete, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Delete can service");
	c = cli_register_command(*cli, d, "socket", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Set can socket");
  cli_register_command(*cli, c, "create", cli_v2x_can_socket_create, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Create can socket");
  cli_register_command(*cli, c, "delete", cli_v2x_can_socket_delete, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Delete can socket");
  cli_register_command(*cli, c, "tx", cli_v2x_can_tx, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Send can frames over socket");
  cli_register_command(*cli, c, "rx", cli_v2x_can_rx, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Receive can frames over socket");
	c = cli_register_command(*cli, d, "counters", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Counters");
	cli_register_command(*cli, c, "reset", cli_v2x_can_reset_cntrs, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Reset Internal link counters");
  cli_register_command(*cli, c, "print", cli_v2x_can_print_cntrs, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "print Internal link counters");
  c = cli_register_command(*cli, d, "rx", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "RX");
  cli_register_command(*cli, c, "rate", cli_v2x_can_print_rx_rate, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Print RX average frames rate");
 

  cli_set_auth_callback(*cli, qa_check_auth);
  cli_set_enable_callback(*cli, qa_check_enable);

  return 0;

}

void cli_cleanup( struct cli_def *cli )
{
	/* get user context */
	// user_context *user_ctx = (user_context *) cli_get_context(cli);
  (void)cli;
  
  return;
	
}
  

void arc_cli_thread_entry( ULONG thread_desc )
{

  cli_thread_info_t 	*thread_info                = (cli_thread_info_t *) thread_desc;
  atlk_rc_t 	        rc                          = ATLK_OK;
  ULONG               trv                         = TX_SUCCESS;
  int                 i;

	(void) thread_info;
  
  /* Accept an IMQ connection */
  for ( i = 0; i < TOTAL_CLI_IMQ; i++ ) { 

    rc = imq_accept(&imq_service[i], &imq_socket[i], &atlk_wait_forever);
    if (atlk_error(rc)) {
      syslog( LOG_ERR, "imq_accept on arc %d : %s\n", ARC_ID, atlk_rc_to_str(rc));
      return;
    }
  }

  /* Create IMQ echo server thread */
  trv = tx_thread_create(&imq_rx_cli_thread, "imq_rx_thread",
                         imq_2_queue_rx_thread, 0,
                         imq_rx_cli_thread_stack,
                         sizeof(imq_rx_cli_thread_stack),
                         IMQ_RX_TX_THREAD_PRIO,
                         IMQ_RX_TX_THREAD_PRIO,
                         IMQ_RX_TX_THREAD_TIME_SLICE, TX_AUTO_START);
  if (trv != TX_SUCCESS) {
    printf( "imq_2_queue_rx_thread failed on arc %d, trv=0x%lx\n", ARC_ID, trv);
    return;
  }
  
  while (1) {
  
    sck_imq_msg_t       msg = {0};
    size_t              len = sizeof(msg);
		cli_thread_info_t 	*new_thread = NULL;

    rc =  imq_receive( &imq_socket[CLI_MNGT_IMQ], &msg, &len, &atlk_wait_forever);
    if (atlk_error(rc)) {
      syslog( LOG_ERR, "imq_receive on arc %d failed: %s\n", ARC_ID, atlk_rc_to_str(rc));
      continue;
    }

    if ( len != sizeof(sck_imq_msg_t) ) {
      syslog( LOG_ERR, "imq_accept on arc %d: %s\n", ARC_ID, atlk_rc_to_str(rc));
      continue;
    }

    if ( msg.opcode == SOCK_IMQ_CREATE_CLI ) {

      new_thread = calloc(1, sizeof(cli_thread_info_t) );
      if (new_thread == NULL) {
				syslog( LOG_ERR, "Error alloc data for new thread" );
        abort();
      }
			new_thread->is_active = 1;

	   	new_thread->socket = msg.socket;
      new_thread->idx = thread_cnt;
      cq_init( &new_thread->buffer ); /* initlize internal buffer and mutex, must clean */
			
      trv = tx_thread_create(&new_thread->thread, "arc_v2x_cli_thread",
		                          connection_handler, (ULONG) new_thread,
		                          new_thread->stack,
		                          sizeof(new_thread->stack),
		                          SOCK_TO_IMQ_THREAD_PRIO,
		                          SOCK_TO_IMQ_THREAD_PRIO,
		                          TX_NO_TIME_SLICE, TX_AUTO_START);
                          
      if (trv != TX_SUCCESS) {
        printf( "tx_thread_create failed on arc %d, rc=%lx\n", ARC_ID, trv);
        abort();
      }

      list_add(&new_thread->list, &cli_thread_list);
			threads_garbage_collector();
      thread_cnt++;
      
    }
		else {
      syslog( LOG_ERR, "Error msg received, rc=%lx\n", trv);
    }
  }
	
  return;
}

void imq_2_queue_rx_thread( ULONG input )
{
  int                   rc = 0;
  sck_imq_msg_t         msg = { 0 };

  size_t                len = sizeof(sck_imq_msg_t);
  cli_thread_info_t			*curr, *temp;

  (void) input;

  while (1) {

    rc =  imq_receive( &imq_socket[CLI_DATA_IMQ], (void*) &msg, &len, &atlk_wait_forever );
    if (atlk_error(rc)) {
      syslog( LOG_ERR, "imq_receive failed on arc %d : %s\n",ARC_ID, atlk_rc_to_str(rc));
    }

    if ( len == 0 ) {
      continue;
    }
		
    list_for_each_entry_safe(curr, temp, &cli_thread_list, list) {

      if ( (curr->socket == msg.socket) && (curr->is_active) ) {
      	cq_add_str( &curr->buffer, msg.buffer, msg.len );
        break;
      }
    }

  }

}


/* This will handle connection for each client */
void connection_handler( ULONG thread_desc )
{
	//Get the socket descriptor
  cli_thread_info_t     *thread_info = (cli_thread_info_t *) thread_desc;
  struct cli_def        *cli = NULL;
  user_context          user_ctx;

  /* Create cli structure for each user */
  create_cli_struct( &cli );

  memset(&user_ctx, 0, sizeof(user_context));

  user_ctx.idx = thread_info->idx;
  user_ctx.cli_thread = thread_info;
  user_ctx.imq_data_socket = &imq_socket[CLI_DATA_IMQ]; 
    
  cli_set_context(cli, (void*)&user_ctx);
  printf( "NOTE: QA cli created on arc %d at socket %d\n", ARC_ID, thread_info->socket);
  cli_loop(cli, thread_info->socket);
  printf( "NOTE: QA cli is closed on arc %d at socket %d\n", ARC_ID, thread_info->socket);

  cli_cleanup( cli );
  cli_done( cli );

	/* Mark thread as ended, the main cli thread will clean on next client */
  sck_imq_msg_t         msg = { 0 };

  msg.opcode = SOCK_IMQ_DELETE_CLI;
  msg.socket = thread_info->socket;
  msg.sock_port = 0;
  msg.len = 0;
  int rc = imq_send( &imq_socket[CLI_MNGT_IMQ], (void*) &msg, sizeof(sck_imq_msg_t), NULL );
  if (atlk_error(rc)) {
    syslog( LOG_ERR , "Failed sending CLI disconnect to ARM, error : %s\n", atlk_rc_to_str(rc) );
  }

  thread_info->is_active = 0;  	
	
  syslog( LOG_DEBUG, " ** ARC CLI Thread closed. Socket %d, thread %p", thread_info->socket, thread_info);
	tx_thread_sleep(10);
	
}


void threads_garbage_collector( void ) 
{
	cli_thread_info_t			*curr, *temp ;

	syslog( LOG_DEBUG, "threads_garbage_collector : started" );

	list_for_each_entry_safe(curr, temp, &cli_thread_list, list) {

		syslog( LOG_DEBUG, "threads_garbage_collector : testing %p", curr );

		/* Test if thread function is completed */
		if (curr->thread.tx_thread_state != TX_READY ) {
		//if (curr->is_active == 0 ) {
		
			syslog( LOG_DEBUG, "@@@@ Terminate at addr %p", curr );

			ULONG trv = tx_thread_terminate(&curr->thread);
			if (trv != TX_SUCCESS) {
				syslog( LOG_ERR, "V2X-CLI-ARC : tx_thread_terminate failed, rc = %lx\n", trv);
			}

			trv = tx_thread_delete(&curr->thread);
			if (trv != TX_SUCCESS) {
				syslog( LOG_ERR, "V2X-CLI-ARC : tx_thread_delete failed, rc = %lx\n", trv);
			}

			list_del(&curr->list);
			cq_terminate(&curr->buffer);
			free(curr);
			curr = NULL;
 		}
	}
 	
}


