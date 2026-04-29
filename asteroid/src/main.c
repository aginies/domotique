#include "game.h"
#include <stdlib.h>

int main(void) {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        SDL_Log("Could not initialize SDL: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    
    SDL_Window *win = SDL_CreateWindow("Asteroids", W, H, 0);
    if (!win) {
        SDL_Log("Could not create window: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    
    SDL_Renderer *ren = SDL_CreateRenderer(win, "gpu");
    if (!ren) {
        ren = SDL_CreateRenderer(win, "opengl");
    }
    if (!ren) {
        SDL_Log("Could not create renderer: %s", SDL_GetError());
        SDL_DestroyWindow(win);
        SDL_Quit();
        return 1;
    }
    
    SDL_ShowWindow(win);
    
    Game game;
    memset(&game, 0, sizeof(Game));
    game_init(&game);
    
    Uint32 last_time = SDL_GetTicks();
    
    while (!game.quit) {
        SDL_Event ev;
        while (SDL_PollEvent(&ev)) {
            handle_event(&game, &ev);
        }
        
        Uint32 now = SDL_GetTicks();
        float dt = (now - last_time) / 1000.0f;
        last_time = now;
        
        if (dt > 0.05f) dt = 0.05f;
        if (dt < 0.001f) dt = 0.001f;
        
        game_update(&game, dt);
        game_render(ren, &game);
        SDL_RenderPresent(ren);
    }
    
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
    
    return 0;
}
