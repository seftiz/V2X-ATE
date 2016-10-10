x := $(TARGET)/bin/v2x-cli
$x-obj-y := v2x_cli.o
$x-obj-y += session/session.o wsmp/wsmp.o libcli/libcli.o gps/gps.o
$x-lib-y := v2x atlk -lcrypt -lpthread
build-y += $x
