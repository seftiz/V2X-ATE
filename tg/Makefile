
SDK_DIR := /docs/ATE/fw_releases/sdk-4.5.1-sc-i686-linux-gnu

include $(SDK_DIR)/build/rules.mk
include $(SDK_DIR)/build/craton.mk
include $(SDK_DIR)/build/u-boot.mk

LDFLAGS := -lcraton -lm
BOARD := atk22016

.DEFAULT_GOAL := arm/img/tg-sc.img

ASN1C := $(HOME)/local/bin/asn1c -fcompound-names



CFLAGS = -g -Os -std=gnu99 -Ietsi/output


asn1c:
	cd etsi && mkdir -p output && cd output && \
	$(ASN1C) -gen-PER -fnative-types ../ITS-Container.asn ../CAM.asn ../DENM.asn 2> ../asn1c.log && \
	sed -f ../../asn1c.sed -i asn_system.h


asn1_c_src :=  $(filter-out %-sample.c, $(wildcard etsi/output/*.c))
asn1_obj := $(patsubst %.c,%.o,$(asn1_c_src))
asn1_arm_obj = $(addprefix arm/obj/etsi/output/, $(notdir $(asn1_obj) ) )

# CRATON_NO_ARC
arm/bin/tg-sc: \
	$(SDK_DIR)/board/$(BOARD)/arm/lib/ref-sys.o \
	$(asn1_arm_obj) \
	arm/obj/generator/asn_frame_builder.o \
	arm/obj/generator/etsi_frames_generator.o

arc1/bin/ref: $(SDK_DIR)/board/$(BOARD)/arc1/bin/ref
	$(COPY)

arc2/bin/ref: $(SDK_DIR)/board/$(BOARD)/arc2/bin/ref
	$(COPY)


clean:
	rm -rf etsi/output