#include <stdio.h>
#include <sys/types.h>
#ifdef WIN32
#include <winsock2.h>
#include <windows.h>
#elif defined(THREADX)
#include <nx_bsd.h>
#include <atlk/common.h>
#include <atlk/craton.h>
#else 
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#endif
#include <signal.h>
#include <strings.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include "../libcli/libcli.h"
#include "../session/session.h"
#include "../wsmp/wsmp.h"
#include "../gps_simulator/gps.h"
#include "../nav_api/nav_api.h"

// todo - do we need craton_netx_init(NX_THREAD_PRIO)
// or is it done 4 us???

#ifdef THREADX
void connection_handler(ULONG socket_desc);
#else
void *connection_handler(void *socket_desc);
#endif /* THREADX*/


int cmd_config_int_exit(struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc))
{
    cli_set_configmode(cli, MODE_CONFIG, NULL);
    return CLI_OK;
}


int check_auth(const char *username, const char *password)
{
    if (strcasecmp(username, USERNAME) != 0)
        return CLI_ERROR;
    if (strcasecmp(password, PASSWORD) != 0)
        return CLI_ERROR;
    return CLI_OK;
}

int check_enable(const char *password)
{
    return !strcasecmp(password, PASSWORD);
}

int idle_timeout(struct cli_def *cli)
{
  cli_print(cli, "Custom idle timeout");
  return CLI_QUIT;
}

void pc(UNUSED(struct cli_def *cli), const char *string)
{
    printf("%s\n", string);
}

int show_version( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
  cli_print( cli, "Version : 0.0.0" );
  return CLI_OK;
}


int create_cli_struct( struct cli_def **cli )
{
  struct cli_command    *c        = NULL; //, *int_gps  = NULL;
  FILE                  *fh       = NULL;

   *cli = cli_init();

   cli_set_hostname(*cli, "v2x >");
   cli_set_banner(*cli, "Autotalks - Confidence of Knowing Ahead.\nWelcome to Auto-talks V2X cli\n\n");
   
   cli_telnet_protocol(*cli, 1);

  cli_regular(*cli, regular_callback);
  cli_regular_interval(*cli, 5); // Defaults to 1 second
  cli_set_idle_timeout_callback(*cli, 0, idle_timeout); /* 5 Minutes idle timeout */


  c = cli_register_command(*cli, NULL, "show", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, NULL);
  cli_register_command(*cli, c, "version", show_version, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Show version");

  /*
  c = cli_register_command(*cli, NULL, "session", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, NULL);
  cli_register_command(*cli, c, "open", cli_v2x_session_open, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "open session");
  cli_register_command(*cli, c, "close", cli_v2x_session_close, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "close session");
  */
  /* handle wsmp command */
  /*
  c = cli_register_command(*cli, NULL, "wsmp", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "send message frame via SDK");
  cli_register_command(*cli, c, "open", cli_v2x_wsmp_sk_open, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "open wsmp new socket");
  cli_register_command(*cli, c, "close", cli_v2x_wsmp_sk_close, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "close wsmp socket");
  cli_register_command(*cli, c, "tx", cli_v2x_wsmp_send_frame, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Transmit Data via wsmp socket");
  */
  /* handle gps command */
  /*
  c = cli_register_command(*cli, NULL, "nav", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Navigation API operations");
  cli_register_command(*cli, c, "init", cli_v2x_nav_init, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "init nav api");
  cli_register_command(*cli, c, "start", cli_v2x_nav_start, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "start nav api handler");
  cli_register_command(*cli, c, "stop", cli_v2x_nav_stop, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "start nav api handler");
 
  
  int_gps = cli_register_command(*cli, c, "internal-gps", NULL, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "Handle inte");
  cli_register_command(*cli, int_gps, "start", cli_v2x_gps_start, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "start gps simulator");
  cli_register_command(*cli, int_gps, "stop", cli_v2x_gps_stop, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "stop gps simulator");
  cli_register_command(*cli, int_gps, "inject", cli_v2x_gps_inject, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "set gps data");
  cli_register_command(*cli, int_gps, "config", cli_v2x_gps_config, PRIVILEGE_UNPRIVILEGED, MODE_EXEC, "set gps configuration parameters");
  */
  

  cli_set_auth_callback(*cli, check_auth);
  cli_set_enable_callback(*cli, check_enable);

  /* Test reading from a file */
  if ((fh = fopen("clitest.txt", "r"))) {
    /* This sets a callback which just displays the cli_print() text to stdout */
     cli_print_callback(*cli, pc);
     cli_file(*cli, fh, PRIVILEGE_UNPRIVILEGED, MODE_EXEC);
     cli_print_callback(*cli, NULL);
    fclose(fh);
  }
  
  return 0;

}
#ifdef THREADX
  #define CLI_THREAD_STACKSIZE 1024*16
  static uint8_t cli_thread_stack[100][CLI_THREAD_STACKSIZE];
  #define CLI_THREAD_PRIO 30
  #define CLI_THREAD_TIME_SLICE 50
#endif 

int main( )
{
            
  int                   s, client_sock , sck_size;
  struct sockaddr_in    server, client;  
#ifdef THREADX
  TX_THREAD                   cli_threads[100];
  int rc = 0; 
#else
  pthread_t             cli_threads[100];
  int                   on = 1;
#endif 
  int                   thread_cnt      = 0;
  

  signal(SIGCHLD, SIG_IGN);

  if ((s = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
#ifndef THREADX
    perror("socket");
#endif 
    return 1;
  }
  
#ifndef THREADX
  setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));
#endif 

  memset(&server, 0, sizeof(server));
  server.sin_family = AF_INET;
#ifdef THREADX
  server.sin_addr.s_addr = htonl(0);
#else
  server.sin_addr.s_addr = htonl(INADDR_ANY);
#endif /* THREADX */
  server.sin_port = htons(CLITEST_PORT);
  if (bind(s, (struct sockaddr *) &server, sizeof(server)) < 0) {
#ifndef THREADX
    perror("bind");
#endif 
    return 1;
  }

#ifdef THREADX
  if (listen(s, 1) < 0) {
#else
  if (listen(s, 50) < 0) {
    perror("listen");
#endif 
    return 1;
  }

  printf("Listening on port %d\n", CLITEST_PORT);
  sck_size = sizeof(struct sockaddr_in);
  while( (client_sock = accept(s, (struct sockaddr *)&client, (socklen_t*)&sck_size)) ) {

#ifdef THREADX
  rc = tx_thread_create(&cli_threads[thread_cnt], "cli_thread",
                        connection_handler, (ULONG)&client_sock,
                        cli_thread_stack[thread_cnt],
                        CLI_THREAD_STACKSIZE,
                        CLI_THREAD_PRIO, CLI_THREAD_PRIO,
                       CLI_THREAD_TIME_SLICE, TX_AUTO_START);
  BUG_ON(rc != TX_SUCCESS);

#else 

    //pthread_t cli_thread;
    pthread_attr_t attr;
    size_t stacksize = 1024*16;

    //new_sock = malloc(1);
    //*new_sock = client_sock;
    
    pthread_attr_init(&attr);
    pthread_attr_setstacksize(&attr, stacksize);


    if( pthread_create( &cli_threads[thread_cnt] , &attr ,  connection_handler , (void*) &client_sock) < 0) {
      perror("could not create thread");
      return (-1);
    }
#endif /* THREADX */

    if (client_sock > 0)
    {
      socklen_t len = sizeof(server);
      if (getpeername(client_sock, (struct sockaddr *) &server, &len) >= 0)
        printf(" * accepted connection from %s, sock id : %d\n", inet_ntoa(server.sin_addr), client_sock);
    }

    //Now join the thread , so that we dont terminate before the thread
    // pthread_join( cli_thread , NULL);
    puts("Handler assigned");
    thread_cnt++;

  }

  if (client_sock < 0) {
#ifndef THREADX
    perror("accept failed");
#endif 
    return 1;
  }
	return 0;
}

/*
 * This will handle connection for each client
 * */
#ifdef THREADX
void connection_handler(ULONG socket_desc)
#else
void *connection_handler(void *socket_desc)
#endif /* THREADX*/
{
	//Get the socket descriptor
#ifdef THREADX
  int sock = (int)socket_desc;
#else 
	int sock = *(int*)socket_desc;
#endif /* THREADX*/
  struct cli_def *cli = NULL;
  
  create_cli_struct( &cli );

  cli_loop(cli, sock);
  //shutdown(sock, SD_BOTH)
    
  //Free the socket pointer
  //free(socket_desc);

  //cli_done(cli);

#ifndef THREADX
  pthread_exit(0);
  
  return (void*) NULL;
#endif
}
