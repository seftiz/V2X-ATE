x := $(HOST)/bin/asn1-benchmark
$x-obj-y := benchmark.o
$x-lib-y := asn1-etsi -lrt
$x-cflags-y := -O2
build-y += $x
