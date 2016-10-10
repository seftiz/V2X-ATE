#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <string.h>

#include <tx_api.h>

#include <atlk/sdk.h>
#include <atlk/can_service.h>

#include <craton/syslog.h>

#include "common.h"
#include "can_feeder.h"


/* CAN receive thread */
static TX_THREAD can_receive_thread;
static uint8_t can_receive_thread_stack[0x4000];
static void can_receive_thread_entry(ULONG input);

/* CAN service */
static can_service_t *can_service = NULL;

/* CAN socket */
static can_socket_t *can_socket = NULL;


/* CAN ID filter array -- NO filtering */
static const can_id_filter_t filter_array[] = {{ 0, 0 }};

#ifdef __CRATON_ARC2
void craton_user_init( void ) 
{

	can_feeder_config_t config;
  config.sched_params.priority = 30;
  config.sched_params.time_slice = 0;
  config.device_id = 1;
	
  if (atlk_error(can_feeder_init(&config))) {
    abort();
  }
}
#endif


/* Init CAN feeder */
atlk_rc_t atlk_must_check
can_feeder_init(const can_feeder_config_t *config)
{
  /* ThreadX return value */
  ULONG trv;
  /* Autotalks return code */
  atlk_rc_t rc = ATLK_OK;
  /* CAN socket configuration */
  can_socket_config_t socket_config;

  /* Verify mandatory function arguments */
  if (atlk_unlikely(!config)) {
    TR_ERROR_NO_ARGS("Mandatory argument is missing.");
    return ATLK_E_INVALID_ARG;
  }

  /* Get default CAN service instance */
  rc = can_default_service_get(&can_service);
  if (atlk_error(rc)) {
    TR_ERROR("can_default_service_get: %s", atlk_rc_to_str(rc));
    goto error;
  }

  /* Set socket configuration */
  socket_config.device_id = config->device_id;
  socket_config.filter_array_ptr = filter_array;
  socket_config.filter_array_size = 1;

  /* Create CAN socket */
  rc = can_socket_create(can_service, &can_socket, &socket_config);
  if (atlk_error(rc)) {
    TR_ERROR("can_socket_create: %s", atlk_rc_to_str(rc));
    goto error;
  }

  /* Create CAN receive thread */
  trv = tx_thread_create(&can_receive_thread, (char *)"qa_can_rcv_app",
                         can_receive_thread_entry, 0,
                         can_receive_thread_stack,
                         sizeof(can_receive_thread_stack),
                         config->sched_params.priority,
                         config->sched_params.priority,
                         config->sched_params.time_slice, TX_AUTO_START);
  if (atlk_unlikely(trv != TX_SUCCESS)) {
    TR_ERROR("tx_thread_create failed, trv=0x%lx", trv);
    abort();
  }

  return rc;

error:
  can_socket_delete(can_socket);
  can_service_delete(can_service);
  return rc;
}

/* SSUData array size; aligned with can_data_decoder.c */
#define SSUDATA_ARRAY_SIZE 3

static void
can_receive_thread_entry(ULONG input)
{
  /* Not using input */
  (void)input;
     
  while (1) {
    /* Autotalks return code */
    atlk_rc_t rc = ATLK_OK;
    /* Received CAN message data */
    uint8_t data[CAN_DATA_SIZE_MAX];
    /* Received CAN message data size */
    size_t data_size = sizeof(data);
    /* Received CAN ID */
    can_id_t can_id;

    /* Receive CAN message */
		rc = can_receive(can_socket, data, &data_size, &can_id, &atlk_wait_forever);
		if (atlk_error(rc)) {
				TR_INFO("can_receive: %s", atlk_rc_to_str(rc));
				continue;
		}
    // TR_DEBUG("Received CAN ID 0x%x", (unsigned int)can_id);
		
		TR_INFO( "Can : Id %d, size %d, data : %02x %02x %02x %02x %02x %02x %02x %02x", can_id, data_size, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]);
  }
}
