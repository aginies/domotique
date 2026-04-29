#ifndef ASTEROIDS_H
#define ASTEROIDS_H

#include "game.h"

void ast_init_random(Game *game, int level, int idx);
void ast_spawn_level(Game *game, int level);
void ast_update(Game *game, float dt);
void ast_draw(SDL_Renderer *ren, Asteroid *a);
void ast_split(Asteroid *a, int idx, Game *game);
void ast_collisions(Game *game);

#endif /* ASTEROIDS_H */
