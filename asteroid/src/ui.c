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
        if (ch >= 32 && ch <= 126) total += scale * (5 + 1);
    }
    return total;
}

void font_draw_char(SDL_Renderer *ren, int x, int y, int ch_idx, int scale, color c) {
    if (ch_idx < 0 || ch_idx >= 95) return;
    const uint8_t *glyph = FONT_DATA[ch_idx];
    for (int row = 0; row < 7; row++) {
        uint8_t bits = glyph[row];
        for (int col = 0; col < 5; col++) {
            if (bits & (0x10 >> col)) {
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

void ui_draw_score_impl(SDL_Renderer *ren, int score, int x, int y) {
    char buf[16];
    SDL_snprintf(buf, sizeof(buf), "%d", score);
    int tw = 0;
    for (const char *p = buf; *p; p++) tw += 6 * 8;
    font_draw(ren, x - tw, y, buf, 8, color_white());
}

void ui_draw_score(SDL_Renderer *ren, Game *game) {
    if (!game->ship.alive) {
        ui_draw_score_impl(ren, game->ship.score, W - 16, 10);
    } else {
        ui_draw_score_impl(ren, game->ship.score, W / 2, 10);
    }
}

void ui_draw(SDL_Renderer *ren, Game *game) {
    if (game->state == GSTATE_PLAYING) {
        ui_draw_score(ren, game);
        
        /* Lives display - top left */
        font_draw(ren, 10, 10, "LIVES", 8, color_white());
        for (int i = 0; i < game->ship.lives; i++) {
            int ix = 10 + i * 32;
            SDL_FRect tris[4];
            tris[0] = (SDL_FRect){(float)ix + 12, (float)54, 6, 6};
            tris[1] = (SDL_FRect){(float)ix, (float)72, 6, 4};
            tris[2] = (SDL_FRect){(float)ix + 18, (float)72, 6, 4};
            tris[3] = (SDL_FRect){(float)ix + 6, (float)78, 12, 4};
            SDL_SetRenderDrawColor(ren, 255, 255, 255, 200);
            for (int t = 0; t < 4; t++)
                SDL_RenderFillRect(ren, &tris[t]);
        }
    }
    else if (game->state == GSTATE_TITLE) {
        int title_w = font_text_width("ASTEROIDS", 12);
        font_draw(ren, W/2 - title_w/2, H/2 - 60, "ASTEROIDS", 12, color_white());
        
        char press_txt[32] = "PRESS ANY KEY TO START";
        int blink = ((int)(SDL_GetTicks() / 500) % 2);
        if (blink) {
            font_draw(ren, W/2 - title_w/2, H/2 + 20, press_txt, 8, color_white());
        }
    }
    else if (game->state == GSTATE_GAME_OVER) {
        int score_w = font_text_width("GAME OVER", 12);
        font_draw(ren, W/2 - score_w/2, H/2 - 40, "GAME OVER", 12, color_white());
        font_draw(ren, W/2 - score_w/2, H/2 + 20, "PRESS ENTER TO RESTART", 8, color_white());
    }
}

int ui_draw_number(SDL_Renderer *ren, int x, int y, int n, int scale, color c) {
    char buf[16];
    SDL_snprintf(buf, sizeof(buf), "%d", n);
    int w = 0;
    for (const char *p = buf; *p; p++) w += 5 * scale;
    int cx = x - w;
    for (const char *p = buf; *p; p++) {
        font_draw_char(ren, cx, y, *p - '0' + 32, scale, c);
        cx += 5 * scale;
    }
    return w;
}
