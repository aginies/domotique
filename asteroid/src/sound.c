#include "sound.h"
#include <SDL3/SDL.h>
#include <SDL3/SDL_audio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SAMPLE_RATE 44100

typedef enum {
    AUDIO_STATE_IDLE = 0,
    AUDIO_STATE_THRUST,
    AUDIO_STATE_SHOOT,
    AUDIO_STATE_EXP_LARGE,
    AUDIO_STATE_EXP_MEDIUM,
    AUDIO_STATE_EXP_SMALL,
    AUDIO_STATE_SAUCER,
    AUDIO_STATE_SHIELD_ON,
    AUDIO_STATE_SHIELD_OFF,
    AUDIO_STATE_HYPERSPACE,
    AUDIO_STATE_EXP_SHIELD,
    AUDIO_STATE_LIFE_LOSE,
    AUDIO_STATE_GAME_OVER
} AudioState;

typedef struct {
    AudioState state;
    float phase;
    float volume;
    float duration;
    float elapsed;
} Voice;

static Voice voices[8];
static SDL_AudioStream *audio_stream = NULL;
static bool audio_initialized = false;
static SDL_AudioSpec current_spec = {0, 0, 0};
static int stream_channels = 0;

static inline float lerp(float a, float b, float t) {
    return a + (b - a) * t;
}

static inline float clamp01(float v) {
    return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v);
}

static float compute_adsr(float t, float attack, float decay, float sustain_level, float release) {
    if (t < attack) return t / attack;
    if (t < attack + decay) return 1.0f - (1.0f - sustain_level) * ((t - attack) / decay);
    if (t < attack + decay + release) return sustain_level * (1.0f - (t - attack - decay) / release);
    return -1.0f;
}

static float generate_voice_voice(Voice *v) {
    if (v->state == AUDIO_STATE_IDLE) return 0.0f;

    float t = v->elapsed;

    /* THRUST: sustain forever while active (no termination envelope) */
    if (v->state == AUDIO_STATE_THRUST) {
        float noise = (SDL_randf() + SDL_randf() + SDL_randf()) / 3.0f - 1.0f;
        return noise * 0.2f;
    }

    float env = compute_adsr(t, 0.05f, 0.1f, 0.5f, 0.2f);
    if (env < 0.0f || env > 2.0f) {
        v->state = AUDIO_STATE_IDLE;
        return 0.0f;
    }

    float sample = 0.0f;
    switch (v->state) {
        case AUDIO_STATE_THRUST:
            { float noise = (SDL_randf() + SDL_randf() + SDL_randf()) / 3.0f - 1.0f; sample = noise * env * 0.2f; } break;
        case AUDIO_STATE_SHOOT: {
            env = compute_adsr(t, 0.02f, 0.05f, 0.0f, 0.1f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(1200.0f, 400.0f, clamp01(t / 0.2f));
            sample = sinf(2.0f * M_PI * freq * (t - v->phase)) * env * 0.4f;
        } break;
        case AUDIO_STATE_EXP_LARGE: {
            env = compute_adsr(t, 0.05f, 0.2f, 0.3f, 1.0f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(80.0f, 20.0f, clamp01(t / 1.0f));
            float sin_val = sinf(2.0f * M_PI * freq * (t - v->phase));
            float noise = (SDL_randf() * 2.0f - 1.0f);
            sample = (sin_val * 0.6f + noise * 0.4f) * env * 0.6f;
        } break;
        case AUDIO_STATE_EXP_MEDIUM: {
            env = compute_adsr(t, 0.03f, 0.15f, 0.3f, 0.5f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(100.0f, 30.0f, clamp01(t / 0.5f));
            float sin_val = sinf(2.0f * M_PI * freq * (t - v->phase));
            float noise = (SDL_randf() * 2.0f - 1.0f);
            sample = (sin_val * 0.5f + noise * 0.5f) * env * 0.5f;
        } break;
        case AUDIO_STATE_EXP_SMALL: {
            env = compute_adsr(t, 0.02f, 0.1f, 0.2f, 0.2f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(200.0f, 50.0f, clamp01(t / 0.3f));
            float sin_val = sinf(2.0f * M_PI * freq * (t - v->phase));
            float noise = (SDL_randf() * 2.0f - 1.0f);
            sample = (sin_val * 0.4f + noise * 0.6f) * env * 0.4f;
        } break;
        case AUDIO_STATE_SAUCER: {
            env = compute_adsr(t, 0.2f, 0.3f, 0.8f, 0.1f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float t_phase = (t - v->phase);
            float osc = sinf(2.0f * M_PI * 220.0f * t_phase) * 0.5f
                      + sinf(2.0f * M_PI * 330.0f * t_phase) * 0.3f
                      + sinf(2.0f * M_PI * 110.0f * t_phase) * 0.2f;
            sample = osc * env * 0.25f;
        } break;
        case AUDIO_STATE_SHIELD_ON: {
            env = compute_adsr(t, 0.1f, 0.1f, 0.0f, 0.1f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float t_phase = (t - v->phase);
            float s1 = sinf(2.0f * M_PI * 800.0f * t_phase);
            float s2 = sinf(2.0f * M_PI * 1600.0f * t_phase);
            sample = s1 * s2 * env * 0.3f;
        } break;
        case AUDIO_STATE_SHIELD_OFF: {
            env = compute_adsr(t, 0.05f, 0.1f, 0.0f, 0.15f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(800.0f, 100.0f, clamp01(t / 0.3f));
            sample = sinf(2.0f * M_PI * freq * (t - v->phase)) * env * 0.3f;
        } break;
        case AUDIO_STATE_HYPERSPACE: {
            env = compute_adsr(t, 0.2f, 0.1f, 0.0f, 0.15f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(100.0f, 2000.0f, clamp01(t / 0.4f));
            float t_phase = (t - v->phase);
            float s1 = sinf(2.0f * M_PI * freq * t_phase);
            float s2 = sinf(2.0f * M_PI * freq * 1.5f * t_phase) * 0.5f;
            sample = (s1 + s2) * env * 0.3f;
        } break;
        case AUDIO_STATE_EXP_SHIELD: {
            env = compute_adsr(t, 0.02f, 0.15f, 0.3f, 0.5f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(500.0f, 100.0f, clamp01(t / 0.8f));
            float t_phase = (t - v->phase);
            float s1 = sinf(2.0f * M_PI * freq * t_phase);
            float s2 = sinf(2.0f * M_PI * freq * 2.0f * t_phase) * 0.3f;
            float noise = (SDL_randf() * 2.0f - 1.0f);
            sample = (s1 + s2 + noise) * env * 0.3f;
        } break;
        case AUDIO_STATE_LIFE_LOSE: {
            env = compute_adsr(t, 0.05f, 0.2f, 0.4f, 1.0f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(400.0f, 50.0f, clamp01(t / 1.0f));
            float t_phase = (t - v->phase);
            float s1 = sinf(2.0f * M_PI * freq * t_phase);
            float s2 = sinf(2.0f * M_PI * freq * 1.5f * t_phase) * 0.5f;
            sample = (s1 + s2) * env * 0.4f;
        } break;
        case AUDIO_STATE_GAME_OVER: {
            env = compute_adsr(t, 0.1f, 0.3f, 0.5f, 1.5f);
            if (env < 0.0f || env > 2.0f) { v->state = AUDIO_STATE_IDLE; return 0.0f; }
            float freq = lerp(300.0f, 30.0f, clamp01(t / 2.5f));
            float t_phase = (t - v->phase);
            float s1 = sinf(2.0f * M_PI * freq * t_phase) * 0.6f;
            float s2 = sinf(2.0f * M_PI * freq * 0.75f * t_phase) * 0.4f;
            sample = (s1 + s2) * env * 0.5f;
        } break;
        default: break;
    }

    return sample;
}

static void on_audio_mix(void *userdata, SDL_AudioStream *stream, int additional_amount, int total_amount) {
    (void)userdata;
    (void)total_amount;

    int num_bytes = additional_amount;
    int bytes_per_frame = (int)sizeof(Sint16) * stream_channels;
    int num_frames = num_bytes / bytes_per_frame;
    int channels = stream_channels;

    Sint16 *buf = (Sint16 *)malloc(num_bytes);
    if (!buf) return;
    memset(buf, 0, num_bytes);

    float sample_duration = 1.0f / current_spec.freq;

    for (int i = 0; i < num_frames; i++) {
        float output = 0.0f;
        for (int v = 0; v < 8; v++) {
            if (voices[v].state != AUDIO_STATE_IDLE) {
                voices[v].elapsed += sample_duration;
                output += generate_voice_voice(&voices[v]);
            }
        }

        Sint16 sample = (Sint16)(SDL_clamp(output * 32767.0f, -32767.0f, 32767.0f));

        for (int c = 0; c < channels; c++) {
            buf[i * channels + c] = sample;
        }
    }

    SDL_PutAudioStreamData(stream, buf, num_bytes);
    free(buf);
}

static void find_free_voice(Voice **out, int *index) {
    for (int i = 0; i < 8; i++) {
        if (voices[i].state == AUDIO_STATE_IDLE) {
            *out = &voices[i];
            *index = i;
            return;
        }
    }
    /* All busy - steal oldest voice (longest elapsed) */
    *out = &voices[0];
    *index = 0;
    for (int i = 1; i < 8; i++) {
        if (voices[i].elapsed > (*out)->elapsed) {
            *out = &voices[i];
            *index = i;
        }
    }
}

void sound_init(void) {
    memset(voices, 0, sizeof(voices));

    SDL_AudioSpec want;
    want.format = SDL_AUDIO_S16;
    want.channels = 2;
    want.freq = SAMPLE_RATE;

    audio_stream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &want, on_audio_mix, NULL);
    if (!audio_stream) {
        SDL_Log("Error: Could not open audio device: %s", SDL_GetError());
        audio_initialized = false;
        return;
    }

    /* Query the actual source format SDL assigned to the stream */
    if (SDL_GetAudioStreamFormat(audio_stream, &current_spec, NULL)) {
        stream_channels = current_spec.channels;
    } else {
        stream_channels = 2;
        current_spec.freq = SAMPLE_RATE;
        current_spec.format = SDL_AUDIO_S16;
    }

    if (!SDL_ResumeAudioStreamDevice(audio_stream)) {
        SDL_Log("Error: Could not resume audio device: %s", SDL_GetError());
        SDL_DestroyAudioStream(audio_stream);
        audio_stream = NULL;
        audio_initialized = false;
        return;
    }

    audio_initialized = true;
    SDL_Log("Audio OK: %d Hz, %d ch, format %d", current_spec.freq, current_spec.channels, current_spec.format);
}

void sound_shutdown(void) {
    if (audio_stream) {
        SDL_PauseAudioStreamDevice(audio_stream);
        SDL_DestroyAudioStream(audio_stream);
        audio_stream = NULL;
    }
    audio_initialized = false;
}

void sound_play(SoundEffect effect) {
    if (!audio_initialized || !audio_stream) return;

    /* For sustained sounds already active, leave them alone */
    AudioState target_state = (AudioState)(AUDIO_STATE_THRUST + (int)effect - SFX_THRUST);
    for (int i = 0; i < 8; i++) {
        if (voices[i].state == target_state) return;
    }

    Voice *voice = NULL;
    int idx = 0;
    find_free_voice(&voice, &idx);

    voice->state = target_state;
    voice->elapsed = 0.0f;
    voice->phase = 0.0f;
    voice->volume = 1.0f;

    switch (effect) {
        case SFX_THRUST: voice->duration = 8.0f; break;
        case SFX_SHOOT: voice->duration = 0.35f; break;
        case SFX_EXPLOSION_LARGE: voice->duration = 1.6f; break;
        case SFX_EXPLOSION_MEDIUM: voice->duration = 0.9f; break;
        case SFX_EXPLOSION_SMALL: voice->duration = 0.5f; break;
        case SFX_SAUCER: voice->duration = 8.0f; break;
        case SFX_SHIELD_ON: voice->duration = 0.4f; break;
        case SFX_SHIELD_OFF: voice->duration = 0.4f; break;
        case SFX_HYPERSPACE: voice->duration = 0.8f; break;
        case SFX_EXPLOSION_SHIELD: voice->duration = 1.1f; break;
        case SFX_LIFE_LOSE: voice->duration = 1.6f; break;
        case SFX_GAME_OVER: voice->duration = 3.2f; break;
        default: voice->duration = 0.0f; break;
    }
}

void sound_stop(SoundEffect effect) {
    if (!audio_initialized || !audio_stream) return;

    AudioState target;
    switch (effect) {
        case SFX_THRUST: target = AUDIO_STATE_THRUST; break;
        case SFX_SHOOT: target = AUDIO_STATE_SHOOT; break;
        case SFX_EXPLOSION_LARGE: target = AUDIO_STATE_EXP_LARGE; break;
        case SFX_EXPLOSION_MEDIUM: target = AUDIO_STATE_EXP_MEDIUM; break;
        case SFX_EXPLOSION_SMALL: target = AUDIO_STATE_EXP_SMALL; break;
        case SFX_SAUCER: target = AUDIO_STATE_SAUCER; break;
        case SFX_SHIELD_ON: target = AUDIO_STATE_SHIELD_ON; break;
        case SFX_SHIELD_OFF: target = AUDIO_STATE_SHIELD_OFF; break;
        case SFX_HYPERSPACE: target = AUDIO_STATE_HYPERSPACE; break;
        case SFX_EXPLOSION_SHIELD: target = AUDIO_STATE_EXP_SHIELD; break;
        case SFX_LIFE_LOSE: target = AUDIO_STATE_LIFE_LOSE; break;
        case SFX_GAME_OVER: target = AUDIO_STATE_GAME_OVER; break;
        default: return;
    }

    for (int i = 0; i < 8; i++) {
        if (voices[i].state == target) {
            voices[i].state = AUDIO_STATE_IDLE;
            voices[i].elapsed = 0.0f;
        }
    }
}

void sound_update(void) {
    if (audio_initialized && audio_stream) {
        for (int i = 0; i < 8; i++) {
            if (voices[i].state != AUDIO_STATE_IDLE) {
                if (voices[i].elapsed >= voices[i].duration) {
                    voices[i].state = AUDIO_STATE_IDLE;
                    voices[i].elapsed = 0.0f;
                    voices[i].volume = 0.0f;
                } else {
                    voices[i].volume = clamp01(1.0f - voices[i].elapsed / voices[i].duration);
                }
            }
        }
    }
}

void sound_set_volume(float volume) {
    (void)volume;
}
