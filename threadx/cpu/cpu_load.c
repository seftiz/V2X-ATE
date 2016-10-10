
#ifdef __THREADX__


#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "../../common/v2x_cli/v2x_cli.h"

	
int cli_v2x_cpu_load_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )
{
  atlk_rc_t      	rc 					= ATLK_OK;
	int						 	i 	= 0,
									timeout  		= -1,
									num_iter = 20000, /* set default to 50% */
									sleep_ticks = 1, 
									cpu_load = -1,
									rx_timeout = 0;
									
	struct timeval start, current;
  
  /* get user context */
  //user_context *myctx = (user_context *) cli_get_context(cli);
  
	IS_HELP_ARG("cpu-load -timeout (0-1e6) [-load 0-100 | [-num_iter 0-1e6] [-sleep_ticks 0-999] ]");

	CHECK_NUM_ARGS /* make sure all parameter are there */
	
  for ( i = 0 ; i < argc; i += 2 ) {
    GET_INT("-timeout", timeout, i, "Set time out for cpu loop ");
    GET_INT("-num_iter", num_iter, i, "Number of iteration in asm nop ");
    GET_INT("-sleep_ticks", sleep_ticks, i, "Number sleep ticks to free resources ");
		GET_INT("-load", cpu_load, i, "Cpu load in precent ");
  } 

	gettimeofday (&start, NULL);	
	current = start;
	
	if ( cpu_load > 0 ) {
		num_iter = (int) 400 * cpu_load;
	}
	
	do {
	/*
		int status;
		ULONG t1, t2;
		
		status = tx_interrupt_control(TX_INT_DISABLE);
		__asm__ __volatile__ ("MRC p15, 0, %0, c9, c13, 0\n" : "=r"(t1));
		*/
		for (int i = 0; i < num_iter; i++) {
			__asm__ __volatile__("nop");
		}
		/*
		__asm__ __volatile__ ("MRC p15, 0, %0, c9, c13, 0\n" : "=r"(t2));
		
		tx_interrupt_control(status);
		status = t2 - t1;
		cli_print( cli, "Num Iteration %d, total ticks %u", num_iter, status);
		*/
		tx_thread_sleep( sleep_ticks );
		
		if ( timeout > 0 ) { 
			gettimeofday (&current, NULL);	
			double elapsedTime = (current.tv_sec - start.tv_sec);
			if ( elapsedTime > timeout ) {
				rx_timeout = 1;
			}
		}
		
		
		
	} while ( !rx_timeout ); 

  return rc;
}	

int cli_v2x_set_thread_name( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) {
 /* V2X API return code */
  atlk_rc_t      rc = ATLK_OK;
  TX_THREAD *my_thread_ptr;
	
  /* get user context */
  user_context *myctx = (user_context *) cli_get_context(cli);
  
  IS_HELP_ARG("cntx -name thread_name");
	
  CHECK_NUM_ARGS /* make sure all parameter are there */

	/* Find out who we are! */
	my_thread_ptr = tx_thread_identify();
	
	GET_STRING_VALUE("-name", myctx->user_context_name,"Set contect name");
	
	if ( my_thread_ptr != NULL ) {
		my_thread_ptr->tx_thread_name = myctx->user_context_name; 
	}
	
	cli_print( cli, "thread addr :0x%x" , (int) my_thread_ptr );
		
	return rc;
}

int cli_v2x_thread_kill( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) {
 /* V2X API return code */
  atlk_rc_t      rc = ATLK_OK;
	unsigned int	thread_addr = 0;
  int						i=0;
	UINT  				status;
	
  
  IS_HELP_ARG("thread kill -addr 0xNNNNNNNNNN");
	
  CHECK_NUM_ARGS /* make sure all parameter are there */

	for ( i = 0 ; i < argc; i += 2 ) {
    GET_TYPE_INT("-addr", thread_addr, unsigned int, i, "Thread address", "%x" );
  } 
	
	
	if ( thread_addr > 0 ) {
	  TX_THREAD 		*my_thread_ptr;
		
		my_thread_ptr = (TX_THREAD*) thread_addr;
		
		status =  tx_thread_terminate(my_thread_ptr);
		if ( status != TX_SUCCESS ) {
			cli_print( cli, "ERROR : failed to kill thread at %x", thread_addr );
		}
		status = tx_thread_delete(my_thread_ptr);
		if ( status != TX_SUCCESS ) {
			cli_print( cli, "ERROR : failed to delete thread at %x", thread_addr );
		}
		
	}
		
	return rc;
}


int cli_v2x_thread_suspend( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
 /* V2X API return code */
  atlk_rc_t      rc = ATLK_OK;
	unsigned int	thread_addr = 0;
  int						i=0;
	UINT  				status;
	
  
  IS_HELP_ARG("thread suspend -addr 0xNNNNNNNNNN");
	
  CHECK_NUM_ARGS /* make sure all parameter are there */

	for ( i = 0 ; i < argc; i += 2 ) {
    GET_TYPE_INT("-addr", thread_addr, unsigned int, i, "Thread address", "%x" );
  } 
	
	
	if ( thread_addr > 0 ) {
	  TX_THREAD 		*my_thread_ptr;
		
		my_thread_ptr = (TX_THREAD*) thread_addr;
		
		status =  tx_thread_suspend(my_thread_ptr);
		if ( status != TX_SUCCESS ) {
		 cli_print( cli, "ERROR : failed to kill thread at %x", thread_addr );
		}
		
	}
		
	return rc;
}


int cli_v2x_thread_resume( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )
{
 /* V2X API return code */
  atlk_rc_t      rc = ATLK_OK;
	unsigned int	thread_addr = 0;
  int						i=0;
	UINT  				status;
	
  
  IS_HELP_ARG("thread resume -addr 0xNNNNNNNNNN");
	
  CHECK_NUM_ARGS /* make sure all parameter are there */

	for ( i = 0 ; i < argc; i += 2 ) {
    GET_TYPE_INT("-addr", thread_addr, unsigned int, i, "Thread address", "%x" );
  } 
	
	
	if ( thread_addr > 0 ) {
	  TX_THREAD 		*my_thread_ptr;
		
		my_thread_ptr = (TX_THREAD*) thread_addr;
		
		status =  tx_thread_resume(my_thread_ptr);
		if ( status != TX_SUCCESS ) {
		 cli_print( cli, "ERROR : failed to kill thread at %x", thread_addr );
		}
		
	}
		
	return rc;
}

#endif