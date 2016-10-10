#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "../libcli/libcli.h"
#include <atlk/v2x/wave.h>
#include "../v2x_cli/v2x_cli.h"

    
static v2x_se_t se = V2X_SE_INIT;   /* V2X session */

int cli_v2x_session_open( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
  /* V2X API return code */
  v2x_rc_t rc = V2X_OK;
  
 /* Open V2X session */
  rc = v2x_se_open(&se, NULL);
  if (v2x_failed(rc)) {
    cli_print(cli, "v2x_se_open: %s\n", v2x_rc_to_str(rc));
    goto exit;
  }

exit:
  return v2x_failed(rc);
}

int cli_v2x_session_close( struct cli_def *cli, UNUSED(const char *command), UNUSED(char *argv[]), UNUSED(int argc) ) 
{
  v2x_se_close(&se);
  cli_print(cli, "Session Closed");
  
  return CLI_OK;
}

v2x_se_t *cli_v2x_get_session( UNUSED(int idx) ) 
{
  return &se;
}
