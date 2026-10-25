# Builds hzcommfix.so, the LD_PRELOAD library used on Linux dedicated servers.
# Release 1.0.1 was built on Ubuntu 22.04 with GCC 11 (see README.md).

CC      ?= gcc
CFLAGS  ?= -O2
TARGET  := hzcommfix.so

all: $(TARGET)

$(TARGET): hzcommfix.c
	$(CC) $(CFLAGS) -shared -fPIC -o $@ $<
	strip --strip-unneeded $@
	sha256sum $@

clean:
	rm -f $(TARGET)

.PHONY: all clean
