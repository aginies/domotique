#ifndef SOUND_H
#define SOUND_H

typedef enum {
    SFX_THRUST = 0,
    SFX_SHOOT,
    SFX_EXPLOSION_LARGE,
    SFX_EXPLOSION_MEDIUM,
    SFX_EXPLOSION_SMALL,
    SFX_SAUCER,
    SFX_SHIELD_ON,
    SFX_SHIELD_OFF,
    SFX_HYPERSPACE,
    SFX_EXPLOSION_SHIELD,
    SFX_LIFE_LOSE,
    SFX_GAME_OVER,
    SFX_COUNT
} SoundEffect;

void sound_init(void);
void sound_shutdown(void);
void sound_play(SoundEffect effect);
void sound_stop(SoundEffect effect);
void sound_set_volume(float volume);
void sound_update(void);

#endif /* SOUND_H */

