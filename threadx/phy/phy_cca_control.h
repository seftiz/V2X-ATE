#ifndef __V2X_PHY_CCA_CONTROL_H__
#define __V2X_PHY_CCA_CONTROL_H__


int cli_v2x_phy_cca_control_start( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );
int cli_v2x_phy_cca_set( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc );

// int cli_v2x_hwregs( struct cli_def *cli, UNUSED(const char *command), char *argv[], int argc);

#endif