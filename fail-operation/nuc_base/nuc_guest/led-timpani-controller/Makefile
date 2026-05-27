CC = gcc
CFLAGS = -Wall -O2
LDFLAGS = -pthread
TARGET = led_timpani

all: $(TARGET)

$(TARGET): led_timpani.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
