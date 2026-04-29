# Asteroids - SDL3 C17 Game

CC = gcc
CFLAGS = -Wall -Wextra -std=c17 -O2 -Isrc
LDFLAGS = $(shell pkg-config --libs sdl3 2>/dev/null || pkg-config --libs sdl3-image 2>/dev/null) -lm

TARGET = asteroid
SRCS = src/main.c src/game.c src/ship.c src/asteroids.c src/saucers.c src/shots.c src/particles.c src/ui.c
OBJS = $(SRCS:.c=.o)

.PHONY: all clean run

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)
