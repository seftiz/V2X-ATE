#.DEFAULT_GOAL := all
FORCE:


CONFIG_MIBS_DIR := /docs/SW/Books/MIB-Collection
#CONFIG_MIBS_DIR := /MIB-Collection
#SDK_DIR := /docs/SW/Release/craton-sdk/sdk-2.0/beta11/sdk-2.0-beta11-pangaea3-i686-linux-gnu
#SDK_DIR := /docs/SW/Release/craton-sdk/sdk-2.0/rel/2.0.3/sdk-2.0.3-pangaea3-i686-linux-gnu
#SDK_DIR := $(HOME)/sdk-2.0.3-pangaea3-i686-linux-gnu
# SDK_DIR := $(HOME)/fw_release/sdk-2.1-alpha3-pangaea3-i686-linux-gnu

# GM version a2
SDK_DIR := $(HOME)/fw_release/sdk-2.1-rc1-atk22031a-i686-linux-gnu



# Auxiliary variables
sdk_config := $(SDK_DIR)/bin/atlk-sdk-config
output_dir := output
target_output_dir := $(output_dir)/target

# Build rules
flthdr = $(CC:%-gcc=%-flthdr)
compile_rule = $(CC) $(CFLAGS) -c $^ -o $@
link_rule = $(CC) $(LDFLAGS) -o $@ $^ $(LIBS) && $(flthdr) -s 65536 $@

all: v2x-cli pysnmp

# v2x-cli-obj := session/session.o wsmp/wsmp.o libcli/libcli.o gps_simulator/gps.o nav_api/nav_api.o v2x_cli/v2x_cli.o
v2x-cli-obj := libcli/libcli.o v2x_cli/v2x_cli.o

#v2x-cli : $(target_output_dir)/bin/v2x-cli
v2x-cli: $(v2x-cli-obj)
	@echo "Building " $@ "... flags" $(LDFLAGS) " Libs " $(LIBS)
	$(link_rule)

%.o: %.c
	@echo "Compiling " $@ $^ "..."
	$(compile_rule)

clean:
	rm -rf $(v2x-cli-obj)

#CFLAGS := -g -Wall -Wextra -Werror
# CFLAGS := -g -std=c99 -D_XOPEN_SOURCE=600 -pedantic -Wall -Werror
CFLAGS := -g -D_XOPEN_SOURCE=600 -Wall -Werror

%: CC := $(shell $(sdk_config) --target-cc)
%: CFLAGS += $(shell $(sdk_config) --target-cflags)
%: LDFLAGS := $(shell $(sdk_config) --target-ldflags)
# ORG %: LIBS := -lv2x -latlk -lpthread -lcrypt -lnav -lgps -lm
%: LIBS := -lpthread -lcrypt

# Build PySNMP MIB modules
snmp_mibs_dir := $(SDK_DIR)/mibs
pysnmp_dir := $(snmp_mibs_dir)/pysnmp

snmp_mib_files := $(wildcard $(snmp_mibs_dir)/*.mib)
pysnmp_files := $(snmp_mib_files:$(snmp_mibs_dir)/%.mib=$(pysnmp_dir)/%.py)

snmp_extern_mibs := IF-MIB IANAifType-MIB
pysnmp_files += $(snmp_extern_mibs:%=$(pysnmp_dir)/%.py)

cmd_pysnmp = SMIPATH=$(CONFIG_MIBS_DIR):$(snmp_mibs_dir) \
	smidump -f python $< | libsmi2pysnmp > $@
$(pysnmp_dir)/%.py: $(snmp_mibs_dir)/%.mib | $(pysnmp_dir)
	$(cmd_pysnmp)
$(pysnmp_dir)/%.py: $(CONFIG_MIBS_DIR)/%.mib | $(pysnmp_dir)
	$(cmd_pysnmp)

$(pysnmp_dir): FORCE
	mkdir -p $@

pysnmp: $(pysnmp_files)
