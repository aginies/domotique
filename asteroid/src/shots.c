#include "game.h"
#include <math.h>
#include <stdlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static void *find_free_game(Game *game) {
    for (int i = 0; i < MAX_SHOTS; i++) {
        if (!game->shots[i].alive) return &game->shots[i];
    }
    return NULL;
}

void shot_init_player(Game *game, float angle) {
    Shot *s = (Shot *)find_free_game(game);
    if (!s) return;
    
    /* Spawn at ship nose */
    float ship_r = SHIP_RADIUS * SHIP_SCALE;
    float nose_x = game->ship.pos.x + sinf(angle) * ship_r;
    float nose_y = game->ship.pos.y - cosf(angle) * ship_r;
    
    s->pos = (vec2){ nose_x, nose_y };
    float cos_a = cosf(angle);
    float sin_a = sinf(angle);
    s->vel = (vec2){
        game->ship.vel.x + sin_a * SHOT_SPEED,
        game->ship.vel.y - cos_a * SHOT_SPEED
    };
    s->alive = true;
    s->is_enemy = false;
    s->life = SHOT_LIFE;
}

void shot_init_enemy(Game *game, Saucer *sc, float angle) {
    Shot *s = (Shot *)find_free_game(game);
    if (!s) return;
    
    float sc_width = sc->type == SAUCER_BIG ? SIZE_LARGE * 0.6f : SIZE_MEDIUM * 0.5f;
    s->pos.x = sc->pos.x;
    s->pos.y = sc->pos.y + sc_width * 0.7f;
    
    s->vel.x = sinf(angle) * SHOT_SPEED + sc->vel.x;
    s->vel.y = -cosf(angle) * SHOT_SPEED + sc->vel.y;
    
    s->alive = true;
    s->is_enemy = true;
    s->life = SHOT_LIFE;
}

void shot_update(Game *game, float dt) {
    for (int i = 0; i < MAX_SHOTS; i++) {
        Shot *s = &game->shots[i];
        if (!s->alive) continue;
        
        s->pos.x += s->vel.x * dt;
        s->pos.y += s->vel.y * dt;
        s->life -= dt;
        
        if (s->life <= 0) {
            s->alive = false;
            continue;
        }
        
        if (s->pos.x < 0.0f) s->pos.x += W;
        if (s->pos.x >= W) s->pos.x -= W;
        if (s->pos.y < 0.0f) s->pos.y += H;
        if (s->pos.y >= H) s->pos.y -= H;
    }
}

void shot_draw(SDL_Renderer *ren, Shot *shot) {
    if (!shot->alive) return;
    
    float line_len = 4.0f;
    float dir = atan2f(shot->vel.x, shot->vel.y);
    
    float x1 = shot->pos.x + sinf(dir) * line_len;
    float y1 = shot->pos.y - cosf(dir) * line_len;
    float x2 = shot->pos.x - sinf(dir) * line_len;
    float y2 = shot->pos.y + cosf(dir) * line_len;
    
    if (shot->is_enemy) {
        SDL_SetRenderDrawColor(ren, 255, 255, 0, 255);
    } else {
        SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
    }
    SDL_RenderLine(ren, x1 + 0.5f, y1 + 0.5f, x2 + 0.5f, y2 + 0.5f);
}
