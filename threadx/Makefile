
#export SDK_DIR := /docs/ATE/fw_releases/sdk-4.3.0-beta7-mc-i686-linux-gnu
#export COMMON := ../common


include $(SDK_DIR)/build/rules.mk
include $(SDK_DIR)/build/craton.mk
include $(SDK_DIR)/build/u-boot.mk

CFLAGS := -Wall -Wextra -Werror -g -Os -std=c99
# CFLAGS := -std=c99 -pedantic -Wall -Wextra -Werror -g -Os
LDFLAGS := -lcraton -lm



ifeq ($(CRATON_NO_ARC),)

.DEFAULT_GOAL := arm/img/qa-mc.img

arm/bin/qa-mc: \
	$(SDK_DIR)/board/$(BOARD)/arm/lib/ref-sys.o \
	arm/obj/$(COMMON)/general/general.o \
	arm/obj/$(COMMON)/nav_api/nav_api.o \
	arm/obj/$(COMMON)/link/link.o \
	arm/obj/$(COMMON)/management/mng_api.o \
	arm/obj/phy/phy_cca_control.o \
	arm/obj/cpu/cpu_load.o \
	arm/obj/loopbacks/eth_loopback.o \
	arm/obj/can/can.o \
	arm/obj/cli_arc/socket_imq_bridge.o \
	arm/obj/$(COMMON)/v2x_cli/v2x_cli.o

arc1/bin/qa-mc: \
	$(SDK_DIR)/board/$(BOARD)/arc1/lib/ref-sys.o \
	arc1/obj/$(COMMON)/general/general.o \
	arc1/obj/cli_arc/libcli/regex/regex.o \
	arc1/obj/cli_arc/libcli/libcli.o \
	arc1/obj/$(COMMON)/link/link.o \
	arc1/obj/can/can.o \
	arc1/obj/$(COMMON)/nav_api/nav_api.o \
	arc1/obj/cli_arc/imq_socket_bridge.o

arc2/bin/qa-mc: \
	$(SDK_DIR)/board/$(BOARD)/arc2/lib/ref-sys.o \
	arc2/obj/$(COMMON)/general/general.o \
	arc2/obj/cli_arc/libcli/regex/regex.o \
	arc2/obj/cli_arc/libcli/libcli.o \
	arc2/obj/can/can.o \
	arc2/obj/$(COMMON)/nav_api/nav_api.o \
	arc2/obj/can/can.o \
	arc2/obj/cli_arc/imq_socket_bridge.o


arm/bin/qa-mc: \
	arm/obj/qa-mc.arc1.o \
	arm/obj/qa-mc.arc2.o

# Handle single core
#	arc1/obj/$(COMMON)/v2x_cli/v2x_cli_arc.o


else

.DEFAULT_GOAL := arm/img/qa-sc.img

# CRATON_NO_ARC
arm/bin/qa-sc: \
	$(SDK_DIR)/board/$(BOARD)/arm/lib/ref-sys.o \
	arm/obj/$(COMMON)/general/general.o \
	arm/obj/$(COMMON)/nav_api/nav_api.o \
	arm/obj/$(COMMON)/link/link.o \
	arm/obj/$(COMMON)/management/mng_api.o \
	arm/obj/phy/phy_cca_control.o \
	arm/obj/cpu/cpu_load.o \
	arm/obj/loopbacks/eth_loopback.o \
	arm/obj/ecc/ecc.o \
	arm/obj/can/can.o \
	arm/obj/$(APPS)/crypto/ecdsa-example.o \
	arm/obj/$(APPS)/sniffer/sniffer.o \
	arm/obj/$(COMMON)/v2x_cli/v2x_cli.o

arc1/bin/ref: $(SDK_DIR)/board/$(BOARD)/arc1/bin/ref
	$(COPY)

arc2/bin/ref: $(SDK_DIR)/board/$(BOARD)/arc2/bin/ref
	$(COPY)


endif
