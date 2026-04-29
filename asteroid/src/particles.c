#include "game.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void particle_spawn(Game *game, vec2 pos, int count, float speed_range, color col) {
    for (int i = 0; i < count; i++) {
        int idx = -1;
        for (int j = 0; j < MAX_PARTICLES; j++) {
            if (!game->particles[j].alive) { idx = j; break; }
        }
        if (idx == -1) break;
        
        Particle *p = &game->particles[idx];
        p->pos = pos;
        
        float angle = SDL_randf() * 2.0f * (float)M_PI;
        float spd = speed_range * SDL_randf();
        p->vel = (vec2){ cosf(angle) * spd, sinf(angle) * spd };
        
        p->life = 0.3f + SDL_randf() * 0.7f;
        p->max_life = p->life;
        p->size = 1.0f + SDL_randf() * 2.0f;
        p->col = col;
        p->alive = true;
    }
}

void particle_update(Game *game, float dt) {
    for (int i = 0; i < MAX_PARTICLES; i++) {
        Particle *p = &game->particles[i];
        if (!p->alive) continue;
        
        p->life -= dt;
        if (p->life <= 0) {
            p->alive = false;
            continue;
        }
        
        p->pos.x += p->vel.x * dt;
        p->pos.y += p->vel.y * dt;
    }
}

void particle_draw(SDL_Renderer *ren, Game *game) {
    for (int i = 0; i < MAX_PARTICLES; i++) {
        Particle *p = &game->particles[i];
        if (!p->alive) continue;
        
        float alpha_frac = p->life / p->max_life;
        SDL_SetRenderDrawColor(ren, p->col.r, p->col.g, p->col.b, (uint8_t)(255 * alpha_frac));
        SDL_RenderPoint(ren, p->pos.x + 0.5f, p->pos.y + 0.5f);
    }
}
