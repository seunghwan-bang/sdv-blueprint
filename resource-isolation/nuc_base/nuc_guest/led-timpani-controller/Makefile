CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -pthread
TARGET = led_timpani

.PHONY: all clean

all: $(TARGET)

$(TARGET): led_timpani.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)
