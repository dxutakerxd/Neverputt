/*
 * Copyright (C) 2003 Robert Kooima
 *
 * NEVERPUTT is  free software; you can redistribute  it and/or modify
 * it under the  terms of the GNU General  Public License as published
 * by the Free  Software Foundation; either version 2  of the License,
 * or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT  ANY  WARRANTY;  without   even  the  implied  warranty  of
 * MERCHANTABILITY or  FITNESS FOR A PARTICULAR PURPOSE.   See the GNU
 * General Public License for more details.
 */

#include <math.h>

#include "hud.h"
#include "geom.h"
#include "gui.h"
#include "vec3.h"
#include "game.h"
#include "hole.h"
#include "audio.h"
#include "course.h"
#include "config.h"
#include "video.h"
#include "haptic.h"
#include "ad.h"
#ifdef ENABLE_WALLET
#include "wallet.h"
#endif
#include "ball.h"
#include "mtrl.h"

#include "st_all.h"
#include "st_conf.h"

/*---------------------------------------------------------------------------*/

static char *number(int i)
{
    static char str[MAXSTR];

    sprintf(str, "%02d", i);

    return str;
}

static void score_card_content(int id)
{
    int jd, kd, ld;

    int p1 = (curr_party() >= 1) ? 1 : 0;
    int p2 = (curr_party() >= 2) ? 1 : 0;
    int p3 = (curr_party() >= 3) ? 1 : 0;
    int p4 = (curr_party() >= 4) ? 1 : 0;

    int i;
    int n = curr_count() - 1;
    int m = curr_count() / 2;

    if ((jd = gui_hstack(id)))
    {
        if ((kd = gui_varray(jd)))
        {
            if (p1) gui_label(kd, _("O"),      0, 0, 0);
            if (p1) gui_label(kd, hole_out(0), 0, gui_wht, gui_wht);
            if (p1) gui_label(kd, hole_out(1), 0, gui_red, gui_wht);
            if (p2) gui_label(kd, hole_out(2), 0, gui_grn, gui_wht);
            if (p3) gui_label(kd, hole_out(3), 0, gui_blu, gui_wht);
            if (p4) gui_label(kd, hole_out(4), 0, gui_yel, gui_wht);

            gui_set_rect(kd, GUI_RGT);
        }

        if ((kd = gui_harray(jd)))
        {
            for (i = m; i > 0; i--)
                if ((ld = gui_varray(kd)))
                {
                    if (p1) gui_label(ld, number(i), 0, 0, 0);
                    if (p1) gui_label(ld, hole_score(i, 0), 0, gui_wht, gui_wht);
                    if (p1) gui_label(ld, hole_score(i, 1), 0, gui_red, gui_wht);
                    if (p2) gui_label(ld, hole_score(i, 2), 0, gui_grn, gui_wht);
                    if (p3) gui_label(ld, hole_score(i, 3), 0, gui_blu, gui_wht);
                    if (p4) gui_label(ld, hole_score(i, 4), 0, gui_yel, gui_wht);
                }

            gui_set_rect(kd, GUI_LFT);
        }

        if ((kd = gui_vstack(jd)))
        {
            gui_space(kd);

            if ((ld = gui_varray(kd)))
            {
                if (p1) gui_label(ld, _("Par"), 0, gui_wht, gui_wht);
                if (p1) gui_label(ld, _("P1"),  0, gui_red, gui_wht);
                if (p2) gui_label(ld, _("P2"),  0, gui_grn, gui_wht);
                if (p3) gui_label(ld, _("P3"),  0, gui_blu, gui_wht);
                if (p4) gui_label(ld, _("P4"),  0, gui_yel, gui_wht);

                gui_set_rect(ld, GUI_ALL);
            }
        }
    }

    gui_space(id);

    if ((jd = gui_hstack(id)))
    {
        if ((kd = gui_varray(jd)))
        {
            if (p1) gui_label(kd, _("Tot"),    0, 0, 0);
            if (p1) gui_label(kd, hole_tot(0), 0, gui_wht, gui_wht);
            if (p1) gui_label(kd, hole_tot(1), 0, gui_red, gui_wht);
            if (p2) gui_label(kd, hole_tot(2), 0, gui_grn, gui_wht);
            if (p3) gui_label(kd, hole_tot(3), 0, gui_blu, gui_wht);
            if (p4) gui_label(kd, hole_tot(4), 0, gui_yel, gui_wht);

            gui_set_rect(kd, GUI_ALL);
        }

        if ((kd = gui_varray(jd)))
        {
            if (p1) gui_label(kd, _("I"),     0, 0, 0);
            if (p1) gui_label(kd, hole_in(0), 0, gui_wht, gui_wht);
            if (p1) gui_label(kd, hole_in(1), 0, gui_red, gui_wht);
            if (p2) gui_label(kd, hole_in(2), 0, gui_grn, gui_wht);
            if (p3) gui_label(kd, hole_in(3), 0, gui_blu, gui_wht);
            if (p4) gui_label(kd, hole_in(4), 0, gui_yel, gui_wht);

            gui_set_rect(kd, GUI_RGT);
        }

        if ((kd = gui_harray(jd)))
        {
            for (i = n; i > m; i--)
                if ((ld = gui_varray(kd)))
                {
                    if (p1) gui_label(ld, number(i), 0, 0, 0);
                    if (p1) gui_label(ld, hole_score(i, 0), 0, gui_wht, gui_wht);
                    if (p1) gui_label(ld, hole_score(i, 1), 0, gui_red, gui_wht);
                    if (p2) gui_label(ld, hole_score(i, 2), 0, gui_grn, gui_wht);
                    if (p3) gui_label(ld, hole_score(i, 3), 0, gui_blu, gui_wht);
                    if (p4) gui_label(ld, hole_score(i, 4), 0, gui_yel, gui_wht);
                }

            gui_set_rect(kd, GUI_LFT);
        }

        if ((kd = gui_vstack(jd)))
        {
            gui_space(kd);

            if ((ld = gui_varray(kd)))
            {
                if (p1) gui_label(ld, _("Par"), 0, gui_wht, gui_wht);
                if (p1) gui_label(ld, _("P1"),  0, gui_red, gui_wht);
                if (p2) gui_label(ld, _("P2"),  0, gui_grn, gui_wht);
                if (p3) gui_label(ld, _("P3"),  0, gui_blu, gui_wht);
                if (p4) gui_label(ld, _("P4"),  0, gui_yel, gui_wht);

                gui_set_rect(ld, GUI_ALL);
            }
        }
    }
}

static int score_card(const char  *title,
                      const GLubyte *c0,
                      const GLubyte *c1)
{
    int id;

    if ((id = gui_vstack(0)))
    {
        gui_label(id, title, GUI_MED, c0, c1);
        gui_space(id);

        score_card_content(id);

        gui_layout(id, 0, 0);
    }

    return id;
}

/*---------------------------------------------------------------------------*/

static int shared_stick_basic(int id, int a, float v, int bump)
{
    int jd;

    if ((jd = gui_stick(id, a, v, bump)))
        gui_pulse(jd, 1.2f);

    return jd;
}

static void shared_stick(int id, int a, float v, int bump)
{
    shared_stick_basic(id, a, v, bump);
}

/*---------------------------------------------------------------------------*/

#define TITLE_PLAY   1
#define TITLE_CONF   2
#define TITLE_EXIT   3
#define TITLE_HELP   4
#define TITLE_WALLET 5

static int title_action(int i)
{
    audio_play(AUD_MENU, 1.0f);

    switch (i)
    {
    case TITLE_PLAY: return goto_state(&st_course);
    case TITLE_CONF: return goto_state(&st_conf);
    case TITLE_HELP: return goto_state(&st_help);
#ifdef ENABLE_WALLET
    case TITLE_WALLET:
        if (wallet_state() >= 3 && wallet_state() <= 4)
        {
            /* Already connected — disconnect and reset ball config. */
            wallet_disconnect();
            config_set_d(CONFIG_WALLET_SEEKER, 0);
            config_set_s(CONFIG_BALL_FILE,
                         "ball/basic-ball/basic-ball");
            config_save();
            /* Reload ball and re-enter title to refresh button label. */
            ball_free();
            ball_init();
            return goto_state(&st_title);
        }
        wallet_connect();
        return goto_state(&st_wallet);
#endif
    case TITLE_EXIT: return 0;
    }
    return 1;
}

static int title_enter(struct state *st, struct state *prev)
{
    int id, jd, kd;

    /* Build the title GUI. */

    if ((id = gui_vstack(0)))
    {
        gui_label(id, "Neverputt", GUI_LRG, 0, 0);
        gui_space(id);

        if ((jd = gui_harray(id)))
        {
            gui_filler(jd);

            if ((kd = gui_varray(jd)))
            {
                gui_start(kd, gt_prefix("menu^Play"),    GUI_MED, TITLE_PLAY, 1);
                gui_state(kd, gt_prefix("menu^Options"), GUI_MED, TITLE_CONF, 0);
#ifdef ENABLE_WALLET
                if (wallet_state() >= 3 && wallet_state() <= 4)
                    gui_state(kd, _("Disconnect Wallet"), GUI_MED, TITLE_WALLET, 0);
                else
                    gui_state(kd, _("Connect Wallet"),    GUI_MED, TITLE_WALLET, 0);
#endif
#if defined(__MOBILE__) || defined (__APPLE__)
                gui_state(kd, gt_prefix("menu^Help"),    GUI_MED, TITLE_HELP, 0);
#endif
                gui_state(kd, gt_prefix("menu^Quit"),    GUI_MED, TITLE_EXIT, 0);
            }

            gui_filler(jd);
        }
        gui_layout(id, 0, 0);
    }

    course_init();
    course_rand();

    return id;
}

static void title_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);

    if (next == &st_conf)
    {
        /*
         * This is ugly, but better than stupidly deleting stuff using
         * object names from a previous GL context.
         */
        course_free();
    }
}

static void title_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void title_timer(int id, float dt)
{
    float g[3] = { 0.f, 0.f, 0.f };

    game_step(g, dt);
    game_set_fly(fcosf(time_state() / 10.f));

    gui_timer(id, dt);
}

static void title_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int title_click(int b, int d)
{
    return gui_click(b, d) ? title_action(gui_token(gui_active())) : 1;
}

static int title_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return title_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return title_action(TITLE_EXIT);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int name_id;
static int desc_id;
static int shot_id;

#define COURSE_BACK -1

static int course_action(int i)
{
    audio_play(AUD_MENU, 1.0f);

    if (course_exists(i))
    {
        course_goto(i);
        goto_state(&st_party);
    }
    if (i == COURSE_BACK)
        goto_state(&st_title);

    return 1;
}

static int comp_size(int n, int s)
{
    return n <= s * s ? s : comp_size(n, s + 1);
}

static int comp_cols(int n)
{
    return comp_size(n, 1);
}

static int comp_rows(int n)
{
    int s = comp_size(n, 1);

    return n <= s * (s - 1) ? s - 1 : s;
}

static int course_enter(struct state *st, struct state *prev)
{
    int w = video.device_w;
    int h = video.device_h;

    int id, jd, kd, ld, md;

    int i, j, r, c, n;

    n = course_count();

    r = comp_rows(n);
    c = comp_cols(n);

    if ((id = gui_vstack(0)))
    {
        gui_label(id, _("Select Course"), GUI_MED, 0, 0);
        gui_space(id);

        /* Portrait: stack shot and grid vertically. */

        shot_id = gui_image(id, course_shot(0), w / 2, h / 5);

        gui_space(id);

        if ((kd = gui_varray(id)))
        {
            for(i = 0; i < r; i++)
            {
                if ((ld = gui_harray(kd)))
                {
                    for (j = c - 1; j >= 0; j--)
                    {
                        int k = i * c + j;

                        if (k < n)
                        {
                            md = gui_image(ld, course_shot(k),
                                           w / 2 / c, h / 6 / r);
                            gui_set_state(md, k, 0);

                            if (k == 0)
                                gui_focus(md);
                        }
                        else
                            gui_space(ld);
                    }
                }
            }
        }

        gui_space(id);
        name_id = gui_label(id, _(course_name(0)), GUI_SML, gui_yel, gui_wht);
        desc_id = gui_multi(id, _(course_desc(0)), GUI_SML, gui_yel, gui_wht);
        gui_space(id);

        if ((jd = gui_hstack(id)))
        {
            gui_filler(jd);
            gui_state(jd, _("Back"), GUI_SML, COURSE_BACK, 0);
        }

        gui_layout(id, 0, 0);
    }

    audio_music_fade_to(0.5f, "bgm/inter.ogg");

    return id;
}

static void course_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
}

static void course_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void course_timer(int id, float dt)
{
    gui_timer(id, dt);
}

static void course_point(int id, int x, int y, int dx, int dy)
{
    int jd;

    if ((jd = gui_point(id, x, y)))
    {
        int i = gui_token(jd);

        if (course_exists(i))
        {
            gui_set_image(shot_id, course_shot(i));
            gui_set_label(name_id, _(course_name(i)));
            gui_set_multi(desc_id, _(course_desc(i)));
        }
        gui_pulse(jd, 1.2f);
    }
}

static void course_stick(int id, int a, float v, int bump)
{
    int jd;

    if ((jd = shared_stick_basic(id, a, v, bump)))
    {
        int i = gui_token(jd);

        if (course_exists(i))
        {
            gui_set_image(shot_id, course_shot(i));
            gui_set_label(name_id, _(course_name(i)));
            gui_set_multi(desc_id, _(course_desc(i)));
        }
        gui_pulse(jd, 1.2f);
    }
}

static int course_click(int b, int d)
{
    return gui_click(b, d) ? course_action(gui_token(gui_active())) : 1;
}

static int course_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return course_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return course_action(COURSE_BACK);
    }
    return 1;
}

/* -------------------------------------------------------------------------- */

static int help_action(int tok)
{
    audio_play(AUD_MENU, 1.0f);

    switch (tok)
    {
        case GUI_BACK:
            return goto_state(&st_title);
    }
    return 1;
}

static int help_enter(struct state *st, struct state *prev)
{
    int id;

    if ((id = gui_vstack(0)))
    {
        gui_label(id, _("Privacy Policy"), GUI_MED, 0, 0);
        gui_multi(id,
            "MiniPutt Mobile does not\\"
            "collect, store, or transmit\\"
            "any personal data.",
            GUI_SML, gui_yel, gui_wht);
        gui_space(id);

        gui_label(id, _("License"), GUI_MED, 0, 0);
        gui_multi(id,
            "Based on Neverputt by\\"
            "Robert Kooima and contributors.\\"
            "Android port by Dmitry Rodin.\\"
            "Licensed under the GNU\\"
            "General Public License v3.\\"
            "Source code is available at\\"
            "github.com/Neverball/neverball",
            GUI_SML, gui_yel, gui_wht);
        gui_space(id);

        gui_state(id, _("Back"), GUI_SML, GUI_BACK, 0);

        gui_layout(id, 0, 0);
    }

    return id;
}

static void help_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
}

static void help_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void help_timer(int id, float dt)
{
    gui_timer(id, dt);
}

static void help_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int help_click(int b, int d)
{
    return gui_click(b, d) ? help_action(gui_token(gui_active())) : 1;
}

static int help_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return help_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return help_action(GUI_BACK);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

#define PARTY_T 0
#define PARTY_1 1
#define PARTY_2 2
#define PARTY_3 3
#define PARTY_4 4
#define PARTY_B 5

static int selected_party = 1;

static int party_action(int i)
{
    switch (i)
    {
    case PARTY_1:
        audio_play(AUD_MENU, 1.f);
        selected_party = 1;
        goto_state(&st_length);
        break;
    case PARTY_2:
        audio_play(AUD_MENU, 1.f);
        selected_party = 2;
        goto_state(&st_length);
        break;
    case PARTY_3:
        audio_play(AUD_MENU, 1.f);
        selected_party = 3;
        goto_state(&st_length);
        break;
    case PARTY_4:
        audio_play(AUD_MENU, 1.f);
        selected_party = 4;
        goto_state(&st_length);
        break;
    case PARTY_B:
        audio_play(AUD_MENU, 1.f);
        goto_state(&st_course);
        break;
    }
    return 1;
}

static int party_enter(struct state *st, struct state *prev)
{
    int id, jd;

    if ((id = gui_vstack(0)))
    {
        gui_label(id, _("Players?"), GUI_MED, 0, 0);
        gui_space(id);

        if ((jd = gui_harray(id)))
        {
            int p4 = gui_state(jd, "4", GUI_LRG, PARTY_4, 0);
            int p3 = gui_state(jd, "3", GUI_LRG, PARTY_3, 0);
            int p2 = gui_state(jd, "2", GUI_LRG, PARTY_2, 0);
            int p1 = gui_state(jd, "1", GUI_LRG, PARTY_1, 0);

            gui_set_color(p1, gui_red, gui_wht);
            gui_set_color(p2, gui_grn, gui_wht);
            gui_set_color(p3, gui_blu, gui_wht);
            gui_set_color(p4, gui_yel, gui_wht);

            gui_focus(p1);
        }

        gui_space(id);

        if ((jd = gui_hstack(id)))
        {
            gui_filler(jd);
            gui_state(jd, _("Back"), GUI_SML, PARTY_B, 0);
        }

        gui_layout(id, 0, 0);
    }

    return id;
}

static void party_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
}

static void party_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void party_timer(int id, float dt)
{
    gui_timer(id, dt);
}

static void party_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int party_click(int b, int d)
{
    return gui_click(b, d) ? party_action(gui_token(gui_active())) : 1;
}

static int party_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return party_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return party_action(PARTY_B);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

#define LENGTH_FRONT 1
#define LENGTH_BACK  2
#define LENGTH_ALL   3
#define LENGTH_B     4

static int length_action(int i)
{
    int n = curr_count() - 1;  /* total playable holes */
    int m = curr_count() / 2;  /* front half size      */

    audio_play(AUD_MENU, 1.0f);

    switch (i)
    {
    case LENGTH_FRONT:
        hole_set_range(1, m);
        if (hole_goto(1, selected_party))
            goto_state(&st_next);
        break;
    case LENGTH_BACK:
        hole_set_range(m + 1, n);
        if (hole_goto(m + 1, selected_party))
            goto_state(&st_next);
        break;
    case LENGTH_ALL:
        hole_set_range(1, 0);
        if (hole_goto(1, selected_party))
            goto_state(&st_next);
        break;
    case LENGTH_B:
        goto_state(&st_party);
        break;
    }
    return 1;
}

static int length_enter(struct state *st, struct state *prev)
{
    int id, jd, kd;

    int n = curr_count() - 1;  /* total playable holes */
    int m = curr_count() / 2;  /* front half size      */

    char front_lbl[32];
    char back_lbl[32];
    char all_lbl[32];

    sprintf(front_lbl, _("Front %d"), m);
    sprintf(back_lbl,  _("Back %d"),  n - m);
    sprintf(all_lbl,   _("All %d"),   n);

    if ((id = gui_vstack(0)))
    {
        gui_label(id, _("How Many Holes?"), GUI_MED, 0, 0);
        gui_space(id);

        if ((jd = gui_hstack(id)))
        {
            gui_filler(jd);

            if ((kd = gui_varray(jd)))
            {
                gui_start(kd, front_lbl, GUI_MED, LENGTH_FRONT, 1);
                gui_state(kd, back_lbl,  GUI_MED, LENGTH_BACK,  0);
                gui_state(kd, all_lbl,   GUI_MED, LENGTH_ALL,   0);
            }

            gui_filler(jd);
        }

        gui_space(id);

        if ((jd = gui_hstack(id)))
        {
            gui_filler(jd);
            gui_state(jd, _("Back"), GUI_SML, LENGTH_B, 0);
        }

        gui_layout(id, 0, 0);
    }

    return id;
}

static void length_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
}

static void length_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void length_timer(int id, float dt)
{
    gui_timer(id, dt);
}

static void length_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int length_click(int b, int d)
{
    return gui_click(b, d) ? length_action(gui_token(gui_active())) : 1;
}

static int length_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return length_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return length_action(LENGTH_B);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int paused = 0;

static struct state *st_continue;
static struct state *st_quit;

#define PAUSE_CONTINUE 1
#define PAUSE_QUIT     2

int goto_pause(struct state *s)
{
    if (curr_state() == &st_pause)
        return 1;

    st_continue = curr_state();
    st_quit = s;
    paused = 1;

    return goto_state(&st_pause);
}

void putt_context_restore(void)
{
    struct state *s = curr_state();

    /* Leave the current state (frees its GUI widgets and HUD). */

    if (s && s->leave)
        s->leave(s, s, s->gui_id);

    /* Free all GL resources (order matches st_null + extras). */

    gui_free();
    geom_free();
    ball_free();
    shad_free();
    game_free_draw();
    back_free();
    mtrl_free_objects();

    /* Re-initialize GL state for the new context. */

    video_gl_init();

    /* Reload all GL resources (reverse order). */

    mtrl_load_objects();
    shad_init();
    ball_init();
    geom_init();
    gui_init();
    game_load_draw();
    back_reload();

    /* Re-enter the current state to rebuild its GUI. */

    paused = 1;
    if (s && s->enter)
        s->gui_id = s->enter(s, s);
}

static int pause_action(int i)
{
    audio_play(AUD_MENU, 1.0f);

    switch(i)
    {
    case PAUSE_CONTINUE:
        return goto_state(st_continue ? st_continue : &st_title);

    case PAUSE_QUIT:
        return goto_state(st_quit);
    }
    return 1;
}

static int pause_enter(struct state *st, struct state *prev)
{
    int id, jd, td;

    audio_music_fade_out(0.2f);

    if ((id = gui_vstack(0)))
    {
        td = gui_label(id, _("Paused"), GUI_LRG, 0, 0);
        gui_space(id);

        if ((jd = gui_harray(id)))
        {
            gui_state(jd, _("Quit"), GUI_SML, PAUSE_QUIT, 0);
            gui_start(jd, _("Continue"), GUI_SML, PAUSE_CONTINUE, 1);
        }

        gui_pulse(td, 1.2f);
        gui_layout(id, 0, 0);
    }

    hud_init();
    return id;
}

static void pause_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
    hud_free();
    audio_music_fade_in(0.5f);
}

static void pause_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
    hud_paint();
}

static void pause_timer(int id, float dt)
{
    gui_timer(id, dt);
}

static void pause_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int pause_click(int b, int d)
{
    return gui_click(b, d) ? pause_action(gui_token(gui_active())) : 1;
}

static int pause_keybd(int c, int d)
{
    if (d && c == KEY_EXIT)
        return pause_action(PAUSE_CONTINUE);
    return 1;
}

static int pause_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return pause_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b) ||
            config_tst_d(CONFIG_JOYSTICK_BUTTON_START, b))
            return pause_action(PAUSE_CONTINUE);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int shared_keybd(int c, int d)
{
    if (d)
    {
        if (c == KEY_EXIT)
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int num = 0;
static int last_ad_hole = 0;
static int next_ad_active = 0;

static int next_enter(struct state *st, struct state *prev)
{
    int id, jd;
    char str[MAXSTR];

    sprintf(str, _("Hole %02d"), curr_hole());

    if ((id = gui_vstack(0)))
    {
        gui_label(id, str, GUI_MED, 0, 0);
        gui_space(id);

        if ((jd = gui_vstack(id)))
        {
            gui_label(jd, _("Player"), GUI_SML, 0, 0);

            switch (curr_player())
            {
            case 1:
                gui_label(jd, "1", GUI_LRG, gui_red, gui_wht);
                if (curr_party() > 1) audio_play(AUD_PLAYER1, 1.f);
                break;
            case 2:
                gui_label(jd, "2", GUI_LRG, gui_grn, gui_wht);
                if (curr_party() > 1) audio_play(AUD_PLAYER2, 1.f);
                break;
            case 3:
                gui_label(jd, "3", GUI_LRG, gui_blu, gui_wht);
                if (curr_party() > 1) audio_play(AUD_PLAYER3, 1.f);
                break;
            case 4:
                gui_label(jd, "4", GUI_LRG, gui_yel, gui_wht);
                if (curr_party() > 1) audio_play(AUD_PLAYER4, 1.f);
                break;
            }

            gui_set_rect(jd, GUI_ALL);
        }
        gui_layout(id, 0, 0);
    }

    hud_init();
    game_set_fly(1.f);

    if (paused)
        paused = 0;

    /* Show interstitial ad once per hole, every CONFIG_AD_INTERVAL holes. */
    next_ad_active = 0;
    {
        int h = curr_hole();
        int interval = config_get_d(CONFIG_AD_INTERVAL);
        if (h > 1 && h != last_ad_hole && interval > 0 && ((h - 1) % interval == 0))
        {
            last_ad_hole = h;
            next_ad_active = 1;
            ad_interstitial_reset();
            SDL_PauseAudio(1);
            ad_show_interstitial();
        }
    }

    return id;
}

static void next_leave(struct state *st, struct state *next, int id)
{
    if (next_ad_active)
    {
        next_ad_active = 0;
        ad_interstitial_reset();
        SDL_PauseAudio(0);
    }
    hud_free();
    gui_delete(id);
}

static void next_paint(int id, float t)
{
    game_draw(0, t);
    hud_paint();
    gui_paint(id);
}

static void next_timer(int id, float dt)
{
    if (next_ad_active)
    {
        if (ad_interstitial_state() == 2)
        {
            next_ad_active = 0;
            ad_interstitial_reset();
            SDL_PauseAudio(0);
        }
        return;
    }
    gui_timer(id, dt);
}

static void next_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int next_click(int b, int d)
{
    if (next_ad_active) return 1;
    return (d && b == SDL_BUTTON_LEFT) ? goto_state(&st_flyby) : 1;
}

static int next_keybd(int c, int d)
{
    if (next_ad_active) return 1;
    if (d)
    {
        if (c == KEY_POSE)
            return goto_state(&st_poser);
        if (c == KEY_EXIT)
            return goto_pause(&st_over);
        if ('0' <= c && c <= '9')
            num = num * 10 + c - '0';
    }
    return 1;
}

static int next_buttn(int b, int d)
{
    if (next_ad_active) return 1;
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
        {
            if (num > 0)
            {
                if (hole_goto(num, -1))
                {
                    num = 0;
                    return goto_state(&st_next);
                }
                else
                {
                    num = 0;
                    return 1;
                }
            }
            return goto_state(&st_flyby);
        }
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int poser_enter(struct state *st, struct state *prev)
{
    game_set_fly(-1.f);
    return 0;
}

static void poser_paint(int id, float t)
{
    game_draw(1, t);
}

static int poser_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return goto_state(&st_next);
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return goto_state(&st_next);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int flyby_enter(struct state *st, struct state *prev)
{
    video_hide_cursor();

    if (paused)
        paused = 0;
    else
        hud_init();

    return 0;
}

static void flyby_leave(struct state *st, struct state *next, int id)
{
    video_show_cursor();
    hud_free();
}

static void flyby_paint(int id, float t)
{
    game_draw(0, t);
    hud_paint();
}

static void flyby_timer(int id, float dt)
{
    float t = time_state();

    if (dt > 0.f && t > 1.f)
        goto_state(&st_stroke);
    else
        game_set_fly(1.f - t);

    gui_timer(id, dt);
}

static int flyby_click(int b, int d)
{
    if (d && b == SDL_BUTTON_LEFT)
    {
        game_set_fly(0.f);
        return goto_state(&st_stroke);
    }
    return 1;
}

static int flyby_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
        {
            game_set_fly(0.f);
            return goto_state(&st_stroke);
        }
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b) ||
            config_tst_d(CONFIG_JOYSTICK_BUTTON_START, b))
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int stroke_rotate = 0;
static int stroke_rotate_alt = 0;
static int stroke_mag = 0;

static int stroke_enter(struct state *st, struct state *prev)
{
    int id = 0;

#ifdef __MOBILE__
    hud_mobile_init();
#endif
    hud_init();
    game_clr_mag();
    config_set_d(CONFIG_CAMERA, 2);
    video_set_grab(1);

    if (paused)
        paused = 0;

    return id;
}

static void stroke_leave(struct state *st, struct state *next, int id)
{
#ifdef __MOBILE__
    hud_mobile_free();
#endif
    hud_free();
    video_clr_grab();
    config_set_d(CONFIG_CAMERA, 0);
    stroke_rotate = 0.0f;
    stroke_mag = 0.0f;
}

static void stroke_paint(int id, float t)
{
    game_draw(0, t);
#ifdef __MOBILE__
    hud_mobile_paint();
#endif
    hud_paint();
}

static void stroke_timer(int id, float dt)
{
    float g[3] = { 0.f, 0.f, 0.f };

    float k;

    if (SDL_GetModState() & KMOD_SHIFT || stroke_rotate_alt)
        k = 0.25;
    else
        k = 1.0;

    game_set_rot(stroke_rotate * k);
    game_set_mag(stroke_mag * k);

    game_update_view(dt);
    game_step(g, dt);
}

static void stroke_point(int id, int x, int y, int dx, int dy)
{
#ifdef __MOBILE__
    hud_mobile_point(x, y);
#endif
    game_set_rot(dx);
    game_set_mag(dy);
}

static void stroke_stick(int id, int a, float v, int bump)
{
#ifdef __MOBILE__
    if (SDL_NumJoysticks() < 2)
        return;
#endif
    if      (config_tst_d(CONFIG_JOYSTICK_AXIS_X0, a))
        stroke_rotate = 6 * v;
    else if (config_tst_d(CONFIG_JOYSTICK_AXIS_Y0, a))
        stroke_mag = -6 * v;
}

static int stroke_click(int b, int d)
{
#ifdef __MOBILE__
    b = hud_mobile_click();
    if (d && b == SDL_BUTTON_RIGHT)
        return goto_pause(&st_over);
#endif
    return (d && b == SDL_BUTTON_LEFT) ? goto_state(&st_roll) : 1;
}

static int stroke_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_X, b))
            stroke_rotate_alt = 1;
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return goto_state(&st_roll);
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_START, b))
            return goto_pause(&st_over);
    }
    else
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_X, b))
            stroke_rotate_alt = 0;
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int roll_enter(struct state *st, struct state *prev)
{
    video_hide_cursor();
    hud_init();

    if (paused)
        paused = 0;
    else
    {
        game_putt();
        haptic_putt();
    }

    return 0;
}

static void roll_leave(struct state *st, struct state *next, int id)
{
    video_show_cursor();
    hud_free();
}

static void roll_paint(int id, float t)
{
    game_draw(0, t);
    hud_paint();
}

static void roll_timer(int id, float dt)
{
    float g[3] = { 0.0f, -9.8f, 0.0f };

    switch (game_step(g, dt))
    {
    case GAME_STOP: goto_state(&st_stop); break;
    case GAME_GOAL: goto_state(&st_goal); break;
    case GAME_FALL: goto_state(&st_fall); break;
    }
}

static int roll_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b) ||
            config_tst_d(CONFIG_JOYSTICK_BUTTON_START, b))
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int goal_enter(struct state *st, struct state *prev)
{
    int id;

    if ((id = gui_label(0, _("It's In!"), GUI_MED, gui_grn, gui_grn)))
        gui_layout(id, 0, 0);

    if (paused)
        paused = 0;
    else
        hole_goal();

    hud_init();

    return id;
}

static void goal_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
    hud_free();
}

static void goal_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
    hud_paint();
}

static void goal_timer(int id, float dt)
{
    if (time_state() > 3)
    {
        if (hole_next())
            goto_state(&st_next);
        else
            goto_state(&st_score);
    }
}

static int goal_click(int b, int d)
{
    if (b == SDL_BUTTON_LEFT && d == 1)
    {
        if (hole_next())
            goto_state(&st_next);
        else
            goto_state(&st_score);
    }
    return 1;
}

static int goal_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
        {
            if (hole_next())
                goto_state(&st_next);
            else
                goto_state(&st_score);
        }
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int stop_enter(struct state *st, struct state *prev)
{
    if (paused)
        paused = 0;
    else
        hole_stop();

    hud_init();

    return 0;
}

static void stop_leave(struct state *st, struct state *next, int id)
{
    hud_free();
}

static void stop_paint(int id, float t)
{
    game_draw(0, t);
    hud_paint();
}

static void stop_timer(int id, float dt)
{
    float g[3] = { 0.f, 0.f, 0.f };

    game_update_view(dt);
    game_step(g, dt);

    if (time_state() > 1)
    {
        if (hole_next())
            goto_state(&st_next);
        else
            goto_state(&st_score);
    }
}

static int stop_click(int b, int d)
{
    if (b == SDL_BUTTON_LEFT && d == 1)
    {
        if (hole_next())
            goto_state(&st_next);
        else
            goto_state(&st_score);
    }
    return 1;
}

static int stop_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
        {
            if (hole_next())
                goto_state(&st_next);
            else
                goto_state(&st_score);
        }
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b) ||
            config_tst_d(CONFIG_JOYSTICK_BUTTON_START, b))
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int fall_ad_offered = 0;
static int fall_ad_active  = 0;

static int   fall_hold_active = 0;   /* is finger currently held down? */
static float fall_hold_time   = 0.f; /* accumulated hold duration       */
static int   fall_mulligan_id;       /* gui label id for hold feedback  */

#define MULLIGAN_HOLD_SEC 2.0f

static int fall_enter(struct state *st, struct state *prev)
{
    int id;

    fall_ad_offered = 0;
    fall_ad_active  = 0;
    fall_hold_active = 0;
    fall_hold_time   = 0.f;

    if (paused)
    {
        paused = 0;
        if ((id = gui_label(0, _("1 Stroke Penalty"), GUI_MED, gui_blk, gui_red)))
            gui_layout(id, 0, 0);
    }
    else
    {
        hole_fall();

        if (!config_get_d(CONFIG_AD_FREE))
        {
            if ((id = gui_vstack(0)))
            {
                gui_label(id, _("1 Stroke Penalty"), GUI_MED, gui_blk, gui_red);
                gui_space(id);
                fall_mulligan_id = gui_label(id, _("Hold for Mulligan!"), GUI_SML, gui_grn, gui_wht);
                gui_layout(id, 0, 0);
            }
            fall_ad_offered = 1;
        }
        else
        {
            if ((id = gui_label(0, _("1 Stroke Penalty"), GUI_MED, gui_blk, gui_red)))
                gui_layout(id, 0, 0);
        }
    }

    hud_init();
    return id;
}

static void fall_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
    hud_free();
}

static void fall_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
    hud_paint();
}

static void fall_timer(int id, float dt)
{
    if (fall_hold_active && fall_ad_offered && !fall_ad_active)
    {
        char buf[32];
        float remaining;

        fall_hold_time += dt;

        remaining = MULLIGAN_HOLD_SEC - fall_hold_time;
        sprintf(buf, "Hold... %d", (int)ceilf(remaining));
        gui_set_label(fall_mulligan_id, buf);

        if (fall_hold_time >= MULLIGAN_HOLD_SEC)
        {
            fall_hold_active = 0;
            fall_ad_active   = 1;
            ad_rewarded_reset();
            ad_show_rewarded();
            gui_set_label(fall_mulligan_id, _("Mulligan!"));
        }
    }

    if (fall_ad_active)
    {
        int state = ad_rewarded_state();
        if (state == 2) /* complete — mulligan earned */
        {
            fall_ad_active  = 0;
            fall_ad_offered = 0;
            hole_fall_undo();
            ad_rewarded_reset();
            if (hole_next())
                goto_state(&st_next);
            else
                goto_state(&st_score);
            return;
        }
        else if (state == 3) /* dismissed without completing */
        {
            fall_ad_active  = 0;
            fall_ad_offered = 0;
            ad_rewarded_reset();
        }
    }

    if (!fall_ad_active && time_state() > 3)
    {
        if (hole_next())
            goto_state(&st_next);
        else
            goto_state(&st_score);
    }
}

static int fall_click(int b, int d)
{
    if (b == SDL_BUTTON_LEFT)
    {
        if (d == 1) /* press */
        {
            if (fall_ad_offered && !fall_ad_active)
            {
                fall_hold_active = 1;
                fall_hold_time   = 0.f;
                return 1;
            }
        }
        else /* release */
        {
            if (fall_hold_active)
            {
                fall_hold_active = 0;
                fall_hold_time   = 0.f;
                gui_set_label(fall_mulligan_id, _("Hold for Mulligan!"));
                return 1;
            }

            if (!fall_ad_active)
            {
                if (hole_next())
                    goto_state(&st_next);
                else
                    goto_state(&st_score);
            }
        }
    }
    return 1;
}

static int fall_buttn(int b, int d)
{
    if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
    {
        if (d) /* press */
        {
            if (fall_ad_offered && !fall_ad_active)
            {
                fall_hold_active = 1;
                fall_hold_time   = 0.f;
                return 1;
            }
        }
        else /* release */
        {
            if (fall_hold_active)
            {
                fall_hold_active = 0;
                fall_hold_time   = 0.f;
                gui_set_label(fall_mulligan_id, _("Hold for Mulligan!"));
                return 1;
            }

            if (!fall_ad_active)
            {
                if (hole_next())
                    goto_state(&st_next);
                else
                    goto_state(&st_score);
            }
        }
    }
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return goto_pause(&st_over);
    }
    return 1;
}

static int fall_keybd(int c, int d)
{
    if (d && c == KEY_EXIT)
    {
        if (fall_ad_active)
        {
            ad_dismiss();
            fall_ad_active  = 0;
            fall_ad_offered = 0;
            ad_rewarded_reset();
        }
        return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

static int score_enter(struct state *st, struct state *prev)
{
    audio_music_fade_out(2.f);

    if (paused)
        paused = 0;

    return score_card(_("Scores"), gui_yel, gui_red);
}

static void score_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);
}

static void score_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void score_timer(int id, float dt)
{
    gui_timer(id, dt);
}

static int score_click(int b, int d)
{
    if (b == SDL_BUTTON_LEFT && d == 1)
    {
        if (hole_move())
            return goto_state(&st_next);
        else
            return goto_state(&st_over);
    }
    return 1;
}

static int score_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
        {
            if (hole_move())
                goto_state(&st_next);
            else
                goto_state(&st_over);
        }
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return goto_pause(&st_over);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

#define OVER_MENU 1

static int over_ad_active = 0;

static int over_action(int i)
{
    audio_play(AUD_MENU, 1.0f);

    switch (i)
    {
    case OVER_MENU:
        return goto_state(&st_title);
    }
    return 1;
}

static int over_enter(struct state *st, struct state *prev)
{
    int id, jd;

    audio_music_stop();
    over_ad_active = 0;
    if (!paused && !config_get_d(CONFIG_AD_FREE))
    {
        over_ad_active = 1;
        ad_interstitial_reset();
        SDL_PauseAudio(1);
        ad_show_interstitial();
    }
    if (paused)
        paused = 0;

    if ((id = gui_vstack(0)))
    {
        gui_label(id, _("Final Scores"), GUI_MED, gui_yel, gui_red);

        gui_space(id);

        if ((jd = gui_harray(id)))
        {
            gui_start(jd, _("Main Menu"), GUI_SML, OVER_MENU, 1);
        }

        gui_space(id);

        score_card_content(id);

        gui_layout(id, 0, 0);
    }

    return id;
}

static void over_leave(struct state *st, struct state *next, int id)
{
    if (over_ad_active)
    {
        over_ad_active = 0;
        ad_interstitial_reset();
        SDL_PauseAudio(0);
    }
    gui_delete(id);
}

static void over_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void over_timer(int id, float dt)
{
    if (over_ad_active)
    {
        if (ad_interstitial_state() == 2)
        {
            over_ad_active = 0;
            ad_interstitial_reset();
            SDL_PauseAudio(0);
        }
        return;
    }
    gui_timer(id, dt);
}

static int over_click(int b, int d)
{
    if (over_ad_active) return 1;
    return gui_click(b, d) ? over_action(gui_token(gui_active())) : 1;
}

static void over_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int over_buttn(int b, int d)
{
    if (over_ad_active) return 1;
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_A, b))
            return over_action(gui_token(gui_active()));
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
            return goto_state(&st_title);
    }
    return 1;
}

/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/

#ifdef ENABLE_WALLET

static int   wallet_gui;
static int   wallet_done;      /* non-zero once final state is handled */
static float wallet_done_t;    /* seconds since result was shown       */
static int   wallet_prev_ws;   /* previous wallet_state() value        */

static int wallet_enter(struct state *st, struct state *prev)
{
    int id;

    wallet_done    = 0;
    wallet_done_t  = 0.f;
    wallet_prev_ws = -1;

    if ((id = gui_vstack(0)))
    {
        wallet_gui = gui_label(id, _("Connecting..."), GUI_MED, 0, 0);
        gui_layout(id, 0, 0);
    }

    return id;
}

static void wallet_leave(struct state *st, struct state *next, int id)
{
    gui_delete(id);

    /* Reload ball if config changed (seeker verified or disconnected). */
    ball_free();
    ball_init();
}

static void wallet_paint(int id, float t)
{
    game_draw(0, t);
    gui_paint(id);
}

static void wallet_timer(int id, float dt)
{
    int ws = wallet_state();

    /* Once done, wait 2 seconds then return to title. */
    if (wallet_done)
    {
        wallet_done_t += dt;

        if (wallet_done_t > 2.f)
            goto_state(&st_title);

        gui_timer(id, dt);
        return;
    }

    /* Only update label on state transitions to avoid per-frame work. */
    if (ws != wallet_prev_ws)
    {
        wallet_prev_ws = ws;

        switch (ws)
        {
        case 0: /* Disconnected (cancel/back during connecting) */
            gui_set_label(wallet_gui, _("Cancelled"));
            wallet_done = 1;
            break;

        case 1:
            gui_set_label(wallet_gui, _("Connecting..."));
            break;

        case 2:
            gui_set_label(wallet_gui, _("Verifying Seeker..."));
            break;

        case 3: /* SGT verified — save config, reload ball when leaving */
            gui_set_label(wallet_gui, _("Seeker Verified!"));
            config_set_s(CONFIG_BALL_FILE,
                         "ball/solana-seeker/solana-seeker");
            config_set_d(CONFIG_WALLET_SEEKER, 1);
            config_save();
            wallet_done = 1;
            break;

        case 4: /* Connected but no SGT */
            gui_set_label(wallet_gui, _("Wallet Connected"));
            wallet_done = 1;
            break;

        case 5: /* Error / cancelled by user */
            gui_set_label(wallet_gui, _("Connection Failed"));
            wallet_done = 1;
            break;
        }
    }

    gui_timer(id, dt);
}

static void wallet_point(int id, int x, int y, int dx, int dy)
{
    gui_pulse(gui_point(id, x, y), 1.2f);
}

static int wallet_click(int b, int d)
{
    if (d && b == SDL_BUTTON_LEFT && wallet_done)
        return goto_state(&st_title);
    return 1;
}

static int wallet_keybd(int c, int d)
{
    if (d && c == KEY_EXIT)
    {
        wallet_disconnect();
        return goto_state(&st_title);
    }
    return 1;
}

static int wallet_buttn(int b, int d)
{
    if (d)
    {
        if (config_tst_d(CONFIG_JOYSTICK_BUTTON_B, b))
        {
            wallet_disconnect();
            return goto_state(&st_title);
        }
    }
    return 1;
}

#endif /* ENABLE_WALLET */

/*---------------------------------------------------------------------------*/

struct state st_title = {
    title_enter,
    title_leave,
    title_paint,
    title_timer,
    title_point,
    shared_stick,
    NULL,
    title_click,
    NULL,
    title_buttn
};

struct state st_course = {
    course_enter,
    course_leave,
    course_paint,
    course_timer,
    course_point,
    course_stick,
    NULL,
    course_click,
    NULL,
    course_buttn
};

struct state st_help = {
    help_enter,
    help_leave,
    help_paint,
    help_timer,
    help_point,
    shared_stick,
    NULL,
    help_click,
    NULL,
    help_buttn
};

struct state st_party = {
    party_enter,
    party_leave,
    party_paint,
    party_timer,
    party_point,
    shared_stick,
    NULL,
    party_click,
    NULL,
    party_buttn
};

struct state st_length = {
    length_enter,
    length_leave,
    length_paint,
    length_timer,
    length_point,
    shared_stick,
    NULL,
    length_click,
    NULL,
    length_buttn
};

struct state st_next = {
    next_enter,
    next_leave,
    next_paint,
    next_timer,
    next_point,
    shared_stick,
    NULL,
    next_click,
    next_keybd,
    next_buttn
};

struct state st_poser = {
    poser_enter,
    NULL,
    poser_paint,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    poser_buttn
};

struct state st_flyby = {
    flyby_enter,
    flyby_leave,
    flyby_paint,
    flyby_timer,
    NULL,
    NULL,
    NULL,
    flyby_click,
    shared_keybd,
    flyby_buttn
};

struct state st_stroke = {
    stroke_enter,
    stroke_leave,
    stroke_paint,
    stroke_timer,
    stroke_point,
    stroke_stick,
    NULL,
    stroke_click,
    shared_keybd,
    stroke_buttn
};

struct state st_roll = {
    roll_enter,
    roll_leave,
    roll_paint,
    roll_timer,
    NULL,
    NULL,
    NULL,
    NULL,
    shared_keybd,
    roll_buttn
};

struct state st_goal = {
    goal_enter,
    goal_leave,
    goal_paint,
    goal_timer,
    NULL,
    NULL,
    NULL,
    goal_click,
    shared_keybd,
    goal_buttn
};

struct state st_stop = {
    stop_enter,
    stop_leave,
    stop_paint,
    stop_timer,
    NULL,
    NULL,
    NULL,
    stop_click,
    shared_keybd,
    stop_buttn
};

struct state st_fall = {
    fall_enter,
    fall_leave,
    fall_paint,
    fall_timer,
    NULL,
    NULL,
    NULL,
    fall_click,
    fall_keybd,
    fall_buttn
};

struct state st_score = {
    score_enter,
    score_leave,
    score_paint,
    score_timer,
    NULL,
    NULL,
    NULL,
    score_click,
    shared_keybd,
    score_buttn
};

struct state st_over = {
    over_enter,
    over_leave,
    over_paint,
    over_timer,
    over_point,
    NULL,
    NULL,
    over_click,
    NULL,
    over_buttn
};

struct state st_pause = {
    pause_enter,
    pause_leave,
    pause_paint,
    pause_timer,
    pause_point,
    shared_stick,
    NULL,
    pause_click,
    pause_keybd,
    pause_buttn
};

#ifdef ENABLE_WALLET
struct state st_wallet = {
    wallet_enter,
    wallet_leave,
    wallet_paint,
    wallet_timer,
    wallet_point,
    shared_stick,
    NULL,
    wallet_click,
    wallet_keybd,
    wallet_buttn
};
#endif
