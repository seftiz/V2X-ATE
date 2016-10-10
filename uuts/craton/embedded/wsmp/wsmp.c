#include <stdio.h>
#include <string.h>
#include <unistd.h>


#include "../libcli/libcli.h"
#include <atlk/v2x/wave.h>
#include "../v2x_cli/v2x_cli.h"
#include "../session/session.h"
#include "wsmp.h"


#define DEFAULT_PSID  0xc01234
    
/* Globals */

static v2x_sk_t sk = V2X_SK_INIT;  /* V2X socket */

int cli_v2x_wsmp_sk_open( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc ) 
{
  v2x_wsmp_sk_attr_t    wsmp_sk_attr = V2X_WSMP_SK_ATTR_INIT; /* WSMP socket attributes */
  int32_t               i     = 0;
  v2x_rc_t              rc    = V2X_OK;
 
  wsmp_sk_attr.psid = DEFAULT_PSID;
  wsmp_sk_attr.sk_attr.rx_disable = 1;
  
  IS_HELP_ARG("wsmp open [-psid 1234] [disable-rx true|false]")

  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  /*
  if (mode == SEND) {
    wsmp_sk_attr.sk_attr.disable_rx = 1;
  }
  */
  for ( i = 0 ; i < argc; i += 2 ) {
    
    GET_INT("-psid", wsmp_sk_attr.psid, i, "Specify the socket psid");
    GET_INT("-disable-rx", wsmp_sk_attr.sk_attr.rx_disable, i, "Specify if socket is for sending only");
    
  }
  
  rc = v2x_wsmp_open(&sk, cli_v2x_get_session(0) , &wsmp_sk_attr);
  if (v2x_failed(rc)) {
    cli_print(cli, "v2x_wsmp_open: %s\n", v2x_rc_to_str(rc));
    goto exit;
  }
  
exit:
  return v2x_failed(rc);
}

int cli_v2x_wsmp_sk_close( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
  
  v2x_sk_close(&sk);
  cli_print(cli, "Socket closed\n" );
  
  return CLI_OK;
  
}

int cli_v2x_wsmp_send_frame( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc )
{
  int32_t       num_frames = 1;     /* total num frames to send */
  int32_t       rate_hz = 1;        /* rate of sending frames   */

  /* A message we'll use for the sake of this example */
  int8_t        wsmp_msg[] = "Autotalks - Confidence of Knowing Ahead\n";

  /* V2X API return code */
  v2x_rc_t      rc = V2X_OK;
  
  /* WSMP TX descriptor */
  v2x_wsmp_tx_t wsmp_tx = V2X_WSMP_TX_INIT;
  /* MAC TX descriptor */
  v2x_mac_tx_t  mac_tx = V2X_MAC_TX_INIT;
  /* TX buffer descriptor */
  v2x_tx_buf_t  tx_buf = V2X_TX_BUF_INIT;
  
  int i;
  
  
  IS_HELP_ARG("send_frame wsmp [-frames 1- ...] [-rate_hz 1 - ...] [-data_rate 54,54,45] [-interface_idx 0|1] [power_dbm8 -20-20] [-psid 0xc01234] \n \
                                            [elem_id 1-23] [-tx_power_used -100-80] [-element_data_rate 1]" );
                                            
  CHECK_NUM_ARGS /* make sure all parameter are there */
  
  /* define defaults for all frame options */
  
  num_frames = 1; /* Default : Send 1 frame */
  rate_hz = 1; /* Send Frame every 1 second */

  /* mac_tx.user_prio = V2X_USER_PRIO_MAX; */
  
  /* Use System Default */
#ifndef __USE_API_DEFAULTS__
 
  mac_tx.datarate = V2X_DATARATE_9MBPS;
  mac_tx.if_num = 0;
  mac_tx.power_dbm8 = -10;
  wsmp_tx.psid = DEFAULT_PSID;
  // REMOVED@2.1 wsmp_tx.elem_id = V2X_WSMP_ELEM_WSM;
  wsmp_tx.ext_elem.set_tx_power_used = 1;
  wsmp_tx.ext_elem.set_datarate = 1;
  /* wsmp_tx.ext_elem.set_channel_num = 1; */
#endif
  
  for ( i = 0 ; i < argc; i += 2 ) {
    
    GET_INT("-frames", num_frames, i, "Specify the number of frames to send");
    GET_INT("-rate-hz", rate_hz, i, "Specify the rate of frames to send");
    /* mac information override defaults */
    /* GET_INT("-user_priority", mac_tx.user_prio, i, "Specify the frame user priority, range 0-7"); */
    GET_INT("-data-rate", mac_tx.datarate, i, "Specify the frame user priority, range 0:7");
    GET_INT("-interface-idx", mac_tx.if_index, i, "Sets mac interface idx to transmit from, 0-1");
    GET_INT("-power-dbm8", mac_tx.power_dbm8, i, "Sets the mac interface to transmit from");
    /* wsmp tx parameters */
    GET_INT("-psid", wsmp_tx.psid, i, "set wsmp psid value");
    // REMOVED@2.1 GET_INT("-elem-id", wsmp_tx.elem_id, i, "set element idx");
    GET_INT("-set-tx-power-used", wsmp_tx.ext_elem.set_tx_power_used, i, "set tx_power_used field in wsmp message");
    GET_INT("-element-data-rate", wsmp_tx.ext_elem.set_datarate, i, "set tx_power_used field in wsmp message");
    /* GET_INT("-element_channel_num", wsmp_tx.ext_elem.set_channel_num, i, "set channel number to sent frame from"); */
  } 

  /* Set payload pointer & size */
  v2x_tx_buf_set(&tx_buf, wsmp_msg, sizeof(wsmp_msg));

  for (i = 0; i < num_frames; ++i) {
    /* Transmit WSMP */
    rc = v2x_wsmp_tx(&sk, &tx_buf, 0, &wsmp_tx, &mac_tx);
    if (v2x_failed(rc)) {
      cli_print(cli, "v2x_wsmp_tx: %s\n", v2x_rc_to_str(rc));
      return rc;
    }
 
    /* Sleep 100 ms between transmissions */
    if ( (num_frames >= 1) && (rate_hz >= 1) ){
      int sleep_time_uSec = (1e6 / rate_hz );
      usleep( sleep_time_uSec );
    }
    
  }

  return CLI_OK;

}
