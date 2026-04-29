## Phase 1: Project Setup & Core Types

### 1. Create directory structure
```
asteroid/
├── Makefile
├── src/
│   ├── main.c       – Entry, SDL3 init, event loop
│   ├── game.h       – Shared types, constants, prototypes
│   ├── ship.c/h     – Ship entity & physics
│   ├── asteroids.c/h– Asteroid system
│   ├── saucers.c/h  – Saucer AI & behavior
│   ├── shots.c/h    – Player + saucer bullets
│   ├── particles.c/h– Explosions, thrust, shield effects
│   └── ui.c/h       – Score/lives/level HUD
```

### 2. `Makefile` variables
| Variable | Value |
|---|---|
| `CC` | `gcc` |
| `CFLAGS` | `-Wall -Wextra -std=c17 -O2 -DS3DLG_LINKER -Isrc` |
| `LDFLAGS` | `SDL3 lib` (auto via pkg-config) |

---

## Phase 2: Architecture & Data Structures

### 3. `src/game.h` — Core structs

**Types:**
- `vec2` — `float x, y`
- `vec2f` (functions): add, sub, mul, dot, len, normalize, rotate
- `rect` — `float x, y, w, h`
- `color` — `uint8_t r, g, b, a`; helpers for white, gray, gold, etc.

**Constants:**
| Constant | Value | Purpose |
|---|---|---|
| `W, H` | 1024, 768 | Screen dimensions |
| `FPS` | 60 | Target frame rate |
| `SHIP_SCALE` | 1.0 | Ship size multiplier |
| `SHIP_RADIUS` | 12.0 | Ship hitbox radius |
| `SHIP_THRUST` | 80.0 | Acceleration (px/s) |
| `SHIP_MAX_SPEED` | 200.0 | Max velocity magnitude |
| `SHIP_ROT_SPEED` | 250.0 deg/s | Rotation speed |
| `SHIP_MASS` | 1.0 | Ship mass for momentum |
| `FRICTION` | 6.0 | Velocity decay per second |
| `SHOT_SPEED` | 300.0 | Bullet velocity magnitude |
| `SHOT_LIFE` | 1.0 | Shot lifetime in seconds |
| `COOLDOWN` | 0.15 | Shot间隔 between shots |
| `ASTEROID_BASE_SPEED` | 20.0 | Base speed before level scaling |
| `ASTEROID_ROT_SPEED` | 80.0 deg/s | Asteroid spin |
| `SAUCER_SPEED` | 150.0 | Saucer drift speed |
| `SAUCER_SHOOT_INTERVAL_BG` | 2.0 | Big saucer shoot cooldown |
| `SAUCER_SHOOT_INTERVAL_SM` | 0.8 | Small saucer shoot cooldown |
| `SAUCER_SPAWN_INTERVAL` | 30.0 | Seconds between saucer spawns |
| `SHIELD_DURATION` | 2.0 | Shield active time in seconds |
| `SHIELD_RADIUS` | 25.0 | Shield sphere radius when shielded |
| `HYPERSPACE_CHANCE` | 15.0 | % chance of death during hyperspace |
| `INVUL_TIME` | 3.0 | Seconds invulnerable after respawning |

**Enums:**
```c
typedef enum { SIZE_LARGE=40.0, SIZE_MEDIUM=25.0, SIZE_SMALL=15.0 } AstSize;
typedef enum { SAUCER_BIG, SAUCER_SMALL } SaucerType;
typedef enum { GSTATE_TITLE, GSTATE_PLAYING, GSTATE_LEVEL_TRANS, GSTATE_GAME_OVER } GState;
```

**Structs (dynamic arrays managed by code):**
- `Ship` — pos, vel, angle, alive, lives, score, invul_timer, shield_timer, shield_activated, thrusting, rotation_dir
- `Asteroid` — pos, vel, radius, size, angle, rot_speed, verts[] (jagged polygon offset angles and distances)
- `Saucer` — pos, vel, type, dir (±1), alive, shoot_timer, enter_timer, color (changes every 5500 pts), points
- `Shot` — pos, vel, alive, is_enemy (bool)
- `Particle` — pos, vel, life, max_life, size, color
- `Game` — state, window/renderer, ship, asteroids[], saucers[], shots[], particles[], level, saucer_timer, level_trans_timer, high_score

**Collision:** `bool intersects(float ax, ay, ar, bx, by, br)` — circle-circle distance check

---

## Phase 3: Entity Systems (8 modules) each with a .c and .h

### 4. `src/ship.c` — Ship management
- `ship_init(Game*)` — center ship, reset state
- `ship_update(Game*, dt, input)` — handle rotation (←/→ arrows modify angle), thrust (↑ arrow adds velocity in ship direction), check down key sets `shield_activated`, check shoot key triggers `shot_spawn`, check space triggers shot cooldown, apply velocity + friction, wrap position, invul timer decay
- `ship_draw(SDL_Renderer*, Ship*)` — if invul && invul_timer > 0, draw only every other scanline (classic flicker); if shielded, draw circle with inner point; else draw wireframe triangle (nose + left corner + right corner)
- `ship_hyperspace(Game*)` — random position, 15% self-destruct chance
- **Render path:** For triangle, use `SDL_RenderLines()` with 3 segments (open triangle — nose to left corner, left to right, right to nose). For shield, use `SDL_RenderCircle()` with thicker stroke and a dot center.

### 5. `src/asteroids.c` — Asteroid system
- `ast_init_random(Game*, int level)` — pick random size (always Large at init), random pos (not near ship), random velocity direction/speed scaled by level: `speed = base_speed * (1 + level * 0.1)`, generate 8-12 vertices with random offsets (±30% of radius) for jagged look
- `ast_spawn_level(Game*, int level)` — call `ast_init_random` N times. N = 4 + level (up to 12)
- `ast_update(Game*, dt)` — move each alive asteroid: pos += vel * dt; angle += rot_speed * dt; wrap with clamp-modulo
- `ast_draw(SDL_Renderer*, Asteroid*)` — compute rotated vertices from polygon offsets; render as `SDL_RenderLines()` wireframe
- `ast_split(Asteroid*, Shot*, Game*)` — on hit: deactivate shot; if Large → 2×Medium: one moves at original angle + 90°, other −90° with randomized ±20° variance; if Medium → 2×Small: same pattern; score = original Asteroid size points; spawn explosion particles
- **Scoring:** Large=20, Medium=50, Small=100

### 6. `src/saucers.c` — Saucer AI
- `saucer_init(Game*, SaucerType)` — pick spawn side (left or right with slight Y random offset), set velocity toward center with slight Y drift, set `type`, initialize `shoot_timer`, `color` based on player score thresholds (0–10000=red, 10000–20000=magenta, 20000–30000=blue, 30000+ = cycling every 5500 pts)
- `saucer_update(Game*, dt)` — move saucer across screen; if off screen → deactivate; update `shoot_timer`: if > interval, call `saucer_fire()`; update `color` cycling
- `saucer_fire(Game*, Saucer*)` — compute angle from saucer to ship (if Small) or random angle (if Big); Small saucer accuracy angle = `20° - (score / 40000 * 20°)` (i.e., at 40k it shoots precisely); spawn Shot with that angle; saucer points increase by 100 every 5500 score (100→200→300)
- `saucer_draw(SDL_Renderer*, Saucer*)` — saucer = ellipse via `SDL_RenderCircleF()` with thick stroke + dome on top. Big: wider ellipse. Small: narrower ellipse
- **Spawn logic:** Timer in Game updates every 30 seconds. At score ≥40k, only Small saucers spawn. Max 2 alive simultaneously.

### 7. `src/shots.c` — Projectile system
- `shot_init_player(Game*, float angle)` — spawn at ship nose + offset, velocity = `ship_vel + angle_direction * SHOT_SPEED`; set `is_enemy = false`
- `shot_init_enemy(Game*, Saucer*, angle)` — spawn at saucer bottom + offset
- `shot_update(Game*, dt)` — for each alive shot: pos += vel * dt; wrap; life -= dt; if life <= 0 → deactivate
- `shot_draw(SDL_Renderer*, Shot*)` — short line (4px) in direction of velocity, white for player shots, gold/yellow for saucer shots. Width = 2
- **Hit detection:** Check all alive shots against all alive asteroids and saucers. Each hit deactivates the shot and calls split function.

### 8. `src/particles.c` — Particle effects
- `particle_spawn(Game*, pos, count, speed_range, color)` — spawn N particles with random angle, uniform/slow velocity, fading color (white→yellow→dark), size shrinks over life
- `particle_update(Game*, dt)` — decay `life -= dt` each frame; deactivate when `life <= 0`
- `particle_draw(SDL_Renderer*)` — render each alive particle as `SDL_RenderPointF()` with color

### 9. `src/ui.c` — HUD
- `ui_draw(SDL_Renderer*, Game*)` — render everything in the HUD (score, lives, level)
  - **Score:** Right-justified at top-right corner. Render as text using a custom 5×7 bitmap font stored as byte arrays. Each pixel is a `SDL_Point` drawn with `SDL_RenderPointF()`. White color. 30px scale.
  - **Level:** Left side below score (e.g., "LVL 1")
  - **Lives:** Bottom-center area. For each remaining life, draw a tiny 12×15 wireframe ship icon
- **Text rendering:** Bitmap font with character data structured as:
  ```c
  typedef struct { SDL_Point pts[16]; int count; } Glyph;
  typedef struct { Glyph frames[7]; int width; } FontChar;
  ```
  Frame-by-frame glyph definitions (e.g., '0' = 7 frames of horizontal lines; digits + colon + letters needed)
  ```c
  FontChar font_chars[95]; // ASCII 32-126
  int font_init(SDL_Renderer*);
  void font_draw(SDL_Renderer*, int x, int y, const char* text, int scale, color c);
  ```

---

## Phase 4: Game Engine

### 10. `src/game.c` — Main game loop
```c
// State machine in game_update(Game*, float dt):

switch (game->state):
  GSTATE_TITLE:
    - if Enter pressed → game->state = GSTATE_PLAYING; ship_init(); ast_spawn_level(game, 0);
  GSTATE_PLAYING:
    - ship_update(game, dt, keys);
    - ast_update(game, dt);
    - saucer_update(game, dt);
    - shot_update(game, dt);
    - ast_collisions(game); // shot vs asteroid, shot vs saucer, ship vs saucer, ship vs asteroid
    - particle_update(game, dt);
    - update saucer spawn timer
    - check if all cleared → game->state = GSTATE_LEVEL_TRANS; game->level_trans_timer = 3.0;
    - check lives → if 0, game->state = GSTATE_GAME_OVER; game->game_over_timer = 5.0;
  GSTATE_LEVEL_TRANS:
    - level_trans_timer -= dt; if timer <= 0: game->level++; ast_spawn_level(game, game->level);
      game->state = GSTATE_PLAYING;
  GSTATE_GAME_OVER:
    - game_over_timer -= dt; if timer <= 0: if Enter → GSTATE_TITLE; if Escape → quit;
```

**Collision handling (in ast_collisions):**
1. **Shot vs Asteroid:** for each alive shot: check all asteroids; if intersects → deactivate shot, split asteroid, score, spawn explosion
2. **Shot vs Saucer:** same pattern → score, deactivate saucer, spawn explosion
3. **Ship vs Asteroid/Saucer:** if ship.invul_timer > 0 or ship.shielded → skip; else → ship.dead = true, ship.lives--, ship_invul = INVUL_TIME, spawn explosion

**Level transition:** Clear all asteroids and saucers → show "LVL 2" (bigger font) flashing on screen → auto advance

### 11. `src/ui.c` — Drawing HUD functions
- All UI elements drawn via `SDL_RenderLines()/SDL_RenderRect()/SDL_RenderPointF()`
- No text library needed — pure bitmap font rendering

---

## Phase 5: Main Application & Integration

### 12. `src/main.c` — Entry point
```c
int main(void) {
    SDL_Init(SDL_INIT_VIDEO);
    SDL_SetMainReady();
    
    SDL_Window *win = SDL_CreateWindow("Asteroids", 1024, 768, SDL_WINDOW_HIDDEN);
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1);
    SDL_SetWindowHidden(win); // full input capture
    
    FontChar fonts[95];
    font_init(ren, fonts);
    
    Game game = {0};
    game_init(&game);
    
    Uint32 last_time = SDL_GetTicks();
    while (!game.quit) {
        SDL_Event ev;
        while (SDL_PollEvent(&ev)) handle_event(&game, &ev);
        
        Uint32 now = SDL_GetTicks();
        float dt = (now - last_time) / 1000.0f;
        last_time = now;
        
        game_update(&game, dt, keys_pressed);
        game_render(ren, &game);
        
        SDL_RenderPresent(ren);
    }
    
    SDL_DestroyRenderer(ren); SDL_DestroyWindow(win); SDL_Quit();
    return 0;
}
```

**Event handling:** KeyDown → set `game->keys[key] = true`. KeyUp → `game->keys[key] = false`. 
- Key mappings: `SDL_SCANCODE_LEFT` (rotate ccw), `SDL_SCANCODE_RIGHT` (rotate cw), `SDL_SCANCODE_UP` (thrust), `SDL_SCANCODE_DOWN` (shield), `SDL_SCANCODE_SPACE` (shoot), `SDL_SCANCODE_H` (hyperspace), `SDL_SCANCODE_RETURN` (menu/back), `SDL_SCANCODE_ESCAPE` (quit)

---

## Phase 6: Final Touches

### 13. Rendering details
- **Background:** `SDL_RenderClear(ren, (SDL_Color){0, 0, 0, 255})`
- **All sprites:** White wireframe via `SDL_SetRenderDrawColor(ren, 255, 255, 255, 255)`
- **Shot lines:** thinner line width (~1) vs ship/saucer lines (width ~2)
- **Ship triangle (default):** 3 line segments forming the outline
- **Ship triangle (thrust):** add flame triangle behind ship
- **Ship (shielded):** circle with thick stroke + center point
- **Asteroid:** open polygon (line segments connecting 8-12 vertices)
- **Saucer (big):** ellipse (thick circle) + small circle dome on top
- **Saucer (small):** narrower ellipse + smaller dome
- **Particles:** point-based fading circles
- **Text:** white bitmap font, all characters pre-rendered to arrays of `SDL_Point`

### 14. Audio (optional, if desired)
- Sound could be added via `libsdl3-ttf` or `SDL3_mixer` for thrusters, explosions, saucer hum
- **Decision:** Skip for now — pure C without external audio dependencies

---

## Execution Sequence

```
Step 1: Create src/ directory (already exists? Check first)
Step 2: Write game.h (defining all types/constants)
Step 3: Write ship.c/h (ship entity)
Step 4: Write asteroids.c/h (asteroid system)
Step 5: Write saucers.c/h (saucer AI)
Step 6: Write shots.c/h (projectile system)
Step 7: Write particles.c/h (effects)
Step 8: Write ui.c/h (HUD + bitmap font)
Step 9: Write game.c (game loop + state machine)
Step 10: Write main.c (entry point + event handling)
Step 11: Write Makefile
Step 12: Build — gcc -o asteroid src/*.c `sdl3-config --libs`
Step 13: Test — run and verify all mechanics work
```

---

**Total files:** 14 (10 .c/.h pairs + 1 Makefile... wait, let me count: game.h, game.c isn't needed as .h, ship.c ship.h, asteroids.c asteroids.h, saucers.c saucers.h, shots.c shots.h, particles.c particles.h, ui.c ui.h, game.c, main.c, Makefile = **16 files**)

**Dependencies:** gcc, SDL3 headers + runtime
**Build time:** ~2-4s on modern machine
**Expected binary size:** ~100-200KB
