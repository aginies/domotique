#include <math.h>
#include <string.h>
#include "game.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

color color_white(void)    { return (color){ 255, 255, 255, 255 }; }
color color_gray(void)     { return (color){ 150, 150, 150, 255 }; }
color color_gold(void)     { return (color){ 255, 200, 50, 255 }; }
color color_red(void)      { return (color){ 255, 50, 50, 255 }; }
color color_magenta(void)  { return (color){ 255, 50, 255, 255 }; }
color color_blue(void)     { return (color){ 50, 50, 255, 255 }; }
color color_yellow(void)   { return (color){ 255, 255, 0, 255 }; }

static void game_clear_shots(Game *game) {
    for (int i = 0; i < MAX_SHOTS; i++) game->shots[i].alive = false;
    game->shot_count = 0;
}

static void game_clear_particles(Game *game) {
    for (int i = 0; i < MAX_PARTICLES; i++) game->particles[i].alive = false;
    game->particle_count = 0;
}

void game_init(Game *game) {
    memset(game, 0, sizeof(Game));
    game->state = GSTATE_TITLE;
    game->ship.lives = 3;
    game->ship.score = 0;
    game->ship.invul_timer = INVUL_TIME;
    game->level = 0;
    game->high_score = 0;
    game->saucer_timer = SAUCER_SPAWN_INTERVAL;
    game->level_trans_timer = 0.0f;
    game->game_over_timer = 0.0f;
    game->quit = false;
    game->last_time = SDL_GetTicks();
    for (int i = 0; i < MAX_SAUCERS; i++) game->saucers[i].alive = false;
    for (int i = 0; i < MAX_SHOTS; i++) game->shots[i].alive = false;
    for (int i = 0; i < MAX_PARTICLES; i++) game->particles[i].alive = false;
}

void game_update(Game *game, float dt) {
    switch (game->state) {
        case GSTATE_TITLE:
            if (game->keys[KEY_ENTER]) {
                game->state = GSTATE_PLAYING;
                ship_init(game);
                ast_spawn_level(game, 0);
                game_clear_shots(game);
                game_clear_particles(game);
                game->saucer_timer = 0;
            }
            if (game->keys[KEY_ESCAPE]) game->quit = true;
            break;
            
        case GSTATE_PLAYING:
            /* Always decay invul timer (even when ship is dead) */
            if (game->ship.invul_timer > 0) game->ship.invul_timer -= dt;
            
            /* Respawn ship when dead and invulnerability expired */
            if (!game->ship.alive && game->ship.invul_timer <= 0 && game->ship.lives > 0) {
                game->ship.alive = true;
                game->ship.pos = (vec2){ W / 2.0f, H / 2.0f };
                game->ship.vel = (vec2){ 0.0f, 0.0f };
                game->ship.invul_timer = INVUL_TIME;
            }
            
            if (game->ship.alive) {
                ship_update(game, dt);
            }
            
            game->saucer_timer += dt;
            float saucer_interval = SAUCER_SPAWN_INTERVAL - (float)game->level * 2.0f;
            if (saucer_interval < 20.0f) saucer_interval = 20.0f;
            if (game->saucer_timer >= saucer_interval) {
                saucer_spawn(game);
                game->saucer_timer = 0.0f;
            }
            
            int ast_alive = 0;
            for (int i = 0; i < game->ast_count; i++) {
                if (game->asteroids[i].alive) ast_alive++;
            }
            if (ast_alive == 0 && game->level >= 0) {
                game->state = GSTATE_LEVEL_TRANS;
                game->level_trans_timer = 2.0f;
                game->level_trans_did_spawn = false;
            }
            
            shot_update(game, dt);
            particle_update(game, dt);
            
            game->shot_count = 0;
            for (int i = 0; i < MAX_SHOTS; i++) {
                if (game->shots[i].alive) game->shot_count++;
            }
            
            ast_collisions(game);
            ast_update(game, dt);
            saucer_update(game, dt);
            break;
            
        case GSTATE_LEVEL_TRANS:
            game->level_trans_timer -= dt;
            if (game->level_trans_timer <= 0 && !game->level_trans_did_spawn) {
                game->level_trans_did_spawn = true;
                game->level++;
                ast_spawn_level(game, game->level);
                game->state = GSTATE_PLAYING;
                ship_init(game);
                game_clear_particles(game);
            }
            break;
            
        case GSTATE_GAME_OVER:
            game->game_over_timer -= dt;
            if (game->game_over_timer <= 0) {
                if (game->keys[KEY_ENTER]) {
                    if (game->ship.score > game->high_score) {
                        game->high_score = game->ship.score;
                    }
                    game_init(game);
                    game->state = GSTATE_TITLE;
                }
                if (game->keys[KEY_ESCAPE]) game->quit = true;
            }
            break;
    }
}

void game_render(SDL_Renderer *ren, Game *game) {
    SDL_SetRenderDrawColor(ren, 0, 0, 0, 255);
    SDL_RenderClear(ren);
    
    if (game->state == GSTATE_PLAYING) {
        for (int i = 0; i < game->ast_count; i++) {
            if (game->asteroids[i].alive) ast_draw(ren, &game->asteroids[i]);
        }
        for (int i = 0; i < MAX_SAUCERS; i++) {
            if (game->saucers[i].alive) saucer_draw(ren, &game->saucers[i]);
        }
        for (int i = 0; i < MAX_SHOTS; i++) {
            if (game->shots[i].alive) shot_draw(ren, &game->shots[i]);
        }
        ship_draw(ren, &game->ship);
        particle_draw(ren, game);
    }
    
    ui_draw(ren, game);
    SDL_RenderPresent(ren);
}

void handle_event(Game *game, SDL_Event *ev) {
    switch (ev->type) {
        case SDL_EVENT_QUIT:
            game->quit = true;
            break;
            
        case SDL_EVENT_KEY_DOWN:
            switch (ev->key.key) {
                case SDLK_LEFT:  game->keys[KEY_LEFT] = true;  break;
                case SDLK_RIGHT: game->keys[KEY_RIGHT] = true;  break;
                case SDLK_UP:    game->keys[KEY_UP] = true;    break;
                case SDLK_DOWN:  game->keys[KEY_DOWN] = true;  break;
                case SDLK_SPACE: game->keys[KEY_SHOOT] = true; break;
                case SDLK_H:     game->keys[KEY_HYPER] = true; break;
                case SDLK_RETURN:game->keys[KEY_ENTER] = true; break;
                case SDLK_ESCAPE:game->keys[KEY_ESCAPE] = true; break;
            }
            break;
            
        case SDL_EVENT_KEY_UP:
            switch (ev->key.key) {
                case SDLK_LEFT:  game->keys[KEY_LEFT] = false; break;
                case SDLK_RIGHT: game->keys[KEY_RIGHT] = false; break;
                case SDLK_UP:    game->keys[KEY_UP] = false;  break;
                case SDLK_DOWN:  game->keys[KEY_DOWN] = false; break;
                case SDLK_SPACE: game->keys[KEY_SHOOT] = false;break;
                case SDLK_H:     game->keys[KEY_HYPER] = false; break;
                case SDLK_RETURN:game->keys[KEY_ENTER] = false;break;
                case SDLK_ESCAPE:game->keys[KEY_ESCAPE] = false;break;
            }
            break;
    }
}
