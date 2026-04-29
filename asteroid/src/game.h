#ifndef GAME_H
#define GAME_H

#include <SDL3/SDL.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/* Screen dimensions */
#define W  1024
#define H  768
#define FPS 60

/* Ship constants */
#define SHIP_SCALE 1.0f
#define SHIP_RADIUS 12.0f
#define SHIP_THRUST 15.0f
#define SHIP_MAX_SPEED 9999.0f
#define SHIP_ROT_SPEED 250.0f
#define SHIP_MASS 1.0f
#define FRICTION 0.01f
#define INVUL_TIME 3.0f
#define SHIELD_DURATION 2.0f
#define SHIELD_RADIUS 25.0f
#define HYPERSPACE_CHANCE 15.0f
#define COOLDOWN 0.15f

/* Shot constants */
#define SHOT_SPEED 300.0f
#define SHOT_LIFE 1.0f

/* Asteroid constants */
#define ASTEROID_BASE_SPEED 20.0f
#define ASTEROID_ROT_SPEED 80.0f
#define AST_MAX_VERTS 12
#define AST_MIN_VERTS 8

/* Saucer constants */
#define SAUCER_SPEED 150.0f
#define SAUCER_SHOOT_INTERVAL_BG 2.0f
#define SAUCER_SHOOT_INTERVAL_SM 0.8f
#define SAUCER_SPAWN_INTERVAL 60.0f
#define SAUCER_MAX_ALIVE 2
#define SAUCER_POINTS_BASE 100
#define SAUCER_POINTS_STEP 5500

/* Particle constants */
#define PARTICLE_POOL 512
#define EXPLOSION_PARTICLES 20

/* Vector2 */
typedef struct { float x, y; } vec2;

vec2 vec2_add(vec2 a, vec2 b);
vec2 vec2_sub(vec2 a, vec2 b);
vec2 vec2_mul(vec2 a, float s);
float vec2_dot(vec2 a, vec2 b);
float vec2_len(vec2 a);
vec2 vec2_norm(vec2 a);
vec2 vec2_rotate(vec2 a, float angle_rad);

/* Rect */
typedef struct { float x, y, w, h; } rect;

/* Color */
typedef struct { uint8_t r, g, b, a; } color;

color color_white(void);
color color_gray(void);
color color_gold(void);
color color_red(void);
color color_magenta(void);
color color_blue(void);
color color_yellow(void);

/* Scoring */
#define AST_LARGE_POINTS 20
#define AST_MEDIUM_POINTS 50
#define AST_SMALL_POINTS 100

/* Sizes */
#define SIZE_LARGE 40.0f
#define SIZE_MEDIUM 25.0f
#define SIZE_SMALL 15.0f

/* Enums */
typedef enum {
    AST_SIZE_LARGE = 0,
    AST_SIZE_MEDIUM,
    AST_SIZE_SMALL
} AstSize;

typedef enum { SAUCER_BIG = 0, SAUCER_SMALL } SaucerType;

typedef enum {
    GSTATE_TITLE = 0,
    GSTATE_PLAYING,
    GSTATE_LEVEL_TRANS,
    GSTATE_GAME_OVER
} GState;

typedef enum {
    KEY_LEFT = 0,
    KEY_RIGHT,
    KEY_UP,
    KEY_DOWN,
    KEY_SHOOT,
    KEY_HYPER,
    KEY_ENTER,
    KEY_ESCAPE,
    KEY_COUNT
} GameKey;

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

/* Ship */
typedef struct {
    vec2 pos;
    vec2 vel;
    float angle;        /* radians, 0 = up */
    bool alive;
    int lives;
    int score;
    float invul_timer;
    float shield_timer;
    bool shield_activated;
    bool thrusting;
    int rot_dir;        /* -1 or 1 */
    float shoot_timer;
} Ship;

/* Asteroid */
typedef struct {
    vec2 pos;
    vec2 vel;
    float radius;
    AstSize size;
    float angle;
    float rot_speed;  /* radians/s */
    int verts;        /* number of vertices (8-12) */
    float vert_dist[AST_MAX_VERTS];
    float vert_angle[AST_MAX_VERTS];
    bool alive;
    int points;
} Asteroid;

/* Saucer */
typedef struct {
    vec2 pos;
    vec2 vel;
    SaucerType type;
    int dir;           /* +1 right, -1 left */
    bool alive;
    float shoot_timer;
    float enter_timer; /* entry animation */
    float color_timer;
    int points_value;
} Saucer;

/* Shot */
typedef struct {
    vec2 pos;
    vec2 vel;
    bool alive;
    bool is_enemy;
    float life;
} Shot;

/* Particle */
typedef struct {
    vec2 pos;
    vec2 vel;
    float life;
    float max_life;
    float size;
    color col;
    bool alive;
} Particle;

/* Game */
#define MAX_SHOTS 128
#define MAX_ASTEROIDS 64
#define MAX_SAUCERS 4
#define MAX_PARTICLES PARTICLE_POOL

typedef struct Game {
    GState state;
    Ship ship;
    Asteroid asteroids[MAX_ASTEROIDS];
    int ast_count;
    Saucer saucers[MAX_SAUCERS];
    int saucer_count;
    Shot shots[MAX_SHOTS];
    int shot_count;
    Particle particles[MAX_PARTICLES];
    int particle_count;
    int level;
    float saucer_timer;
    float level_trans_timer;
    float game_over_timer;
    int high_score;
    bool quit;
    bool keys[KEY_COUNT];
    float dt;
    Uint32 last_time;
    bool level_trans_did_spawn;
    bool hyper_triggered;
} Game;

/* Ship functions */
void ship_init(Game *game);
void ship_update(Game *game, float dt);
void ship_draw(SDL_Renderer *ren, Ship *ship);
void ship_hyperspace(Game *game);

/* Asteroid functions */
void ast_init_random(Game *game, int level, int idx);
void ast_spawn_level(Game *game, int level);
void ast_update(Game *game, float dt);
void ast_draw(SDL_Renderer *ren, Asteroid *ast);
void ast_collisions(Game *game);
void ast_split(Asteroid *a, int idx, Game *game);

/* Saucer functions */
void saucer_init(Game *game, SaucerType type);
void saucer_update(Game *game, float dt);
void saucer_draw(SDL_Renderer *ren, Saucer *sc);
void saucer_spawn(Game *game);

/* Shot functions */
void shot_init_player(Game *game, float angle);
void shot_init_enemy(Game *game, Saucer *sc, float angle);
void shot_update(Game *game, float dt);
void shot_draw(SDL_Renderer *ren, Shot *shot);

/* Particle functions */
void particle_spawn(Game *game, vec2 pos, int count, float speed_range, color col);
void particle_update(Game *game, float dt);
void particle_draw(SDL_Renderer *ren, Game *game);

/* UI functions */
void ui_draw(SDL_Renderer *ren, Game *game);
int ui_draw_number(SDL_Renderer *ren, int x, int y, int n, int scale, color c);

/* Font */
int font_text_width(const char *text, int scale);
void font_draw(SDL_Renderer *ren, int x, int y, const char *text, int scale, color c);
void font_draw_char(SDL_Renderer *ren, int x, int y, int ch_idx, int scale, color c);

/* Game engine */
void game_init(Game *game);
void game_update(Game *game, float dt);
void game_render(SDL_Renderer *ren, Game *game);
void handle_event(Game *game, SDL_Event *ev);

#endif /* GAME_H */
