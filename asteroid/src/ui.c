#include "game.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

/* 5x7 bitmap font character data. Index = ASCII - 32 */
static const uint8_t FONT_DATA[95][7] = {
    {0,0,0,0,0,0,0},{0,0,8,8,8,8,0},{6,6,0,0,0,0,0},{0,0,0,126,0,0,0},
    {0,0,0,126,0,0,0},{126,0,0,0,0,0,0},{0,0,0,0,0,0,0},{0,0,0,12,6,0,0},
    {0,12,24,24,12,0,0},{0,6,24,24,6,0,0},{0,0,26,0,26,0,0},{0,0,28,28,0,0,0},
    {0,0,0,0,0,6,0},{0,0,0,126,0,0,0},{0,0,0,0,0,6,0},{0,24,48,96,64,0,0},
    {0,28,48,48,48,28,0},{0,8,12,8,8,8,0},{0,28,48,24,12,6,0},{0,28,48,24,48,28,0},
    {0,14,48,48,126,0,0},{0,126,48,28,6,126,0},{0,28,48,28,48,28,0},{0,60,96,96,24,12,0},
    {0,28,48,28,48,28,0},{0,28,48,60,6,28,0},{0,24,24,0,0,0,0},{0,24,0,6,6,0,0},
    {0,6,12,24,12,6,0},{0,0,126,126,0,0,0},{0,6,12,24,12,6,0},{0,28,48,24,12,0,0},
    {0,0,0,0,0,0,0},{0,24,48,48,126,48,48},{0,60,102,60,102,96,60},{0,28,48,48,48,48,28},
    {0,60,102,102,102,96,60},{0,126,48,48,60,48,126},{0,126,48,48,60,48,48},{0,28,48,48,48,54,28},
    {0,48,48,48,126,48,48},{0,28,24,24,24,24,28},{0,60,48,48,48,48,24},{0,12,24,48,24,12,6},
    {0,60,48,48,48,48,48},{0,24,60,102,48,48,24},{0,48,96,96,102,60,24},{0,28,48,48,48,48,28},
    {0,60,102,102,60,48,48},{0,28,48,48,54,12,24},{0,60,102,102,60,24,12},{0,28,48,126,6,48,28},
    {0,30,24,24,24,24,24},{0,48,48,48,48,48,28},{0,48,48,48,24,24,12},{0,24,24,24,60,102,102},
    {0,12,24,48,48,24,12},{0,6,12,48,48,24,24},{0,7,6,12,24,48,126},{0,28,24,24,24,24,28},
    {0,0,0,28,48,28,0},{0,60,48,48,60,6,12},{0,0,0,28,48,48,28},{0,28,48,48,48,24,28},
    {0,0,0,28,48,54,12},{0,24,60,24,24,24,48},{0,0,0,28,48,54,28},{0,24,48,48,60,6,12},
    {0,12,12,0,0,0,0},{0,48,48,24,24,24,16},{0,28,48,24,12,24,12},{0,28,24,24,24,24,28},
    {0,0,0,60,102,96,48},{0,0,0,60,102,6,12},{0,0,0,28,48,48,28},{0,60,102,102,60,48,48},
    {0,28,48,48,48,24,28},{0,0,0,60,102,6,12},{0,0,0,30,48,30,0},{0,24,24,62,24,24,16},
    {0,0,0,48,48,48,28},{0,0,0,24,24,12,6},{0,0,0,24,60,102,102},{0,0,0,12,48,48,12},
    {0,0,0,48,48,24,28},{0,0,0,24,60,102,102},{0,0,0,12,48,48,12},{0,6,12,24,12,6,0},
    {0,24,24,24,24,24,24},{0,6,12,24,12,6,0},{0,0,0,0,0,0,0}
};

int font_text_width(const char *text, int scale) {
    int total = 0;
    for (const char *p = text; *p; p++) {
        int ch = (unsigned char)*p;
        if (ch >= 32 && ch <= 126) total += scale * (5 + 2);
    }
    return total;
}

void font_draw_char(SDL_Renderer *ren, int x, int y, int ch_idx, int scale, color c) {
    if (ch_idx < 0 || ch_idx >= 95) return;
    const uint8_t *glyph = FONT_DATA[ch_idx];
    for (int row = 0; row < 7; row++) {
        uint8_t bits = glyph[row];
        for (int col = 0; col < 5; col++) {
            if (bits & (0x20 >> col)) {
                int px = x + col * scale;
                int py = y + row * scale;
                SDL_SetRenderDrawColor(ren, c.r, c.g, c.b, c.a);
                SDL_RenderFillRect(ren, &(SDL_FRect){(float)px, (float)py, (float)scale, (float)scale});
            }
        }
    }
}

void font_draw(SDL_Renderer *ren, int x, int y, const char *text, int scale, color c) {
    int cur_x = x;
    for (const char *p = text; *p; p++) {
        int ch = (unsigned char)*p;
        if (ch >= 32 && ch <= 126) {
            font_draw_char(ren, cur_x, y, ch - 32, scale, c);
            cur_x += scale * (5 + 1);
        }
    }
}

void ui_draw_score(SDL_Renderer *ren, Game *game);

static void draw_text_box(SDL_Renderer *ren, int x, int y, int w, int h) {
    SDL_SetRenderDrawColor(ren, 0, 0, 0, 180);
    SDL_RenderFillRect(ren, &(SDL_FRect){(float)(x - 8), (float)(y - 8), (float)(w + 16), (float)(h + 16)});
}

void ui_draw_score_impl(SDL_Renderer *ren, int score, int x, int y, int scale) {
    char buf[16];
    SDL_snprintf(buf, sizeof(buf), "%d", score);
    int tw = font_text_width(buf, scale);
    int th = scale * 7;
    draw_text_box(ren, x - tw, y, tw, th);
    font_draw(ren, x - tw, y, buf, scale, color_white());
}

void ui_draw_score(SDL_Renderer *ren, Game *game) {
    if (!game->ship.alive) {
        ui_draw_score_impl(ren, game->ship.score, W - 16, 10, 8);
    } else {
        ui_draw_score_impl(ren, game->ship.score, W / 2, 10, 8);
    }
}

void ui_draw(SDL_Renderer *ren, Game *game) {
    if (game->state == GSTATE_PLAYING) {
        /* Lives as small ship icons on the far right */
        int icon_scale = 3;
        int ship_w = 6 * icon_scale;
        int ship_h = 4 * icon_scale;
        int lives_w = game->ship.lives * ship_w;
        int lx = W - 16 - lives_w;
        draw_text_box(ren, lx, 16, lives_w, ship_h);
        for (int i = 0; i < game->ship.lives; i++) {
            float sx = lx + i * ship_w + 3 * icon_scale;
            float sy = 16 + ship_h / 2;
            /* Draw a small triangle pointing up */
            float nose_x = sx, nose_y = sy - 2 * icon_scale;
            float l_x = sx - 3 * icon_scale, l_y = sy + icon_scale;
            float r_x = sx + 3 * icon_scale, r_y = sy + icon_scale;
            SDL_Vertex verts[3] = {
                {{nose_x, nose_y}, {1.0f, 1.0f, 1.0f, 1.0f}, {0.0f, 0.0f}},
                {{l_x, l_y},       {1.0f, 1.0f, 1.0f, 1.0f}, {0.0f, 0.0f}},
                {{r_x, r_y},       {1.0f, 1.0f, 1.0f, 1.0f}, {0.0f, 0.0f}},
            };
            SDL_RenderGeometry(ren, NULL, verts, 3, NULL, 0);
        }
        
        /* Level + Score */
        int lscale = 8;
        /* Level number top-left */
        int level_num = game->level + 1;
        char level_str[8];
        SDL_snprintf(level_str, sizeof(level_str), "%d", level_num);
        int level_w = font_text_width(level_str, lscale);
        draw_text_box(ren, 16, 16, level_w, lscale * 7);
        font_draw(ren, 16, 16, level_str, lscale, color_gold());
        
        /* Score centered */
        char score_str[16];
        int score_scale = 10;
        SDL_snprintf(score_str, sizeof(score_str), "%d", game->ship.score);
        /* Pad score to always be 6 digits */
        int pad = 6;
        if (game->ship.score < pad) {
            SDL_snprintf(score_str, sizeof(score_str), "%0*d", pad, game->ship.score);
        }
        int score_w = font_text_width(score_str, score_scale);
        int score_h = score_scale * 7;
        draw_text_box(ren, W / 2 - score_w / 2, 16, score_w, score_h);
        font_draw(ren, W / 2 - score_w / 2, 16, score_str, score_scale, color_white());
        
        /* High score below */
        char hi_str[16];
        int hi_scale = 7;
        int pad2 = 6;
        SDL_snprintf(hi_str, sizeof(hi_str), "%0*d", pad2, game->high_score);
        int hi_w = font_text_width(hi_str, hi_scale);
        draw_text_box(ren, W / 2 - hi_w / 2, 40, hi_w, hi_scale * 7);
        font_draw(ren, W / 2 - hi_w / 2, 40, hi_str, hi_scale, (color){100, 100, 100, 255});
    }
    
    else if (game->state == GSTATE_TITLE) {
        int scale = 10;
        int title_w = font_text_width("ASTEROIDS", scale);
        int title_h = scale * 7;
        draw_text_box(ren, W/2 - title_w/2, H/2 - 70, title_w, title_h);
        font_draw(ren, W/2 - title_w/2, H/2 - 70, "ASTEROIDS", scale, color_white());
        
        char press_txt[] = "PRESS ANY KEY TO START";
        int subscale = 7;
        int pw = font_text_width(press_txt, subscale);
        int ph = subscale * 7;
        draw_text_box(ren, W/2 - pw/2, H/2 + 30, pw, ph);
        int blink = ((int)(SDL_GetTicks() / 500) % 2);
        if (blink) {
            font_draw(ren, W/2 - pw/2, H/2 + 30, press_txt, subscale, color_white());
        }
    }
    else if (game->state == GSTATE_GAME_OVER) {
        int scale = 14;
        int score_w = font_text_width("GAME OVER", scale);
        int score_h = scale * 7;
        draw_text_box(ren, W/2 - score_w/2, H/2 - 50, score_w, score_h);
        font_draw(ren, W/2 - score_w/2, H/2 - 50, "GAME OVER", scale, color_red());
        
        int subscale = 10;
        int txt_w = font_text_width("PRESS ENTER TO RESTART", subscale);
        int txt_h = subscale * 7;
        draw_text_box(ren, W/2 - txt_w/2, H/2 + 30, txt_w, txt_h);
        font_draw(ren, W/2 - txt_w/2, H/2 + 30, "PRESS ENTER TO RESTART", subscale, color_white());
    }
}

int ui_draw_number(SDL_Renderer *ren, int x, int y, int n, int scale, color c) {
    char buf[16];
    SDL_snprintf(buf, sizeof(buf), "%d", n);
    int w = 0;
    for (const char *p = buf; *p; p++) w += 6 * scale;
    int cx = x - w;
    for (const char *p = buf; *p; p++) {
        font_draw_char(ren, cx, y, *p - '0' + 32, scale, c);
        cx += 6 * scale;
    }
    return w;
}
