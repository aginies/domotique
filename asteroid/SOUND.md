# Sound Integration Plan

## Problem Summary

`sounds.c` has a complete procedural audio synthesis engine (12 sound effects) but it's completely disconnected: not compiled, not linked, and has no working audio output path.

### Current Issues
- `sound.c` not in Makefile SRCS
- No file includes `sound.h` or calls `sound_*()` functions
- `sound_init()` doesn't create an SDL audio device
- Audio callback is a no-op stub (params cast to `void`)
- `queue_audio()` is cast to `(void)` to suppress a compiler warning
- Duplicate `SoundEffect` enum in `game.h` (lines 115-124 is dead code)
- Single-voice architecture (can't play thrust + explosions simultaneously)

---

## Files to Change

### 1. `src/game.h` — Fix duplicate enums (lines 115-124)

Remove the first `SoundEffect` enum (`S_NONE`, `S_SHOOT`, `S_HIT_BIG`, etc.) which is dead code. Keep the second, more detailed enum (`SFX_THRUST` through `SFX_GAME_OVER`, lines 126-140).

### 2. `src/sound.h` — Remove dependency on `game.h`

Replace `#include "game.h"` with no includes. The `SoundEffect` enum is standalone integer values, not tied to any game types.

### 3. `src/sound.c` — Major rewrite

**Add SDL3 audio subsystem:**
- Include `<SDL3/SDL_audio.h>`
- Implement proper stream callback that fills the output buffer with mixed samples
- Initialize audio device with `SDL_OpenAudioDevice()`

**Implement multi-voice mixing (6 simultaneous voices):**
- Replace single `voice_state` with a `Voice` struct array of 6 slots
- Each voice has: state, phase, volume, duration, elapsed time
- Main mix loop iterates all voices and accumulates samples

**Implement `start_voice(SoundEffect)` function:**
- Find a free voice slot (or steal the quietest/oldest one)
- Set voice parameters based on sound type

**Fix audio clock management:**
- Use global audio clock for ADSR envelope timing
- Voices track their own offset for waveform phase

**Replace `drand48()` calls with `SDL_randf()`:**
- Better C standard/portability compatibility

### 4. `Makefile` — Add `sound.c` to build

```makefile
SRCS = src/main.c src/game.c src/ship.c src/asteroids.c src/saucers.c src/shots.c src/particles.c src/ui.c src/sound.c
```

### 5. `src/main.c` — Initialize sound

After SDL init and window/Renderer creation:
```c
SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO);
...
sound_init();
```

Before cleanup:
```c
sound_shutdown();
```

### 6. `src/ship.c` — Wire sound events

| Event | Sound | Where |
|---|---|---|
| Shield activate | `SFX_SHIELD_ON` | Edge-triggered when down-key goes active |
| Shield deactivate | `SFX_SHIELD_OFF` | Edge-triggered when up-key goes inactive |
| Ship shot | `SFX_SHOOT` | On each shot in `shot_init_player()` or `ship_update()` |
| Hyperspace teleport | `SFX_HYPERSPACE` | In `ship_hyperspace()` |
| Shield death | `SFX_EXPLOSION_SHIELD` | When shield timer expires (survives but loses nothing) |
| Ship dies (explosion) | `SFX_LIFE_LOSE` | When ship is destroyed by asteroid/saucer or shield overload |

**Thrust sound (continuous):**
- Since it's a sustained sound, call `start_voice(SFX_THRUST)` every frame while thrusting (it will skip if the voice is already active)
- Or implement a `sound_stop(SFX_THRUST)` called when thrust ends

### 7. `src/asteroids.c` — Wire explosion sounds

| Event | Sound | Where |
|---|---|---|
| Large asteroid split (into medium) | `SFX_EXPLOSION_LARGE` | `ast_split()` when size == `AST_SIZE_LARGE` |
| Medium asteroid split (into small) | `SFX_EXPLOSION_MEDIUM` | `ast_split()` when size == `AST_SIZE_MEDIUM` |
| Small asteroid destroyed | `SFX_EXPLOSION_SMALL` | `ast_split()` when size == `AST_SIZE_SMALL` (dead without splitting) |
| Ship dies (collision with asteroid) | `SFX_LIFE_LOSE` | `ast_collisions()` when ship alive check fails |

### 8. `src/saucers.c` — Saucer hum management

| Event | Sound | Where |
|---|---|---|
| Saucer enters | `SFX_SAUCER` | `saucer_init()` — start saucer hum |
| Saucer dies/leaves | Stop hum | `saucer_update()` — need a way to identify/stop this saucer's hum sound |

**Saucer hum management:**
- Each saucer gets its own voice slot for the hum
- When a saucer leaves the screen, find its voice slot and silence/free it
- Need `void sound_stop(SoundEffect effect)` or track per-saucer sound IDs
- Alternatively: store the sound instance ID returned by `sound_play()` and stop it when saucer dies

### 9. `src/game.c` — Game state sounds

| Event | Sound | Where |
|---|---|---|
| Level complete transition | `SFX_SHOOT` or fanfare (e.g., ascending tone) | `game_update()` when transitioning into `GSTATE_LEVEL_TRANS` |
| Game over screen starts | `SFX_GAME_OVER` | `game_update()` when transitioning into `GSTATE_GAME_OVER` |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Mono or stereo? | Mono source, SDL interleaves to stereo | Simpler synthesis, SDL handles stereo output |
| Multi-voice count | 6 simultaneous voices | Enough for thrust + explosions + saucer hum without wasting CPU |
| Saucer hum persistence | Voice slot per saucer instance | Each saucer has its own hum; voice freed when saucer dies |
| Voice stealing | Steal oldest voice if all 6 busy | Short sounds get priority; old sounds cut off gracefully |
| Thrust as sustained | Re-call `start_voice(SFX_THRUST)` every frame | Idempotent: skips if voice slot already active |
| Audio init failure | Fail silently, set flag, skip soundPlay | Game still fully works on headless/Xvfb systems |
| Envelope timing | Global audio clock (time-based) | Consistent playback regardless of sample rate |

---

## Implementation Order

1. Fix `game.h` (remove dead `SoundEffect` enum)
2. Update `sound.h` (remove `game.h` include)
3. Rewrite `sound.c` (SDL3 device + multi-voice mixer)
4. Update `Makefile` (add `sound.c`)
5. Wire up `main.c` (init/shutdown calls)
6. Wire up game modules:
   a. `game.c` (level complete, game over)
   b. `ship.c` (shield, shoot, hyperspace)
   c. `asteroids.c` (explosion splits)
   d. `saucers.c` (saucer hum)
7. Build test

---

## Architecture

```
main.c
  └── SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO)
  └── sound_init()          -- opens audio device, registers callback
  └── game loop
       ├── sound_play(SFX_*) -- game modules emit sound events
       └── sound_shutdown()  -- closes audio device

sound.c
  ├── Voice struct pool (6 slots)
  ├── sound_init()          -- SDL_OpenAudioDevice()
  ├── audio_callback()      -- SDL calls this per buffer, mixes all active voices
  ├── sound_play()          -- finds free voice, sets waveform params
  └── sound_shutdown()      -- SDL_CloseAudioDevice()
```

### Voice Structure (proposed)

```c
typedef enum {
    VOICE_IDLE = 0,
    VOICE_THRUST,          // Brown noise (sustained)
    VOICE_SHOOT,           // Descending sine 1200->400 Hz
    VOICE_EXP_LARGE,       // 80->20 Hz bass + noise
    VOICE_EXP_MEDIUM,      // 100->30 Hz + noise
    VOICE_EXP_SMALL,       // 200->50 Hz quick pop
    VOICE_SAUCER,          // 3-oscillator hum (220/330/110 Hz)
    VOICE_SHIELD_ON,       // Cross-modulated 800/1600 Hz
    VOICE_SHIELD_OFF,      // Descending 800->100 Hz
    VOICE_HYPERSPACE,      // Rising 100->2000 Hz chirp
    VOICE_EXP_SHIELD,      // Metallic crash
    VOICE_LIFE_LOSE,       // Descending 400->50 Hz sad tone
    VOICE_GAME_OVER        // Descending glissando 300->30 Hz
} VoiceState;

typedef struct {
    VoiceState state;
    float phase;           // waveform phase (radians)
    float volume;          // ADSR envelope
    float duration;        // total sound duration in seconds
    float elapsed;         // time elapsed in current sound
    int ref_count;         // for saucer hum (shared by all saucer hum voices)
} Voice;
```

### ADSR Envelope Calculation (per sample)

```
attack = min(t, 0.05s) / 0.05s
decay = if t > attack_duration: max(0, 1.0 - (t - attack) / decay_duration)
sustain_level = 0.7f
release = if t > (attack + decay): max(0, 1.0 - (t - attack - decay) / release_duration)
volume = attack * (sustain > 0 ? sustain_level : 0) + release;
```

---

## Testing Checklist

- [ ] Game compiles with `make`
- [ ] Launches and runs with sound on desktop
- [ ] Shot pew sound plays on each press
- [ ] Thrust hisses while holding up arrow
- [ ] Each asteroid size plays different explosion
- [ ] Sounds overlap correctly (thrust + explosion + saucer simultaneously)
- [ ] Shield on/off sounds trigger at correct moments
- [ ] Hyperspace warp chirp plays
- [ ] Saucer hum plays continuously while saucer is on screen
- [ ] Saucer hum stops when saucer leaves screen
- [ ] Level complete chime plays
- [ ] Game over glissando plays
- [ ] No artifacts (clicks, pops, clipping)
- [ ] Works in headless mode (Xvfb) without crashing
