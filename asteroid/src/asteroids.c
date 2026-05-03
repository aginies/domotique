#include "game.h"
#include <math.h>
#include <stdlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static int asteroid_points_val(AstSize size) {
    switch (size) {
        case AST_SIZE_LARGE:   return AST_LARGE_POINTS;
        case AST_SIZE_MEDIUM:  return AST_MEDIUM_POINTS;
        case AST_SIZE_SMALL:   return AST_SMALL_POINTS;
    }
    return AST_LARGE_POINTS;
}

static float asteroid_radius_val(AstSize size) {
    switch (size) {
        case AST_SIZE_LARGE:   return SIZE_LARGE;
        case AST_SIZE_MEDIUM:  return SIZE_MEDIUM;
        case AST_SIZE_SMALL:   return SIZE_SMALL;
    }
    return SIZE_LARGE;
}

void ast_init_random(Game *game, int level, int idx) {
    Asteroid *ast = &game->asteroids[idx];
    ast->alive = false;
    
    /* pick size */
    AstSize sz = AST_SIZE_LARGE;
    if (game->ast_count > 0) {
        int r = SDL_rand(3);
        sz = (AstSize)r;
    } else {
        /* first asteroids on new level - always large */
        if (level == 0) {
            sz = AST_SIZE_LARGE;
        } else {
            float r3 = SDL_randf();
            if (r3 < 0.33f) sz = AST_SIZE_LARGE;
            else if (r3 < 0.66f) sz = AST_SIZE_MEDIUM;
            else sz = AST_SIZE_SMALL;
        }
    }
    
    float r_sz = asteroid_radius_val(sz);
    
    /* find position not near ship */
    for (int attempt = 0; attempt < 30; attempt++) {
        float x = SDL_randf() * W;
        float y = SDL_randf() * H;
        
        float dx = x - game->ship.pos.x;
        float dy = y - game->ship.pos.y;
        float dist = sqrtf(dx * dx + dy * dy);
        if (dist < r_sz * 4.0f + SHIP_RADIUS + 40.0f) continue;
        
        ast->size = sz;
        ast->radius = r_sz;
        ast->pos = (vec2){ x, y };
        
        float angle = SDL_randf() * 2.0f * (float)M_PI;
        float spd = ASTEROID_BASE_SPEED * (1.0f + level * 0.1f) * (0.5f + 0.5f * SDL_randf());
        ast->vel = (vec2){ cosf(angle) * spd, sinf(angle) * spd };
        
        ast->angle = SDL_randf() * 2.0f * (float)M_PI;
        ast->rot_speed = ASTEROID_ROT_SPEED * (SDL_randf() > 0.5f ? 1.0f : -1.0f) * ((float)M_PI / 180.0f);
        
        ast->verts = 8 + SDL_rand(5); /* 8-12 vertices */
        for (int v = 0; v < AST_MAX_VERTS; v++) {
            ast->vert_dist[v] = r_sz * (0.7f + 0.6f * SDL_randf());
            ast->vert_angle[v] = (int)((float)v / (float)ast->verts * 32.0f) * (float)M_PI / 16.0f;
        }
        
        ast->alive = true;
        ast->points = asteroid_points_val(sz);
        return;
    }
}

void ast_spawn_level(Game *game, int level) {
    for (int i = 0; i < MAX_ASTEROIDS; i++) {
        game->asteroids[i].alive = false;
    }
    game->ast_count = 0;
    game->level_trans_did_spawn = false;
    
    int N = 4 + level;
    if (N > 14) N = 14;
    
    for (int i = 0; i < N && game->ast_count < MAX_ASTEROIDS; i++) {
        ast_init_random(game, level, game->ast_count);
        game->ast_count++;
    }
}

void ast_update(Game *game, float dt) {
    for (int i = 0; i < game->ast_count; i++) {
        Asteroid *a = &game->asteroids[i];
        if (!a->alive) continue;
        
        a->pos.x += a->vel.x * dt;
        a->pos.y += a->vel.y * dt;
        a->angle += a->rot_speed * dt;
        
        /* Wrap with clamping */
        float half = a->radius * 0.5f;
        if (a->pos.x < -half) a->pos.x = W + half;
        if (a->pos.x > W + half) a->pos.x = -half;
        if (a->pos.y < -half) a->pos.y = H + half;
        if (a->pos.y > H + half) a->pos.y = -half;
    }
}

void ast_draw(SDL_Renderer *ren, Asteroid *a) {
    if (!a->alive) return;
    
    SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
    
    SDL_FPoint pts[AST_MAX_VERTS + 1];
    for (int i = 0; i < a->verts; i++) {
        float ra = a->vert_angle[i] + a->angle;
        pts[i].x = a->pos.x + cosf(ra) * a->vert_dist[i];
        pts[i].y = a->pos.y + sinf(ra) * a->vert_dist[i];
    }
    /* Close the polygon: last point == first point */
    pts[a->verts] = pts[0];
    SDL_RenderLines(ren, pts, a->verts + 1);
}

static bool intersects(float ax, float ay, float ar, float bx, float by, float br) {
    float dx = ax - bx;
    float dy = ay - by;
    float dist_sq = dx * dx + dy * dy;
    float min_dist = ar + br;
    return dist_sq <= min_dist * min_dist;
}

void ast_split(Asteroid *a, int idx, Game *game) {
    (void)idx;
    if (!a->alive) return;
    a->alive = false;
    
    /* Score */
    game->ship.score += a->points;
    if (game->ship.score > game->high_score) game->high_score = game->ship.score;
    
    /* Explosion sound */
    if (a->size == AST_SIZE_LARGE) {
        sound_play(SFX_EXPLOSION_LARGE);
    } else if (a->size == AST_SIZE_MEDIUM) {
        sound_play(SFX_EXPLOSION_MEDIUM);
    } else {
        sound_play(SFX_EXPLOSION_SMALL);
    }
    
    /* Explosion particles */
    particle_spawn(game, a->pos, EXPLOSION_PARTICLES, 60.0f, color_white());
    particle_spawn(game, a->pos, EXPLOSION_PARTICLES / 2, 30.0f, color_gray());
    
    /* If large or medium, split */
    AstSize next_size;
    if (a->size == AST_SIZE_LARGE) next_size = AST_SIZE_MEDIUM;
    else if (a->size == AST_SIZE_MEDIUM) next_size = AST_SIZE_SMALL;
    else return; /* small dies without splitting */
    
    /* Spawn two smaller asteroids at angles +/- some variance from original direction */
    float orig_angle = atan2f(a->vel.y, a->vel.x);
    float variance = (SDL_randf() - 0.5f) * (40.0f * ((float)M_PI / 180.0f));
    
    int third_chance = 0;
    if (a->size == AST_SIZE_LARGE && game->level >= 4) third_chance = (game->level - 3) * 10;
    if (a->size == AST_SIZE_MEDIUM && game->level >= 6) third_chance = (game->level - 5) * 10;
    
    for (int dir = -1; dir <= 1; dir += 2) {
        if (game->ast_count >= MAX_ASTEROIDS) break;
        
        float new_angle = orig_angle + variance * (float)dir;
        float spd = ASTEROID_BASE_SPEED * (1.0f + game->level * 0.1f) * (0.6f + 0.4f * SDL_randf());
        
        Asteroid *new_ast = &game->asteroids[game->ast_count];
        new_ast->size = next_size;
        new_ast->radius = asteroid_radius_val(next_size);
        new_ast->pos = a->pos;
        new_ast->vel = (vec2){ cosf(new_angle) * spd, sinf(new_angle) * spd };
        new_ast->angle = SDL_randf() * 2.0f * (float)M_PI;
        new_ast->rot_speed = ASTEROID_ROT_SPEED * (SDL_randf() > 0.5f ? 1.0f : -1.0f) * ((float)M_PI / 180.0f);
        new_ast->verts = 8 + SDL_rand(5);
        for (int v = 0; v < AST_MAX_VERTS; v++) {
            new_ast->vert_dist[v] = new_ast->radius * (0.7f + 0.6f * SDL_randf());
            new_ast->vert_angle[v] = (int)((float)v / (float)new_ast->verts * 32.0f) * (float)M_PI / 16.0f;
        }
        new_ast->alive = true;
        new_ast->points = asteroid_points_val(next_size);
        game->ast_count++;
    }
    
    /* Third split chance grows with level */
    if (third_chance > 0 && game->ast_count < MAX_ASTEROIDS && SDL_rand(100) < third_chance) {
        float perp = orig_angle + (SDL_randf() > 0.5f ? 1.0f : -1.0f) * 1.2f;
        float spd = ASTEROID_BASE_SPEED * (1.0f + game->level * 0.1f) * (0.6f + 0.4f * SDL_randf());
        
        Asteroid *new_ast = &game->asteroids[game->ast_count];
        new_ast->size = next_size;
        new_ast->radius = asteroid_radius_val(next_size);
        new_ast->pos = a->pos;
        new_ast->vel = (vec2){ cosf(perp) * spd, sinf(perp) * spd };
        new_ast->angle = SDL_randf() * 2.0f * (float)M_PI;
        new_ast->rot_speed = ASTEROID_ROT_SPEED * (SDL_randf() > 0.5f ? 1.0f : -1.0f) * ((float)M_PI / 180.0f);
        new_ast->verts = 8 + SDL_rand(5);
        for (int v = 0; v < AST_MAX_VERTS; v++) {
            new_ast->vert_dist[v] = new_ast->radius * (0.7f + 0.6f * SDL_randf());
            new_ast->vert_angle[v] = (int)((float)v / (float)new_ast->verts * 32.0f) * (float)M_PI / 16.0f;
        }
        new_ast->alive = true;
        new_ast->points = asteroid_points_val(next_size);
        game->ast_count++;
    }
}

void ast_collisions(Game *game) {
    /* Shot vs Asteroid */
    for (int si = 0; si < game->shot_count; si++) {
        Shot *shot = &game->shots[si];
        if (!shot->alive || shot->is_enemy) continue;
        
        for (int ai = 0; ai < game->ast_count; ai++) {
            Asteroid *a = &game->asteroids[ai];
            if (!a->alive) continue;
            
            if (intersects(shot->pos.x, shot->pos.y, 3.0f, a->pos.x, a->pos.y, a->radius)) {
                shot->alive = false;
                ast_split(a, ai, game);
                break;
            }
        }
    }
    
    /* Shot vs Saucer */
    for (int si = 0; si < game->shot_count; si++) {
        Shot *shot = &game->shots[si];
        if (!shot->alive) continue;
        
        for (int sci = 0; sci < game->saucer_count; sci++) {
            Saucer *sc = &game->saucers[sci];
            if (!sc->alive) continue;
            
            float sc_radius = sc->type == SAUCER_BIG ? SIZE_LARGE * 0.6f : SIZE_MEDIUM * 0.6f;
            if (intersects(shot->pos.x, shot->pos.y, 12.0f, sc->pos.x, sc->pos.y, sc_radius)) {
                shot->alive = false;
                sc->alive = false;
                game->ship.score += sc->points_value;
                if (game->ship.score > game->high_score) game->high_score = game->ship.score;
                particle_spawn(game, sc->pos, EXPLOSION_PARTICLES * 2, 80.0f, color_white());
                particle_spawn(game, sc->pos, EXPLOSION_PARTICLES, 60.0f, color_gold());
                break;
            }
        }
    }
    
    /* Player shot vs saucer (friendly fire - doesn't work in original but let's do enemy shots vs ship) */
    
    /* Enemy shot vs ship */
    if (game->ship.alive && game->ship.invul_timer <= 0 && !game->ship.shield_activated) {
        for (int si = 0; si < game->shot_count; si++) {
            Shot *shot = &game->shots[si];
            if (!shot->alive || !shot->is_enemy) continue;
            
            if (intersects(shot->pos.x, shot->pos.y, 3.0f, game->ship.pos.x, game->ship.pos.y, SHIP_RADIUS)) {
                shot->alive = false;
                /* ship dies */
                game->ship.alive = false;
                game->ship.lives--;
                game->ship.invul_timer = INVUL_TIME;
                particle_spawn(game, game->ship.pos, 40, 80.0f, color_white());
                sound_play(SFX_LIFE_LOSE);
                
                if (game->ship.lives <= 0) {
                    game->state = GSTATE_GAME_OVER;
                    game->game_over_timer = 5.0f;
                }
                break;
            }
        }
    }
    
    /* Ship vs Asteroid or Saucer (only if not invulnerable and not shielded) */
    if (game->ship.alive && game->ship.invul_timer <= 0 && !game->ship.shield_activated) {
        /* Ship vs Asteroid */
        for (int ai = 0; ai < game->ast_count; ai++) {
            Asteroid *a = &game->asteroids[ai];
            if (!a->alive) continue;
            
            if (intersects(game->ship.pos.x, game->ship.pos.y, SHIP_RADIUS, a->pos.x, a->pos.y, a->radius)) {
                game->ship.alive = false;
                game->ship.lives--;
                game->ship.invul_timer = INVUL_TIME;
                ast_split(a, ai, game);
                particle_spawn(game, game->ship.pos, 50, 90.0f, color_white());
                sound_play(SFX_LIFE_LOSE);
                
                if (game->ship.lives <= 0) {
                    game->state = GSTATE_GAME_OVER;
                    game->game_over_timer = 5.0f;
                }
                break;
            }
        }
        
        /* Ship vs Saucer */
        if (game->ship.alive) {
            for (int sci = 0; sci < game->saucer_count; sci++) {
                Saucer *sc = &game->saucers[sci];
                if (!sc->alive) continue;
                
                float sc_radius = sc->type == SAUCER_BIG ? SIZE_LARGE * 0.6f : SIZE_MEDIUM * 0.6f;
                if (intersects(game->ship.pos.x, game->ship.pos.y, SHIP_RADIUS, sc->pos.x, sc->pos.y, sc_radius)) {
                    game->ship.alive = false;
                    game->ship.lives--;
                    game->ship.invul_timer = INVUL_TIME;
                    sc->alive = false;
                    game->ship.score += sc->points_value;
                    if (game->ship.score > game->high_score) game->high_score = game->ship.score;
                    particle_spawn(game, sc->pos, 30, 70.0f, color_white());
                    particle_spawn(game, game->ship.pos, 40, 80.0f, color_white());
                    sound_play(SFX_LIFE_LOSE);
                    
                    if (game->ship.lives <= 0) {
                        game->state = GSTATE_GAME_OVER;
                        game->game_over_timer = 5.0f;
                    }
                    break;
                }
            }
        }
    }
}
