#ifndef _SOCK_TO_IMQ_H__
#define _SOCK_TO_IMQ_H__

#include "../../common/queue.h"


#define TOTAL_ARCS  2
#define ARC_1_ID    1
#define ARC_2_ID    2


#define ARM_ARC1_MNGT_IMQ_ID    0
#define ARM_ARC1_DATA_IMQ_ID    (ARM_ARC1_MNGT_IMQ_ID + 1)

#define ARM_ARC2_MNGT_IMQ_ID    2
#define ARM_ARC2_DATA_IMQ_ID    (ARM_ARC2_MNGT_IMQ_ID+1)

  #define CLI_MNGT_IMQ      0
  #define CLI_DATA_IMQ      1



#if	defined(__CRATON_ARC1)
  #define ARC_ID            ARC_1_ID
  #define IMQ_IDX_START     0
#elif defined(__CRATON_ARC2)
  #define ARC_ID            ARC_2_ID
  #define IMQ_IDX_START     2
#else 
  #undef ARC_ID            
  #undef CLI_MNGT_IMQ      
  #undef CLI_DATA_IMQ      
#endif


#define ARM_SCK_PORT  8000
#define ARC1_SCK_PORT (ARM_SCK_PORT+1)
#define ARC2_SCK_PORT (ARC1_SCK_PORT+1)





// #define IMQ_CLI_BASE_ADDRESS 10
#define IMQ_MNGT_THREAD_PRIO 50
#define SOCK_TO_IMQ_THREAD_PRIO 30
#define IMQ_RX_TX_THREAD_PRIO   20
#define IMQ_RX_TX_THREAD_TIME_SLICE 50

void qa_cli_arm( int arc_id );



#define TOTAL_CLI_IMQ     2



#define SOCK_IMQ_CREATE_CLI 	0
#define SOCK_IMQ_DELETE_CLI		1
#define SOCK_IMQ_DATA			    2


#define MAX_BUFFER_SIZE  200

typedef struct _sock_imq_ {

	char			        opcode; /* sock to imq value */
	int				        socket;
	short			        sock_port;
  short             len;
	char			        buffer[MAX_BUFFER_SIZE];

} sck_imq_msg_t;


#define IMQ_CLI_QUEUE_MTU sizeof(sck_imq_msg_t)
#define MAX_IMQ_MEM_SIZE  (32 * 1024)
#define IMQ_CLI_QUEUE_LENGTH (MAX_IMQ_MEM_SIZE / IMQ_CLI_QUEUE_MTU)



#endif /* _SOCK_TO_IMQ_H__ */

