#include "game.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static Saucer *find_free_saucer(Game *game) {
    for (int i = 0; i < MAX_SAUCERS; i++) {
        if (!game->saucers[i].alive) return &game->saucers[i];
    }
    return NULL;
}

void saucer_init(Game *game, SaucerType type) {
    Saucer *sc = find_free_saucer(game);
    if (!sc) return;
    
    sc->type = type;
    sc->alive = true;
    
    /* Spawn from left or right */
    int side = SDL_rand(2);
    if (side == 0) {
        sc->pos.x = -SIZE_LARGE * 2.0f;
        sc->dir = 1;
    } else {
        sc->pos.x = W + SIZE_LARGE * 2.0f;
        sc->dir = -1;
    }
    sc->pos.y = SDL_randf() * H * 0.6f + H * 0.1f;
    
    sc->vel.x = SAUCER_SPEED * sc->dir;
    sc->vel.y = SAUCER_SPEED * (SDL_randf() - 0.5f) * 0.1f;
    
    sc->shoot_timer = (type == SAUCER_BIG) ? SAUCER_SHOOT_INTERVAL_BG : SAUCER_SHOOT_INTERVAL_SM;
    sc->enter_timer = 0.0f;
    sc->color_timer = 0.0f;
    
    int score_groups = game->ship.score / SAUCER_POINTS_STEP;
    sc->points_value = SAUCER_POINTS_BASE + score_groups * 100;
    if (sc->points_value > 300) sc->points_value = 300;
}

void saucer_update(Game *game, float dt) {
    for (int i = 0; i < MAX_SAUCERS; i++) {
        Saucer *sc = &game->saucers[i];
        if (!sc->alive) continue;
        
        sc->pos.x += sc->vel.x * dt;
        sc->pos.y += sc->vel.y * dt;
        
        sc->enter_timer += dt;
        
        /* Off screen */
        if (sc->dir == 1 && sc->pos.x > W + SIZE_LARGE * 2.0f) sc->alive = false;
        if (sc->dir == -1 && sc->pos.x < -SIZE_LARGE * 2.0f) sc->alive = false;
        
        /* Shooting */
        sc->shoot_timer -= dt;
        if (sc->shoot_timer <= 0) {
            /* Aim at ship for small saucer */
            float angle;
            if (sc->type == SAUCER_SMALL && game->ship.alive) {
                float dx = game->ship.pos.x - sc->pos.x;
                float dy = game->ship.pos.y - sc->pos.y;
                float orig_angle = atan2f(dy, dx);
                /* Accuracy: 20 deg at 0 score, 0 deg at 40000 score */
                float accuracy = SDL_max(0.0f, 20.0f - (game->ship.score / 40000.0f * 20.0f)) * ((float)M_PI / 180.0f);
                angle = orig_angle + (SDL_randf() - 0.5f) * accuracy * 2.0f;
            } else {
                angle = SDL_randf() * 2.0f * (float)M_PI;
            }
            shot_init_enemy(game, sc, angle);
            sc->shoot_timer = (sc->type == SAUCER_BIG) ? SAUCER_SHOOT_INTERVAL_BG : SAUCER_SHOOT_INTERVAL_SM;
        }
    }
}

void saucer_draw(SDL_Renderer *ren, Saucer *sc) {
    if (!sc->alive) return;
    
    SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
    
    float width, height;
    if (sc->type == SAUCER_BIG) {
        width = SIZE_LARGE * 0.6f;
        height = SIZE_MEDIUM * 0.5f;
    } else {
        width = SIZE_MEDIUM * 0.5f;
        height = SIZE_SMALL * 0.4f;
    }
    
    float enter_scale = SDL_min(1.0f, sc->enter_timer);
    
    /* Ellipse approximation */
    int seg_count = 36;
    SDL_FPoint ellipse_pts[seg_count + 1];
    for (int i = 0; i <= seg_count; i++) {
        float a = (float)i / (float)seg_count * 2.0f * (float)M_PI;
        ellipse_pts[i].x = sc->pos.x + cosf(a) * width * enter_scale;
        ellipse_pts[i].y = sc->pos.y + sinf(a) * height * enter_scale;
    }
    SDL_RenderLines(ren, ellipse_pts, seg_count + 1);
    
    /* Dome on top */
    SDL_FPoint dome_pts[19];
    int dome_count = 0;
    for (int i = 0; i <= 9; i++) {
        float a = (float)i / 9.0f * M_PI;
        dome_pts[dome_count].x = sc->pos.x - cosf(a) * width * 0.4f * enter_scale;
        dome_pts[dome_count].y = sc->pos.y - sinf(a) * height * 0.6f * enter_scale;
        dome_count++;
    }
    SDL_RenderLines(ren, dome_pts, dome_count);
}

void saucer_spawn(Game *game) {
    int alive_count = 0;
    for (int i = 0; i < MAX_SAUCERS; i++) {
        if (game->saucers[i].alive) alive_count++;
    }
    if (alive_count >= SAUCER_MAX_ALIVE) return;
    
    SaucerType type = SAUCER_BIG;
    if (game->ship.score >= 40000 && SDL_randf() > 0.3f) {
        type = SAUCER_SMALL;
    }
    saucer_init(game, type);
}
