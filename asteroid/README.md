# Asteroids

A classic Asteroids game built in C using SDL3.

This project was generated using the Qwen3.6 LLM.

## Build

```bash
make
```

## Run

```bash
./asteroid
```

## Controls

| Key | Action |
|-----|--------|
| Left Arrow / A | Rotate left |
| Right Arrow / D | Rotate right |
| Up Arrow / W | Thrust |
| Space | Fire |
| Shift | Hyperspace |

## Development

This is an open-source implementation of the classic Asteroids arcade game.

### Tech Stack

- **Language:** Pure C (no C++ dependencies)
- **Graphics:** SDL3 with OpenGL renderer
- **Build system:** GNU Make with pkg-config for SDL3 discovery

### Architecture

The project is structured into modular source files, each responsible for a game subsystem:

| Module | Responsibility |
|--------|----------------|
| `main.c` | Entry point, event loop, render loop |
| `game.c` | Core game loop (init, update, render) |
| `game.h` | All type definitions, constants, and declarations |
| `ship.c` | Ship physics, rotation, thrust, drawing, hyperspace |
| `asteroids.c` | Asteroid spawning, splitting, collision detection |
| `saucers.c` | Flying saucer AI, spawning, drawing |
| `shots.c` | Player and enemy projectile logic |
| `particles.c` | Explosion particle effects |
| `ui.c` | UI rendering, bitmap font rendering, score/lives display |

### Design Decisions

- **Slow acceleration:** The ship has gradual thrust buildup with no practical speed cap and minimal friction, creating a sense of weight and momentum.
- **Bitmap font:** A hand-crafted pixel font drawn via `SDL_RenderFillRect` for crisp, retro text rendering at any scale.
- **Renderer fallback:** Attempts the SDL3 "gpu" renderer first, falls back to "opengl" for compatibility.
- **Level scaling:** Saucer spawn rate decreases as levels progress, but is clamped to prevent overwhelming the player.

