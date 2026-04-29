#include "game.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void ship_init(Game *game) {
    game->ship.pos = (vec2){ W / 2.0f, H / 2.0f };
    game->ship.vel = (vec2){ 0.0f, 0.0f };
    game->ship.angle = -90.0f * (M_PI / 180.0f);
    game->ship.alive = true;
    game->ship.lives = 3;
    game->ship.score = 0;
    game->ship.invul_timer = INVUL_TIME;
    game->ship.shield_timer = 0.0f;
    game->ship.shield_activated = false;
    game->ship.thrusting = false;
    game->ship.rot_dir = 0;
    game->ship.shoot_timer = 0.0f;
    game->hyper_triggered = false;
}

void ship_update(Game *game, float dt) {
    Ship *s = &game->ship;
    
    if (!s->alive) return;
    
    /* Rotation */
    if (game->keys[KEY_LEFT]) s->angle = s->angle - SHIP_ROT_SPEED * dt * (M_PI / 180.0f);
    if (game->keys[KEY_RIGHT]) s->angle = s->angle + SHIP_ROT_SPEED * dt * (M_PI / 180.0f);
    
    /* Thrust */
    s->thrusting = false;
    if (game->keys[KEY_UP]) {
        s->vel.x += sinf(s->angle) * SHIP_THRUST * dt;
        s->vel.y -= cosf(s->angle) * SHIP_THRUST * dt;
        s->thrusting = true;
        if (!game->thrust_held) sound_play(SFX_THRUST);
    } else if (game->thrust_held) {
        sound_stop(SFX_THRUST);
    }
    game->thrust_held = game->keys[KEY_UP];
    
    /* Clamp speed */
    float speed = sqrtf(s->vel.x * s->vel.x + s->vel.y * s->vel.y);
    if (speed > SHIP_MAX_SPEED) {
        s->vel.x = s->vel.x * SHIP_MAX_SPEED / speed;
        s->vel.y = s->vel.y * SHIP_MAX_SPEED / speed;
    }
    
    /* Shield */
    s->shield_activated = game->keys[KEY_DOWN];
    if (s->shield_activated && !game->shield_was_pressed) {
        sound_play(SFX_SHIELD_ON);
    }
    if (!s->shield_activated) {
        sound_stop(SFX_SHIELD_ON);
    }
    game->shield_was_pressed = s->shield_activated;
    if (s->shield_activated) {
        s->shield_timer += dt;
        if (s->shield_timer >= SHIELD_DURATION) {
            s->shield_activated = false;
            s->alive = false;
            s->shield_timer = 0.0f;
            s->lives--;
            s->invul_timer = INVUL_TIME;
            particle_spawn(game, s->pos, 40, 80.0f, color_white());
            if (s->lives <= 0) {
                game->state = GSTATE_GAME_OVER;
                game->game_over_timer = 5.0f;
            }
            return;
        }
    } else {
        s->shield_timer = 0.0f;
    }
    
    /* Shooting */
    s->shoot_timer -= dt;
    if (game->keys[KEY_SHOOT] && s->alive && s->shoot_timer <= 0) {
        shot_init_player(game, s->angle);
        sound_play(SFX_SHOOT);
        s->shoot_timer = COOLDOWN;
    }
    
    /* Hyperspace (H key, edge-triggered) */
    if (game->keys[KEY_HYPER] && !game->hyper_triggered) {
        game->hyper_triggered = true;
        ship_hyperspace(game);
    }
    if (!game->keys[KEY_HYPER]) {
        game->hyper_triggered = false;
    }
    
    /* Apply velocity */
    s->pos.x += s->vel.x * dt;
    s->pos.y += s->vel.y * dt;
    
    /* Friction */
    float fric_factor = FRICTION * dt;
    s->vel.x -= s->vel.x * fric_factor;
    s->vel.y -= s->vel.y * fric_factor;
    
    /* Wrap */
    if (s->pos.x < 0.0f) s->pos.x += W;
    if (s->pos.x >= W) s->pos.x -= W;
    if (s->pos.y < 0.0f) s->pos.y += H;
    if (s->pos.y >= H) s->pos.y -= H;
    
    /* Invul timer decay */
    if (s->invul_timer > 0) s->invul_timer -= dt;
}

static void circle_points(SDL_FPoint *pts, int n, float cx, float cy, float r) {
    for (int i = 0; i < n; i++) {
        float a = (float)i / (float)n * 2.0f * (float)M_PI;
        pts[i].x = cx + cosf(a) * r;
        pts[i].y = cy + sinf(a) * r;
    }
}

void ship_draw(SDL_Renderer *ren, Ship *ship) {
    if (!ship->alive) return;
    
    /* Flickering during invulnerability */
    if (ship->invul_timer > 0) {
        int flick = ((int)(ship->invul_timer * 20)) % 2;
        if (flick == 0) return;
    }
    
    SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
    
    float r = SHIP_RADIUS * SHIP_SCALE;
    float cos_a = cosf(ship->angle);
    float sin_a = sinf(ship->angle);
    
    /* Nose */
    float nx = ship->pos.x + sin_a * r;
    float ny = ship->pos.y - cos_a * r;
    
    /* Tail: back half of ship width */
    float tx = ship->pos.x - sin_a * r * 0.5f;
    float ty = ship->pos.y + cos_a * r * 0.5f;
    
    /* Left and right tail corners */
    float perp_x = -cos_a;
    float perp_y = sin_a;
    float back_x = sin_a * r * 0.5f;
    float back_y = -cos_a * r * 0.5f;
    
    float lx = ship->pos.x - back_x + perp_x * r * 0.5f;
    float ly = ship->pos.y - back_y + perp_y * r * 0.5f;
    
    float rx = ship->pos.x - back_x - perp_x * r * 0.5f;
    float ry = ship->pos.y - back_y - perp_y * r * 0.5f;
    
    /* Draw filled triangle so it looks clean at any rotation */
    SDL_Vertex verts[3] = {
        {{nx, ny}, {1.0f, 1.0f, 1.0f, 1.0f}, {0.0f, 0.0f}},
        {{lx, ly}, {1.0f, 1.0f, 1.0f, 1.0f}, {0.0f, 0.0f}},
        {{rx, ry}, {1.0f, 1.0f, 1.0f, 1.0f}, {0.0f, 0.0f}},
    };
    SDL_RenderGeometry(ren, NULL, verts, 3, NULL, 0);
    
    /* Shield circle (rendered as line polygon) */
    if (ship->shield_activated) {
        SDL_SetRenderDrawColor(ren, 150, 150, 255, 255);
        SDL_FPoint shield_pts[49];
        circle_points(shield_pts, 49, ship->pos.x, ship->pos.y, SHIELD_RADIUS);
        SDL_RenderLines(ren, shield_pts, 49);
        SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
        SDL_RenderFillRect(ren, &(SDL_FRect){ship->pos.x, ship->pos.y, 1, 1});
    }
    
    /* Thrust flame */
    if (ship->thrusting && !ship->shield_activated) {
        float flame_len = r * 0.6f * (0.5f + 0.5f * sinf(SDL_GetTicks() * 0.02f));
        int tips = (int)(flame_len / 2.0f);
        if (tips < 2) tips = 2;
        
        SDL_FPoint flame_pts[tips + 2];
        flame_pts[0].x = lx;
        flame_pts[0].y = ly;
        for (int i = 0; i < tips; i++) {
            float t = (float)(i + 1) / (float)(tips + 1);
            flame_pts[i + 1].x = tx + (sin_a * flame_len - sin_a * r * 0.5f) * t + perp_x * r * 0.25f * sinf((float)i * 2.0f);
            flame_pts[i + 1].y = ty + (cos_a * flame_len - cos_a * r * 0.5f) * t + perp_y * r * 0.25f * sinf((float)i * 2.0f + 1.0f);
        }
        flame_pts[tips + 1].x = rx;
        flame_pts[tips + 1].y = ry;
        
        SDL_SetRenderDrawColor(ren, 255, 200, 50, 200);
        SDL_RenderLines(ren, flame_pts, tips + 2);
    }
}

void ship_hyperspace(Game *game) {
    Ship *s = &game->ship;
    if (!s->alive) return;
    
    sound_play(SFX_HYPERSPACE);
    /* 15% chance of death */
    Sint32 roll = SDL_rand(100);
    if (roll < (Sint32)(HYPERSPACE_CHANCE - 1)) {
        /* hyperspace failure - die */
        s->alive = false;
        s->lives--;
        s->invul_timer = INVUL_TIME;
        particle_spawn(game, s->pos, 40, 80.0f, color_white());
        return;
    }
    
    /* Teleport to random position */
    float rf = SDL_randf();
    float rf2 = SDL_randf();
    s->pos.x = rf * W;
    s->pos.y = rf2 * H;
    s->vel = (vec2){ 0.0f, 0.0f };
    s->invul_timer = INVUL_TIME;
    particle_spawn(game, s->pos, 15, 40.0f, color_gray());
}
