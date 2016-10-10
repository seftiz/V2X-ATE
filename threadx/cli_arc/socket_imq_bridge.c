
  
#include <libcli.h>
#include <nxd_bsd.h>

#include <craton/imq.h>

#include <atlk/sdk.h>
#include <craton/syslog.h>

#include <strings.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

#include "../../common/v2x_cli/list.h"
#include "socket_imq_bridge.h"


static TX_THREAD    sock_thread[TOTAL_ARCS];
static TX_THREAD    tx_thread[TOTAL_ARCS];
static TX_THREAD    rx_thread[TOTAL_ARCS];
static uint8_t      rx_thread_stack[TOTAL_ARCS][0x2000];
static uint8_t      tx_thread_stack[TOTAL_ARCS][0x2000];
static uint8_t      sock_thread_stack[TOTAL_ARCS][0x2000];

/* Managment channel */
static TX_THREAD    rx_mngt_thread[TOTAL_ARCS];
static uint8_t      rx_mngt_stack[TOTAL_ARCS][0x1000];


static imq_socket_t arc_imq_socket_mng[TOTAL_ARCS] = { IMQ_SOCKET_INIT };
static imq_socket_t arc_imq_socket_data[TOTAL_ARCS] = { IMQ_SOCKET_INIT };
struct list_head  sockets[TOTAL_ARCS];
int               thread_cnt[TOTAL_ARCS];



static void create_socket_server(ULONG input);
static void sock_tx_thread(ULONG input);
static void sock_rx_thread(ULONG input);
static void imq_mngt_rx_thread( ULONG input );


typedef struct _cli_thread_info {
  
	struct list_head  list;
	int							  socket;
  int							  idx;
	char						  is_active;
  
} socket_info_t;


void qa_cli_arm( int arc_id )
{
  ULONG trv = TX_SUCCESS;
  
	
	INIT_LIST_HEAD(&sockets[arc_id]);

  int port = (8001 + arc_id);
  /* Create a thread to run socket server */
  trv = tx_thread_create(&sock_thread[arc_id], "arc_socket_server",
                        create_socket_server, port,
                        sock_thread_stack[arc_id],
                        sizeof(sock_thread_stack[arc_id]),
                        SOCK_TO_IMQ_THREAD_PRIO, SOCK_TO_IMQ_THREAD_PRIO,
                        TX_NO_TIME_SLICE, TX_AUTO_START);
  if ( trv != TX_SUCCESS ) {
    fprintf( stderr, "Failed to create sock imq server\n");
  }
  
  tx_thread_sleep(50);
  
  /* Create a thread to run tx server */
  trv = tx_thread_create(&tx_thread[arc_id], "sock2imq_tx",
                        sock_tx_thread, arc_id,
                        tx_thread_stack[arc_id],
                        sizeof(tx_thread_stack[arc_id]),
                        SOCK_TO_IMQ_THREAD_PRIO, 
                        SOCK_TO_IMQ_THREAD_PRIO,
                        TX_NO_TIME_SLICE, TX_AUTO_START);
  if ( trv != TX_SUCCESS ) {
    fprintf( stderr, "Failed to create sock2imq_tx server\n");
  }
  
  /* Create a thread to run tx server */
  trv = tx_thread_create(&rx_thread[arc_id], "sock2imq_rx",
                        sock_rx_thread, arc_id,
                        rx_thread_stack[arc_id],
                        sizeof(rx_thread_stack[arc_id]),
                        SOCK_TO_IMQ_THREAD_PRIO, 
                        SOCK_TO_IMQ_THREAD_PRIO,
                        TX_NO_TIME_SLICE, TX_AUTO_START);
  if ( trv != TX_SUCCESS ) {
    fprintf( stderr, "Failed to create sock2imq_rx server\n");
  }

  /* Create a thread to run rx managment server server */
  trv = tx_thread_create(&rx_mngt_thread[arc_id], "sock2imq_mngt_rx",
                        imq_mngt_rx_thread, arc_id,
                        rx_mngt_stack[arc_id],
                        sizeof(rx_mngt_stack[arc_id]),
                        IMQ_MNGT_THREAD_PRIO, 
                        IMQ_MNGT_THREAD_PRIO,
                        TX_NO_TIME_SLICE, TX_AUTO_START);
  if ( trv != TX_SUCCESS ) {
    fprintf( stderr, "Failed to create sock2imq_mngt_rx server\n");
  }

  
  
  return;
}




static void create_socket_server(ULONG input)
{
  int                     server_sock, client_sock, rc;
  
  struct sockaddr_in      server, client;
	socket_info_t   			  *new_sck  			= NULL;

  int sock_port   = (int) input;
  int imq_addr    = 0;
  int arc_id      = 0;
  
  if ( (sock_port < ARM_SCK_PORT) || (sock_port >ARC2_SCK_PORT) ) {
    fprintf( stderr, "ERROR : socket is unsupported");
    return;
  }
  if (sock_port == ARC1_SCK_PORT ) {
    imq_addr = 0;
    arc_id = 0;
  }
  else if (sock_port == ARC2_SCK_PORT )  {
    imq_addr = 2;
    arc_id = 1;
  }

  printf( "Config server on port %d for arc %d, imq %d\n", sock_port, arc_id+1, imq_addr);
  
  rc = imq_connect( &arc_imq_socket_mng[arc_id], imq_addr, &atlk_wait_forever );
  if ( atlk_error(rc) ) {
    syslog( LOG_ERR , "imq_connect Failed with error %s\n", atlk_rc_to_str(rc) );
    return;
  }
  
  rc = imq_connect( &arc_imq_socket_data[arc_id], (imq_addr+1), &atlk_wait_forever );
  if ( atlk_error(rc) ) {
    syslog( LOG_ERR , "imq_connect for data failed with error %s\n", atlk_rc_to_str(rc) );
    return;
  }
  

  server_sock = socket(AF_INET, SOCK_STREAM, 0);
  if ( server_sock < 0 ) {
    printf( "ERROR : Failed to create socket");
    return;
  }

  memset(&server, 0, sizeof(server));
  server.sin_family = AF_INET;
  server.sin_addr.s_addr = 0;
  server.sin_port = htons(sock_port);
  
  rc = bind(server_sock, (struct sockaddr *) &server, sizeof(server));
  if ( rc < 0) {
    printf("ERROR : failed to bind the socket\n");
    return;
  }

  rc = listen(server_sock, 1);
  if ( rc < 0) {
    printf( "ERROR : Failed to listen socket");
    return;
  }

  syslog( LOG_INFO,  "Starting cli server loop on port %d", sock_port );

  
  while( 1 ) {

    int                   client_len = sizeof(client);
    sck_imq_msg_t         msg;
    
    client_sock = accept(server_sock, (struct sockaddr *)&client, &client_len );
    if (client_sock < 0) {
			syslog( LOG_ERR, " * client_sock is with error, Connection Failed\n");
			break;
		}

    /* Set socket to non-blocking ? */
    int optval = NX_NO_WAIT;
    rc = setsockopt(client_sock, SOL_SOCKET, SO_RCVTIMEO, &optval, sizeof(optval) );
    if ( rc < 0 ) {
      syslog( LOG_ERR, " Error : Failed to set setsockopt socket to non-blocking\n");
    }

		optval = NX_TRUE;
    rc = ioctl( client_sock, FIONBIO , &optval );
    if ( rc < 0 ) {
      syslog( LOG_ERR, " Error : Failed to set ioctl socket to non-blocking\n");
    }
    
    
		/* Create new cli on arc thread information */
		new_sck = calloc(1, sizeof(socket_info_t) );
		if (new_sck == NULL) {
		 syslog( LOG_ERR, "Error alloc data for new thread\n");
		 abort();
	  }

		new_sck->socket = client_sock;
		new_sck->idx = ntohs(client.sin_port);
		new_sck->is_active = 1;
    

    msg.opcode = SOCK_IMQ_CREATE_CLI;
    msg.socket = client_sock;
    msg.sock_port = new_sck->idx;
    msg.len = 0;
    memset( &msg.buffer, 0 , sizeof(msg.buffer) );
    
    rc = imq_send( &arc_imq_socket_mng[arc_id], (void*)(char*) &msg, sizeof(sck_imq_msg_t), NULL );
    if (atlk_error(rc)) {
      syslog( LOG_ERR , "ERROR : Failed to send imq command to create CLI, %s\n", atlk_rc_to_str(rc) );
    }

		list_add( &new_sck->list, &sockets[arc_id]);

		//threads_garbage_collector();
    
  }
	
  return;
  
}


/* This thread is receiving data from IMQ and send it to socket */
static void sock_tx_thread(ULONG input)
{
  atlk_rc_t         rc    = ATLK_OK;
  int               flags = 0;
  socket_info_t			*curr, *temp;
  int               arc_id              = (int)input;
  
  syslog( LOG_INFO,  "Starting thread sock_tx_thread on arc %d", arc_id );

  while (1) {
  
    char rx_buf[IMQ_CLI_QUEUE_MTU];
    size_t rx_size = IMQ_CLI_QUEUE_MTU;
    sck_imq_msg_t   msg;
    size_t          len           = sizeof(sck_imq_msg_t);


    rc = imq_receive(&arc_imq_socket_data[arc_id], rx_buf, &rx_size, &atlk_wait_forever);
    if ( atlk_error(rc) ) {
			syslog( LOG_ERR,	"ERROR@ARM : imq_receive: %s\n", atlk_rc_to_str(rc));
      tx_thread_sleep(200);
      continue;
    }

    if ( rx_size != len ) {
      syslog( LOG_ERR,  "ERROR@ARM : Received len error, expcted %d, recevied %d", len, rx_size); 
    }
    
    memcpy( &msg, &rx_buf, len );
    /* search current socket */
    list_for_each_entry_safe(curr, temp, &sockets[arc_id], list) {

      if (curr->is_active) {
        if ( msg.socket == curr->socket ) {
          rc = send(curr->socket, (char*)&msg.buffer, msg.len, flags);
        }
      }
    }
  }
  
  return;
}


static void imq_mngt_rx_thread( ULONG input )
{ 
  atlk_rc_t         rc    = ATLK_OK;
  socket_info_t			*curr, *temp;
  int               arc_id              = (int)input;

  while (1) {

    char            rx_buf[IMQ_CLI_QUEUE_MTU]       = {0};
    size_t          rx_size                         = IMQ_CLI_QUEUE_MTU;
    sck_imq_msg_t   msg;
    size_t          len           = sizeof(sck_imq_msg_t);


    rc = imq_receive(&arc_imq_socket_mng[arc_id], rx_buf, &rx_size, &atlk_wait_forever);
    if (atlk_error(rc)) {
      syslog( LOG_ERR , "ERROR : Failed to send imq command to create CLI, %s\n", atlk_rc_to_str(rc) );
    }

    /* Copy data to msg time */
    memcpy( &msg, &rx_buf, len );
    

    list_for_each_entry_safe(curr, temp, &sockets[arc_id], list) {

      if (!curr->is_active) {
        continue;
      }
      
      if ( msg.socket == curr->socket ) {
        if ( msg.opcode == SOCK_IMQ_DELETE_CLI) {
          
          curr->is_active = 0;
          soc_close( curr->socket );
          list_del(&curr->list);
      		free(curr);
        }
        else {
          printf( "Error : Managment command unknown : %d from %d\n", msg.opcode, msg.socket );
        }
      }
      
    }
    
  }
  
  return;

}


static void sock_rx_thread(ULONG input)
{
  int               rc    = ATLK_OK;
  socket_info_t			*curr, *temp;
  int               arc_id              = (int)input;
  
  syslog( LOG_INFO,  "Starting thread sock_rx_thread on arc %d", arc_id );

  while (1) {

    char            rx_buf[MAX_BUFFER_SIZE];
    size_t          rx_size       = MAX_BUFFER_SIZE;
    sck_imq_msg_t   msg = {0};
    size_t          len           = sizeof(sck_imq_msg_t);
    
    
    list_for_each_entry_safe(curr, temp, &sockets[arc_id], list) {

      if ( curr->is_active ) {

        rc = recv( curr->socket, &rx_buf, rx_size, 0 );
        if ( rc <= 0 ) {
          continue;
        }

        msg.opcode = SOCK_IMQ_DATA;
        msg.socket = curr->socket;
        msg.sock_port = curr->idx;
        msg.len = rc;
        memcpy( &msg.buffer, &rx_buf, rc );

        syslog( LOG_DEBUG, "Sending to ARC msg, socket %d, msg size %d, msg ", msg.socket, msg.len );
        rc = imq_send( &arc_imq_socket_data[arc_id], (void*) &msg, len, NULL);

        if (atlk_error(rc)) {
          syslog( LOG_ERR , "sock_rx_thread, imq_send failed, error %s\n", atlk_rc_to_str(rc) );
          continue;
        }
      }
    }
    /* in case no cli, do not create overload process */
    tx_thread_sleep(1);
    
  }
  
  return;
 
}
