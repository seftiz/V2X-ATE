#ifndef _CAN_FEEDER_H_
#define _CAN_FEEDER_H_

#include <atlk/sdk.h>
#include <atlk/os.h>
#include <atlk/can.h>

/** CAN feeder configuration parameters */
typedef struct {
  /** CAN feeder thread scheduling parameters */
  atlk_thread_sched_t sched_params;

  /** CAN device ID to receive from */
  can_device_id_t device_id;

} can_feeder_config_t;

/**
  Init CAN feeder.

  @param[in] config CAN feeder configuration parameters

  @retval ::ATLK_OK if succeeded
  @return Error code if failed
*/
atlk_rc_t atlk_must_check
can_feeder_init(const can_feeder_config_t *config);

#endif /* _CAN_FEEDER_HPP */
