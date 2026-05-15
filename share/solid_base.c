/*
 * Copyright (C) 2003 Robert Kooima
 *
 * NEVERBALL is  free software; you can redistribute  it and/or modify
 * it under the  terms of the GNU General  Public License as published
 * by the Free  Software Foundation; either version 2  of the License,
 * or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT  ANY  WARRANTY;  without   even  the  implied  warranty  of
 * MERCHANTABILITY or  FITNESS FOR A PARTICULAR PURPOSE.   See the GNU
 * General Public License for more details.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL.h>

#include "solid_base.h"
#include "base_config.h"
#include "binary.h"
#include "common.h"
#include "fs.h"
#include "vec3.h"

enum
{
    SOL_VERSION_1_5 = 6,
    SOL_VERSION_1_6 = 7,
    SOL_VERSION_DEV,
    SOL_VERSION_1_7 = 9
};

#define SOL_VERSION_MIN  SOL_VERSION_1_5
#define SOL_VERSION_CURR SOL_VERSION_1_7

#define SOL_MAGIC (0xAF | 'S' << 8 | 'O' << 16 | 'L' << 24)

/*---------------------------------------------------------------------------*/

static int sol_version;

static int sol_file(fs_file fin)
{
    int magic;
    int version;

    magic   = get_index(fin);
    version = get_index(fin);

    if (magic != SOL_MAGIC || (version < SOL_VERSION_MIN ||
                               version > SOL_VERSION_CURR))
        return 0;

    sol_version = version;

    return 1;
}

static void sol_load_mtrl(fs_file fin, struct b_mtrl *mp)
{
    get_array(fin, mp->d, 4);
    get_array(fin, mp->a, 4);
    get_array(fin, mp->s, 4);
    get_array(fin, mp->e, 4);
    get_array(fin, mp->h, 1);

    mp->fl = get_index(fin);

    fs_read(mp->f, 1, PATHMAX, fin);

    if (sol_version >= SOL_VERSION_1_6)
    {
        if (mp->fl & M_ALPHA_TEST)
        {
            mp->alpha_func = get_index(fin);
            mp->alpha_ref  = get_float(fin);
        }
    }

    /* Convert 1.5.4 material flags. */

    if (sol_version == SOL_VERSION_1_5)
    {
        static const int flags[][2] = {
            { 1, M_SHADOWED },
            { 2, M_TRANSPARENT },
            { 4, M_REFLECTIVE | M_SHADOWED },
            { 8, M_ENVIRONMENT },
            { 16, M_ADDITIVE },
            { 32, M_CLAMP_S | M_CLAMP_T },
            { 64, M_DECAL | M_SHADOWED },
            { 128, M_TWO_SIDED }
        };

        if (mp->fl)
        {
            int i, f;

            for (f = 0, i = 0; i < ARRAYSIZE(flags); i++)
                if (mp->fl & flags[i][0])
                    f |= flags[i][1];

            mp->fl = f;
        }
        else
        {
            /* Must be "mtrl/invisible". */

            mp->fl = M_TRANSPARENT;
            mp->d[3] = 0.0f;
        }
    }
}

static void sol_load_vert(fs_file fin, struct b_vert *vp)
{
    get_array(fin, vp->p, 3);
}

static void sol_load_edge(fs_file fin, struct b_edge *ep)
{
    ep->vi = get_index(fin);
    ep->vj = get_index(fin);
}

static void sol_load_side(fs_file fin, struct b_side *sp)
{
    get_array(fin, sp->n, 3);

    sp->d = get_float(fin);
}

static void sol_load_texc(fs_file fin, struct b_texc *tp)
{
    get_array(fin, tp->u, 2);
}

static void sol_load_offs(fs_file fin, struct b_offs *op)
{
    op->ti = get_index(fin);
    op->si = get_index(fin);
    op->vi = get_index(fin);
}

static void sol_load_geom(fs_file fin, struct b_geom *gp, struct s_base *fp)
{
    gp->mi = get_index(fin);

    if (sol_version >= SOL_VERSION_1_6)
    {
        gp->oi = get_index(fin);
        gp->oj = get_index(fin);
        gp->ok = get_index(fin);
    }
    else
    {
        struct b_offs ov[3];
        int i, j, iv[3], oc;
        void *p;

        oc = 0;

        for (i = 0; i < 3; i++)
        {
            ov[i].ti = get_index(fin);
            ov[i].si = get_index(fin);
            ov[i].vi = get_index(fin);

            iv[i] = -1;

            for (j = 0; j < fp->oc; j++)
                if (ov[i].ti == fp->ov[j].ti &&
                    ov[i].si == fp->ov[j].si &&
                    ov[i].vi == fp->ov[j].vi)
                {
                    iv[i] = j;
                    break;
                }

            if (j == fp->oc)
                oc++;
        }

        if (oc && (p = realloc(fp->ov, sizeof (struct b_offs) * (fp->oc + oc))))
        {
            fp->ov = p;

            for (i = 0; i < 3; i++)
                if (iv[i] < 0)
                {
                    fp->ov[fp->oc] = ov[i];
                    iv[i] = fp->oc++;
                }
        }

        gp->oi = iv[0];
        gp->oj = iv[1];
        gp->ok = iv[2];
    }
}

static void sol_load_lump(fs_file fin, struct b_lump *lp)
{
    lp->fl = get_index(fin);
    lp->v0 = get_index(fin);
    lp->vc = get_index(fin);
    lp->e0 = get_index(fin);
    lp->ec = get_index(fin);
    lp->g0 = get_index(fin);
    lp->gc = get_index(fin);
    lp->s0 = get_index(fin);
    lp->sc = get_index(fin);
}

static void sol_load_node(fs_file fin, struct b_node *np)
{
    np->si = get_index(fin);
    np->ni = get_index(fin);
    np->nj = get_index(fin);
    np->l0 = get_index(fin);
    np->lc = get_index(fin);
}

static void sol_load_path(fs_file fin, struct b_path *pp)
{
    get_array(fin, pp->p, 3);

    pp->t  = get_float(fin);
    pp->pi = get_index(fin);
    pp->f  = get_index(fin);
    pp->s  = get_index(fin);

    pp->tm = TIME_TO_MS(pp->t);
    pp->t  = MS_TO_TIME(pp->tm);

    if (sol_version >= SOL_VERSION_1_6)
        pp->fl = get_index(fin);

    pp->e[0] = 1.0f;
    pp->e[1] = 0.0f;
    pp->e[2] = 0.0f;
    pp->e[3] = 0.0f;

    if (pp->fl & P_ORIENTED)
        get_array(fin, pp->e, 4);
}

static void sol_load_body(fs_file fin, struct b_body *bp)
{
    bp->pi = get_index(fin);

    if (sol_version >= SOL_VERSION_1_6)
    {
        bp->pj = get_index(fin);

        if (bp->pj < 0)
            bp->pj = bp->pi;
    }
    else
        bp->pj = bp->pi;

    bp->ni = get_index(fin);
    bp->l0 = get_index(fin);
    bp->lc = get_index(fin);
    bp->g0 = get_index(fin);
    bp->gc = get_index(fin);
}

static void sol_load_item(fs_file fin, struct b_item *hp)
{
    get_array(fin, hp->p, 3);

    hp->t = get_index(fin);
    hp->n = get_index(fin);
}

static void sol_load_goal(fs_file fin, struct b_goal *zp)
{
    /* Skip per-goal garbage 0xFFFFFFFF sentinel values.                    */
    /* Same pattern as sol_load_jump/sol_load_swch — some pre-compiled SOL  */
    /* files have sentinel pairs before each goal entry.                    */

    long pos = fs_tell(fin);
    int  v0  = get_index(fin);
    int  v1  = get_index(fin);

    SDL_Log("sol_load_goal: pos=%ld peek v0=0x%08X v1=0x%08X %s",
            pos, (unsigned)v0, (unsigned)v1,
            (v0 == -1 && v1 == -1) ? "SKIPPING" : "KEEPING");

    if (v0 != -1 || v1 != -1)
        fs_seek(fin, pos, SEEK_SET);

    get_array(fin, zp->p, 3);

    zp->r = get_float(fin);

    SDL_Log("sol_load_goal: p=(%.2f,%.2f,%.2f) r=%.4f",
            zp->p[0], zp->p[1], zp->p[2], zp->r);
}

static void sol_load_swch(fs_file fin, struct b_swch *xp)
{
    /* Skip per-switch garbage 0xFFFFFFFF sentinel values.                  */
    /* Same pattern as sol_load_jump — some pre-compiled SOL files have     */
    /* sentinel pairs before each switch (and also at the jump/switch       */
    /* boundary when jc=0).                                                 */

    long pos = fs_tell(fin);
    int  v0  = get_index(fin);
    int  v1  = get_index(fin);

    SDL_Log("sol_load_swch: pos=%ld peek v0=0x%08X v1=0x%08X %s",
            pos, (unsigned)v0, (unsigned)v1,
            (v0 == -1 && v1 == -1) ? "SKIPPING" : "KEEPING");

    if (v0 != -1 || v1 != -1)
        fs_seek(fin, pos, SEEK_SET);

    get_array(fin, xp->p, 3);

    xp->r  = get_float(fin);
    xp->pi = get_index(fin);
    xp->t  = get_float(fin);
    (void)   get_float(fin);
    xp->f  = get_index(fin);
    (void)   get_index(fin);
    xp->i  = get_index(fin);

    /* Clamp state and invisible flags to valid boolean values.             */
    /* Some SOL files have garbage in these fields due to file corruption.  */

    if (xp->f != 0 && xp->f != 1)
        xp->f = 0;
    if (xp->i != 0 && xp->i != 1)
        xp->i = 0;

    xp->tm = TIME_TO_MS(xp->t);
    xp->t = MS_TO_TIME(xp->tm);

    SDL_Log("sol_load_swch: p=(%.2f,%.2f,%.2f) r=%.2f pi=%d t=%.2f f=%d i=%d",
            xp->p[0], xp->p[1], xp->p[2], xp->r, xp->pi, xp->t, xp->f, xp->i);
}

static void sol_load_bill(fs_file fin, struct b_bill *rp)
{
    rp->fl = get_index(fin);
    rp->mi = get_index(fin);
    rp->t  = get_float(fin);
    rp->d  = get_float(fin);

    get_array(fin, rp->w,  3);
    get_array(fin, rp->h,  3);
    get_array(fin, rp->rx, 3);
    get_array(fin, rp->ry, 3);
    get_array(fin, rp->rz, 3);
    get_array(fin, rp->p,  3);
}

static void sol_load_jump(fs_file fin, struct b_jump *jp)
{
    /* Skip per-jump garbage 0xFFFFFFFF sentinel values.                    */

    long pos = fs_tell(fin);
    int  v0  = get_index(fin);
    int  v1  = get_index(fin);

    SDL_Log("sol_load_jump: pos=%ld peek v0=0x%08X v1=0x%08X %s",
            pos, (unsigned)v0, (unsigned)v1,
            (v0 == -1 && v1 == -1) ? "SKIPPING" : "KEEPING");

    if (v0 != -1 || v1 != -1)
        fs_seek(fin, pos, SEEK_SET);

    /* Remember where the actual data read starts (after any sentinel).     */

    long data_pos = fs_tell(fin);

    get_array(fin, jp->p, 3);
    get_array(fin, jp->q, 3);

    jp->r = get_float(fin);

    /* Detect "ball extras" contamination.                                  */
    /*                                                                      */
    /* Some pre-compiled SOL files have 2 stray ball-data floats (e.g.      */
    /* position component ~0.0625 and negative-zero) injected before a      */
    /* jump entry.  These are NOT sentinel pairs (-1, -1), so the check     */
    /* above keeps them and they become the first 2 values of the jump      */
    /* read, corrupting the position.  If both p[0] and p[1] are tiny       */
    /* (< 0.1), re-read from 8 bytes past data_pos to skip the extras.     */

    if (fabsf(jp->p[0]) < 0.1f && fabsf(jp->p[1]) < 0.1f)
    {
        SDL_Log("sol_load_jump: suspected ball extras at data_pos=%ld "
                "p=(%.4f,%.4f,%.4f) — re-reading from +8",
                data_pos, jp->p[0], jp->p[1], jp->p[2]);

        fs_seek(fin, data_pos + 8, SEEK_SET);

        get_array(fin, jp->p, 3);
        get_array(fin, jp->q, 3);

        jp->r = get_float(fin);
    }

    SDL_Log("sol_load_jump: p=(%.2f,%.2f,%.2f) q=(%.2f,%.2f,%.2f) r=%.2f pos_after=%ld",
            jp->p[0], jp->p[1], jp->p[2],
            jp->q[0], jp->q[1], jp->q[2], jp->r, fs_tell(fin));
}

static void sol_load_ball(fs_file fin, struct b_ball *up)
{
    get_array(fin, up->p, 3);

    up->r = get_float(fin);
}

static void sol_load_view(fs_file fin, struct b_view *wp)
{
    get_array(fin, wp->p, 3);
    get_array(fin, wp->q, 3);

    SDL_Log("sol_load_view: p=(%.2f,%.2f,%.2f) q=(%.2f,%.2f,%.2f)",
            wp->p[0], wp->p[1], wp->p[2],
            wp->q[0], wp->q[1], wp->q[2]);
}

static void sol_load_dict(fs_file fin, struct b_dict *dp)
{
    dp->ai = get_index(fin);
    dp->aj = get_index(fin);
}

static void sol_load_indx(fs_file fin, struct s_base *fp)
{
    fp->ac = get_index(fin);
    fp->dc = get_index(fin);
    fp->mc = get_index(fin);
    fp->vc = get_index(fin);
    fp->ec = get_index(fin);
    fp->sc = get_index(fin);
    fp->tc = get_index(fin);

    if (sol_version >= SOL_VERSION_1_6)
        fp->oc = get_index(fin);

    fp->gc = get_index(fin);
    fp->lc = get_index(fin);
    fp->nc = get_index(fin);
    fp->pc = get_index(fin);
    fp->bc = get_index(fin);
    fp->hc = get_index(fin);
    fp->zc = get_index(fin);
    fp->jc = get_index(fin);
    fp->xc = get_index(fin);
    fp->rc = get_index(fin);
    fp->uc = get_index(fin);
    fp->wc = get_index(fin);
    fp->ic = get_index(fin);
}

static const char *sol_load_name;

/* Upper bound for any single SOL count field. */
#define SOL_MAX_COUNT 2000000

static int sol_validate_counts(const struct s_base *fp)
{
    if (fp->ac < 0 || fp->ac > SOL_MAX_COUNT) return 0;
    if (fp->dc < 0 || fp->dc > SOL_MAX_COUNT) return 0;
    if (fp->mc < 0 || fp->mc > SOL_MAX_COUNT) return 0;
    if (fp->vc < 0 || fp->vc > SOL_MAX_COUNT) return 0;
    if (fp->ec < 0 || fp->ec > SOL_MAX_COUNT) return 0;
    if (fp->sc < 0 || fp->sc > SOL_MAX_COUNT) return 0;
    if (fp->tc < 0 || fp->tc > SOL_MAX_COUNT) return 0;
    if (fp->oc < 0 || fp->oc > SOL_MAX_COUNT) return 0;
    if (fp->gc < 0 || fp->gc > SOL_MAX_COUNT) return 0;
    if (fp->lc < 0 || fp->lc > SOL_MAX_COUNT) return 0;
    if (fp->nc < 0 || fp->nc > SOL_MAX_COUNT) return 0;
    if (fp->pc < 0 || fp->pc > SOL_MAX_COUNT) return 0;
    if (fp->bc < 0 || fp->bc > SOL_MAX_COUNT) return 0;
    if (fp->hc < 0 || fp->hc > SOL_MAX_COUNT) return 0;
    if (fp->zc < 0 || fp->zc > SOL_MAX_COUNT) return 0;
    if (fp->jc < 0 || fp->jc > SOL_MAX_COUNT) return 0;
    if (fp->xc < 0 || fp->xc > SOL_MAX_COUNT) return 0;
    if (fp->rc < 0 || fp->rc > SOL_MAX_COUNT) return 0;
    if (fp->uc < 0 || fp->uc > SOL_MAX_COUNT) return 0;
    if (fp->wc < 0 || fp->wc > SOL_MAX_COUNT) return 0;
    if (fp->ic < 0 || fp->ic > SOL_MAX_COUNT) return 0;
    return 1;
}

static int sol_load_file(fs_file fin, struct s_base *fp)
{
    int i;

    if (!sol_file(fin))
        return 0;

    sol_load_indx(fin, fp);

    if (!sol_validate_counts(fp))
        return 0;

    if (fp->ac)
        fp->av = (char *)          calloc(fp->ac, sizeof (*fp->av));
    if (fp->mc)
        fp->mv = (struct b_mtrl *) calloc(fp->mc, sizeof (*fp->mv));
    if (fp->vc)
        fp->vv = (struct b_vert *) calloc(fp->vc, sizeof (*fp->vv));
    if (fp->ec)
        fp->ev = (struct b_edge *) calloc(fp->ec, sizeof (*fp->ev));
    if (fp->sc)
        fp->sv = (struct b_side *) calloc(fp->sc, sizeof (*fp->sv));
    if (fp->tc)
        fp->tv = (struct b_texc *) calloc(fp->tc, sizeof (*fp->tv));
    if (fp->oc)
        fp->ov = (struct b_offs *) calloc(fp->oc, sizeof (*fp->ov));
    if (fp->gc)
        fp->gv = (struct b_geom *) calloc(fp->gc, sizeof (*fp->gv));
    if (fp->lc)
        fp->lv = (struct b_lump *) calloc(fp->lc, sizeof (*fp->lv));
    if (fp->nc)
        fp->nv = (struct b_node *) calloc(fp->nc, sizeof (*fp->nv));
    if (fp->pc)
        fp->pv = (struct b_path *) calloc(fp->pc, sizeof (*fp->pv));
    if (fp->bc)
        fp->bv = (struct b_body *) calloc(fp->bc, sizeof (*fp->bv));
    if (fp->hc)
        fp->hv = (struct b_item *) calloc(fp->hc, sizeof (*fp->hv));
    if (fp->zc)
        fp->zv = (struct b_goal *) calloc(fp->zc, sizeof (*fp->zv));
    if (fp->jc)
        fp->jv = (struct b_jump *) calloc(fp->jc, sizeof (*fp->jv));
    if (fp->xc)
        fp->xv = (struct b_swch *) calloc(fp->xc, sizeof (*fp->xv));
    if (fp->rc)
        fp->rv = (struct b_bill *) calloc(fp->rc, sizeof (*fp->rv));
    if (fp->uc)
        fp->uv = (struct b_ball *) calloc(fp->uc, sizeof (*fp->uv));
    if (fp->wc)
        fp->wv = (struct b_view *) calloc(fp->wc, sizeof (*fp->wv));
    if (fp->dc)
        fp->dv = (struct b_dict *) calloc(fp->dc, sizeof (*fp->dv));
    if (fp->ic)
        fp->iv = (int *)           calloc(fp->ic, sizeof (*fp->iv));

    if (fp->ac)
        fs_read(fp->av, 1, fp->ac, fin);

    for (i = 0; i < fp->dc; i++) sol_load_dict(fin, fp->dv + i);
    for (i = 0; i < fp->mc; i++) sol_load_mtrl(fin, fp->mv + i);
    for (i = 0; i < fp->vc; i++) sol_load_vert(fin, fp->vv + i);
    for (i = 0; i < fp->ec; i++) sol_load_edge(fin, fp->ev + i);
    for (i = 0; i < fp->sc; i++) sol_load_side(fin, fp->sv + i);
    for (i = 0; i < fp->tc; i++) sol_load_texc(fin, fp->tv + i);
    for (i = 0; i < fp->oc; i++) sol_load_offs(fin, fp->ov + i);
    for (i = 0; i < fp->gc; i++) sol_load_geom(fin, fp->gv + i, fp);
    for (i = 0; i < fp->lc; i++) sol_load_lump(fin, fp->lv + i);
    for (i = 0; i < fp->nc; i++) sol_load_node(fin, fp->nv + i);
    for (i = 0; i < fp->pc; i++) sol_load_path(fin, fp->pv + i);
    for (i = 0; i < fp->bc; i++) sol_load_body(fin, fp->bv + i);
    for (i = 0; i < fp->hc; i++) sol_load_item(fin, fp->hv + i);
    for (i = 0; i < fp->zc; i++) sol_load_goal(fin, fp->zv + i);

    /* Repair goals with corrupted radius and position.                     */
    /* Some pre-compiled SOL files have the last fields of a goal entry     */
    /* (p[2] and r) overwritten by ball data.  Detect by checking for an   */
    /* unreasonably small radius (smaller than any playable hole), then     */
    /* recover r from a valid sibling goal and p[2] from the centroid of   */
    /* nearby vertices (the hole rim geometry).                             */

    for (i = 0; i < fp->zc; i++)
    {
        struct b_goal *zp = fp->zv + i;

        if (zp->r >= 0.1f)
            continue;

        SDL_Log("sol_load_goal: goal[%d] r=%.4f suspect (too small), repairing",
                i, zp->r);

        /* Repair radius from the first valid sibling goal. */

        {
            int   j;
            float good_r = 0.75f;          /* fallback to default */

            for (j = 0; j < fp->zc; j++)
            {
                if (j != i && fp->zv[j].r >= 0.1f)
                {
                    good_r = fp->zv[j].r;
                    break;
                }
            }

            SDL_Log("sol_load_goal: repaired goal[%d] r=%.4f->%.4f",
                    i, zp->r, good_r);
            zp->r = good_r;
        }

        /* Repair p[2] using vertex proximity.                              */
        /* The goal sits at the center of a circular hole in the geometry.  */
        /* Search vertices near (p[0], p[1]) to find the hole's Z coord.   */

        {
            int   j;
            float sum_z = 0.0f;
            int   count = 0;

            for (j = 0; j < fp->vc; j++)
            {
                float dx = fp->vv[j].p[0] - zp->p[0];
                float dy = fp->vv[j].p[1] - zp->p[1];

                if (dx * dx + dy * dy < 0.25f)
                {
                    sum_z += fp->vv[j].p[2];
                    count++;
                }
            }

            if (count > 0)
            {
                float avg_z = sum_z / (float) count;
                float diff  = avg_z - zp->p[2];

                if (diff < 0.0f) diff = -diff;

                if (diff > 1.0f)
                {
                    SDL_Log("sol_load_goal: repaired goal[%d] p[2]=%.4f->%.4f "
                            "(%d nearby vertices)",
                            i, zp->p[2], avg_z, count);
                    zp->p[2] = avg_z;
                }
            }
            else
            {
                SDL_Log("sol_load_goal: WARNING goal[%d] no vertices found "
                        "near (%.2f, %.2f), cannot repair p[2]",
                        i, zp->p[0], zp->p[1]);
            }
        }
    }

    /* Sentinel-bearing sections.  sol_load_jump and sol_load_swch each     */
    /* peek for 0xFFFFFFFF sentinel pairs and consume them, so after these  */
    /* loops the cursor is correctly positioned past all sentinel bytes     */
    /* and real data — no seek-back needed.                                 */

    for (i = 0; i < fp->jc; i++) sol_load_jump(fin, fp->jv + i);
    for (i = 0; i < fp->xc; i++) sol_load_swch(fin, fp->xv + i);

    /* Repair switches with corrupted path indices.                         */
    /* Some pre-compiled SOL files have switch fields (pi, t) overwritten   */
    /* by ball data.  When pi is out of range, find the moving body whose   */
    /* starting path is not already claimed by a valid switch and link to   */
    /* it.  Recover the timer from the first valid switch with the same     */
    /* default state.                                                       */

    for (i = 0; i < fp->xc; i++)
    {
        struct b_swch *xp = fp->xv + i;

        if (xp->pi >= 0 && xp->pi < fp->pc)
            continue;

        SDL_Log("sol_load_swch: swch[%d] pi=%d OUT OF RANGE (pc=%d), repairing",
                i, xp->pi, fp->pc);

        /* Collect path indices already claimed by valid switches. */

        {
            int  claimed[64] = { 0 };
            int  j;
            float best_t = 0.0f;
            int   found_t = 0;

            for (j = 0; j < fp->xc && j < 64; j++)
            {
                if (j != i && fp->xv[j].pi >= 0 && fp->xv[j].pi < fp->pc)
                {
                    if (fp->xv[j].pi < 64)
                        claimed[fp->xv[j].pi] = 1;

                    /* Pick timer from a valid switch with the same state. */

                    if (!found_t && fp->xv[j].f == xp->f)
                    {
                        best_t  = fp->xv[j].t;
                        found_t = 1;
                    }
                }
            }

            /* Find a moving body whose starting path is unclaimed. */

            for (j = 0; j < fp->bc; j++)
            {
                int bpi = fp->bv[j].pi;

                if (bpi >= 0 && bpi < fp->pc && bpi < 64 && !claimed[bpi])
                {
                    SDL_Log("sol_load_swch: repaired swch[%d] pi=%d->%d "
                            "(body[%d] path)", i, xp->pi, bpi, j);
                    xp->pi = bpi;
                    break;
                }
            }

            /* Repair the timer if it looks corrupted. */

            if (found_t && xp->t < 0.1f)
            {
                SDL_Log("sol_load_swch: repaired swch[%d] t=%.4f->%.4f",
                        i, xp->t, best_t);
                xp->t  = best_t;
                xp->tm = TIME_TO_MS(xp->t);
                xp->t  = MS_TO_TIME(xp->tm);
            }

            if (xp->pi < 0 || xp->pi >= fp->pc)
            {
                SDL_Log("sol_load_swch: WARNING swch[%d] pi=%d still invalid, "
                        "clamping to 0", i, xp->pi);
                xp->pi = 0;
            }
        }
    }

    for (i = 0; i < fp->rc; i++) sol_load_bill(fin, fp->rv + i);

    for (i = 0; i < fp->uc; i++) sol_load_ball(fin, fp->uv + i);

    /* Skip duplicate ball entries not counted by the header.               */
    /* Some pre-compiled SOL files have extra ball entries appended that    */
    /* shift the view and index sections if not consumed.                   */

    if (fp->uc > 0)
    {
        int skipped = 0;

        for (;;)
        {
            long  pos = fs_tell(fin);
            float p[3];
            float r;
            int   j, is_dup = 0;

            get_array(fin, p, 3);
            r = get_float(fin);

            for (j = 0; j < fp->uc; j++)
            {
                if (p[0] == fp->uv[j].p[0] &&
                    p[1] == fp->uv[j].p[1] &&
                    p[2] == fp->uv[j].p[2] &&
                    r    == fp->uv[j].r)
                {
                    is_dup = 1;
                    break;
                }
            }

            if (is_dup)
            {
                SDL_Log("sol_load(%s): skipping extra ball at pos=%ld "
                        "p=(%.3f,%.3f,%.3f) r=%.4f",
                        sol_load_name, pos, p[0], p[1], p[2], r);
                skipped++;
            }
            else
            {
                fs_seek(fin, pos, SEEK_SET);
                break;
            }
        }

        if (skipped)
            SDL_Log("sol_load(%s): skipped %d extra ball entries",
                    sol_load_name, skipped);
    }

    for (i = 0; i < fp->wc; i++) sol_load_view(fin, fp->wv + i);
    for (i = 0; i < fp->ic; i++) fp->iv[i] = get_index(fin);

    /* Fix shifted index array.                                             */
    /*                                                                      */
    /* Some pre-compiled SOL files have extra values prepended to the       */
    /* index array, shifting all real data right.  The shift can range      */
    /* from 2 entries (common) to 100+ entries (e.g. 17.sol with 114).     */
    /* The lump v0/e0/s0/g0 fields were compiled against the UN-shifted    */
    /* array, so every indirect lookup through iv[] is off by the shift.   */
    /*                                                                      */
    /* Detection: compute shift from remaining file data after ic entries.  */
    /* The trailing entries ARE the real data that was pushed past the      */
    /* nominal end.  Validate that all trailing entries are valid indices   */
    /* before correcting.                                                   */

    if (fp->ic >= 4)
    {
        int max_idx = fp->vc;
        int shift = 0;

        if (fp->ec > max_idx) max_idx = fp->ec;
        if (fp->sc > max_idx) max_idx = fp->sc;
        if (fp->gc > max_idx) max_idx = fp->gc;

        /* Compute shift from remaining file data after ic entries.     */

        {
            long pos_after_ic = fs_tell(fin);

            fs_seek(fin, 0, SEEK_END);
            long file_end = fs_tell(fin);
            int  trailing_bytes = (int)(file_end - pos_after_ic);

            fs_seek(fin, pos_after_ic, SEEK_SET);

            if (trailing_bytes > 0 && (trailing_bytes % 4) == 0)
                shift = trailing_bytes / 4;
        }

        if (shift > 0 && shift < fp->ic)
        {
            int *extras = (int *) calloc(shift, sizeof (int));
            int  valid  = 1;

            if (extras)
            {
                for (i = 0; i < shift; i++)
                {
                    extras[i] = get_index(fin);
                    if (extras[i] < 0 || extras[i] >= max_idx)
                    {
                        valid = 0;
                        break;
                    }
                }

                if (valid)
                {
                    SDL_Log("sol_load(%s): iv[] shifted by %d, correcting "
                            "(iv[0]=0x%X iv[1]=0x%X)",
                            sol_load_name, shift, fp->iv[0],
                            shift > 1 ? fp->iv[1] : 0);

                    memmove(fp->iv, fp->iv + shift,
                            (fp->ic - shift) * sizeof (int));

                    for (i = 0; i < shift; i++)
                        fp->iv[fp->ic - shift + i] = extras[i];
                }

                free(extras);
            }
        }
    }

    /* Magically "fix" all of our code. */

    if (!fp->uc)
    {
        fp->uc = 1;
        fp->uv = (struct b_ball *) calloc(fp->uc, sizeof (*fp->uv));
    }

    /* Fix zero or negative ball radii.  Some corrupted SOL files have     */
    /* ball entries with r=0, causing the ball to clip through geometry.    */

    for (i = 0; i < fp->uc; i++)
    {
        if (fp->uv[i].r <= 0.0f)
        {
            SDL_Log("sol_load(%s): fixing ball[%d] r=%.4f -> 0.0625",
                    sol_load_name, i, fp->uv[i].r);
            fp->uv[i].r = 0.0625f;
        }
    }

    /* Add lit flag to old materials. */

    if (sol_version <= SOL_VERSION_1_6)
    {
        for (i = 0; i < fp->mc; ++i)
            fp->mv[i].fl |= M_LIT;

        for (i = 0; i < fp->rc; ++i)
          fp->mv[fp->rv[i].mi].fl &= ~M_LIT;
    }

    return 1;
}

static int sol_load_head(fs_file fin, struct s_base *fp)
{
    if (!sol_file(fin))
        return 0;

    sol_load_indx(fin, fp);

    if (fp->ac)
    {
        fp->av = (char *) calloc(fp->ac, sizeof (*fp->av));
        fs_read(fp->av, 1, fp->ac, fin);
    }

    if (fp->dc)
    {
        int i;

        fp->dv = (struct b_dict *) calloc(fp->dc, sizeof (*fp->dv));

        for (i = 0; i < fp->dc; i++)
            sol_load_dict(fin, fp->dv + i);
    }

    return 1;
}

int sol_load_base(struct s_base *fp, const char *filename)
{
    fs_file fin;
    int res = 0;

    memset(fp, 0, sizeof (*fp));

    if ((fin = fs_open_read(filename)))
    {
        sol_load_name = filename;
        res = sol_load_file(fin, fp);
        fs_close(fin);
    }
    return res;
}

int sol_load_meta(struct s_base *fp, const char *filename)
{
    fs_file fin;
    int res = 0;

    memset(fp, 0, sizeof (*fp));

    if ((fin = fs_open_read(filename)))
    {
        res = sol_load_head(fin, fp);
        fs_close(fin);
    }
    return res;
}

void sol_free_base(struct s_base *fp)
{
    if (fp->av) free(fp->av);
    if (fp->mv) free(fp->mv);
    if (fp->vv) free(fp->vv);
    if (fp->ev) free(fp->ev);
    if (fp->sv) free(fp->sv);
    if (fp->tv) free(fp->tv);
    if (fp->ov) free(fp->ov);
    if (fp->gv) free(fp->gv);
    if (fp->lv) free(fp->lv);
    if (fp->nv) free(fp->nv);
    if (fp->pv) free(fp->pv);
    if (fp->bv) free(fp->bv);
    if (fp->hv) free(fp->hv);
    if (fp->zv) free(fp->zv);
    if (fp->jv) free(fp->jv);
    if (fp->xv) free(fp->xv);
    if (fp->rv) free(fp->rv);
    if (fp->uv) free(fp->uv);
    if (fp->wv) free(fp->wv);
    if (fp->dv) free(fp->dv);
    if (fp->iv) free(fp->iv);

    memset(fp, 0, sizeof (*fp));
}

/*---------------------------------------------------------------------------*/

static void sol_stor_mtrl(fs_file fout, struct b_mtrl *mp)
{
    put_array(fout, mp->d, 4);
    put_array(fout, mp->a, 4);
    put_array(fout, mp->s, 4);
    put_array(fout, mp->e, 4);
    put_array(fout, mp->h, 1);
    put_index(fout, mp->fl);

    fs_write(mp->f, 1, PATHMAX, fout);

    if (mp->fl & M_ALPHA_TEST)
    {
        put_index(fout, mp->alpha_func);
        put_float(fout, mp->alpha_ref);
    }
}

static void sol_stor_vert(fs_file fout, struct b_vert *vp)
{
    put_array(fout,  vp->p, 3);
}

static void sol_stor_edge(fs_file fout, struct b_edge *ep)
{
    put_index(fout, ep->vi);
    put_index(fout, ep->vj);
}

static void sol_stor_side(fs_file fout, struct b_side *sp)
{
    put_array(fout, sp->n, 3);
    put_float(fout, sp->d);
}

static void sol_stor_texc(fs_file fout, struct b_texc *tp)
{
    put_array(fout,  tp->u, 2);
}

static void sol_stor_offs(fs_file fout, struct b_offs *op)
{
    put_index(fout, op->ti);
    put_index(fout, op->si);
    put_index(fout, op->vi);
}

static void sol_stor_geom(fs_file fout, struct b_geom *gp)
{
    put_index(fout, gp->mi);
    put_index(fout, gp->oi);
    put_index(fout, gp->oj);
    put_index(fout, gp->ok);
}

static void sol_stor_lump(fs_file fout, struct b_lump *lp)
{
    put_index(fout, lp->fl);
    put_index(fout, lp->v0);
    put_index(fout, lp->vc);
    put_index(fout, lp->e0);
    put_index(fout, lp->ec);
    put_index(fout, lp->g0);
    put_index(fout, lp->gc);
    put_index(fout, lp->s0);
    put_index(fout, lp->sc);
}

static void sol_stor_node(fs_file fout, struct b_node *np)
{
    put_index(fout, np->si);
    put_index(fout, np->ni);
    put_index(fout, np->nj);
    put_index(fout, np->l0);
    put_index(fout, np->lc);
}

static void sol_stor_path(fs_file fout, struct b_path *pp)
{
    put_array(fout, pp->p, 3);
    put_float(fout, pp->t);
    put_index(fout, pp->pi);
    put_index(fout, pp->f);
    put_index(fout, pp->s);
    put_index(fout, pp->fl);

    if (pp->fl & P_ORIENTED)
        put_array(fout, pp->e, 4);
}

static void sol_stor_body(fs_file fout, struct b_body *bp)
{
    put_index(fout, bp->pi);
    put_index(fout, bp->pj);
    put_index(fout, bp->ni);
    put_index(fout, bp->l0);
    put_index(fout, bp->lc);
    put_index(fout, bp->g0);
    put_index(fout, bp->gc);
}

static void sol_stor_item(fs_file fout, struct b_item *hp)
{
    put_array(fout, hp->p, 3);
    put_index(fout, hp->t);
    put_index(fout, hp->n);
}

static void sol_stor_goal(fs_file fout, struct b_goal *zp)
{
    put_array(fout, zp->p, 3);
    put_float(fout, zp->r);
}

static void sol_stor_swch(fs_file fout, struct b_swch *xp)
{
    put_array(fout, xp->p, 3);
    put_float(fout, xp->r);
    put_index(fout, xp->pi);
    put_float(fout, xp->t);
    put_float(fout, xp->t);
    put_index(fout, xp->f);
    put_index(fout, xp->f);
    put_index(fout, xp->i);
}

static void sol_stor_bill(fs_file fout, struct b_bill *rp)
{
    put_index(fout, rp->fl);
    put_index(fout, rp->mi);
    put_float(fout, rp->t);
    put_float(fout, rp->d);
    put_array(fout, rp->w,  3);
    put_array(fout, rp->h,  3);
    put_array(fout, rp->rx, 3);
    put_array(fout, rp->ry, 3);
    put_array(fout, rp->rz, 3);
    put_array(fout, rp->p,  3);
}

static void sol_stor_jump(fs_file fout, struct b_jump *jp)
{
    put_array(fout, jp->p, 3);
    put_array(fout, jp->q, 3);
    put_float(fout, jp->r);
}

static void sol_stor_ball(fs_file fout, struct b_ball *bp)
{
    put_array(fout, bp->p, 3);
    put_float(fout, bp->r);
}

static void sol_stor_view(fs_file fout, struct b_view *wp)
{
    put_array(fout,  wp->p, 3);
    put_array(fout,  wp->q, 3);
}

static void sol_stor_dict(fs_file fout, struct b_dict *dp)
{
    put_index(fout, dp->ai);
    put_index(fout, dp->aj);
}

static void sol_stor_file(fs_file fout, struct s_base *fp)
{
    int i;
    int magic   = SOL_MAGIC;
    int version = SOL_VERSION_CURR;

    put_index(fout, magic);
    put_index(fout, version);

    put_index(fout, fp->ac);
    put_index(fout, fp->dc);
    put_index(fout, fp->mc);
    put_index(fout, fp->vc);
    put_index(fout, fp->ec);
    put_index(fout, fp->sc);
    put_index(fout, fp->tc);
    put_index(fout, fp->oc);
    put_index(fout, fp->gc);
    put_index(fout, fp->lc);
    put_index(fout, fp->nc);
    put_index(fout, fp->pc);
    put_index(fout, fp->bc);
    put_index(fout, fp->hc);
    put_index(fout, fp->zc);
    put_index(fout, fp->jc);
    put_index(fout, fp->xc);
    put_index(fout, fp->rc);
    put_index(fout, fp->uc);
    put_index(fout, fp->wc);
    put_index(fout, fp->ic);

    fs_write(fp->av, 1, fp->ac, fout);

    for (i = 0; i < fp->dc; i++) sol_stor_dict(fout, fp->dv + i);
    for (i = 0; i < fp->mc; i++) sol_stor_mtrl(fout, fp->mv + i);
    for (i = 0; i < fp->vc; i++) sol_stor_vert(fout, fp->vv + i);
    for (i = 0; i < fp->ec; i++) sol_stor_edge(fout, fp->ev + i);
    for (i = 0; i < fp->sc; i++) sol_stor_side(fout, fp->sv + i);
    for (i = 0; i < fp->tc; i++) sol_stor_texc(fout, fp->tv + i);
    for (i = 0; i < fp->oc; i++) sol_stor_offs(fout, fp->ov + i);
    for (i = 0; i < fp->gc; i++) sol_stor_geom(fout, fp->gv + i);
    for (i = 0; i < fp->lc; i++) sol_stor_lump(fout, fp->lv + i);
    for (i = 0; i < fp->nc; i++) sol_stor_node(fout, fp->nv + i);
    for (i = 0; i < fp->pc; i++) sol_stor_path(fout, fp->pv + i);
    for (i = 0; i < fp->bc; i++) sol_stor_body(fout, fp->bv + i);
    for (i = 0; i < fp->hc; i++) sol_stor_item(fout, fp->hv + i);
    for (i = 0; i < fp->zc; i++) sol_stor_goal(fout, fp->zv + i);
    for (i = 0; i < fp->jc; i++) sol_stor_jump(fout, fp->jv + i);
    for (i = 0; i < fp->xc; i++) sol_stor_swch(fout, fp->xv + i);
    for (i = 0; i < fp->rc; i++) sol_stor_bill(fout, fp->rv + i);
    for (i = 0; i < fp->uc; i++) sol_stor_ball(fout, fp->uv + i);
    for (i = 0; i < fp->wc; i++) sol_stor_view(fout, fp->wv + i);
    for (i = 0; i < fp->ic; i++) put_index(fout, fp->iv[i]);
}

int sol_stor_base(struct s_base *fp, const char *filename)
{
    fs_file fout;

    if ((fout = fs_open_write(filename)))
    {
        sol_stor_file(fout, fp);
        fs_close(fout);

        return 1;
    }
    return 0;
}

/*---------------------------------------------------------------------------*/

const struct path tex_paths[4] = {
    { "textures/", ".png" },
    { "textures/", ".jpg" },
    { "",          ".png" },
    { "",          ".jpg" }
};

const struct path mtrl_paths[2] = {
    { "textures/", "" },
    { "",          "" }
};

/*---------------------------------------------------------------------------*/

/*
 * This has to match up with mtrl_func_syms in mtrl.c.
 */
static const char mtrl_func_names[8][16] = {
    "always",
    "equal",
    "gequal",
    "greater",
    "lequal",
    "less",
    "never",
    "notequal"
};

static const struct
{
    char name[16];
    int flag;
} mtrl_flags[] = {
    { "additive",    M_ADDITIVE },
    { "clamp-s",     M_CLAMP_S },
    { "clamp-t",     M_CLAMP_T },
    { "decal",       M_DECAL },
    { "environment", M_ENVIRONMENT },
    { "reflective",  M_REFLECTIVE },
    { "shadowed",    M_SHADOWED },
    { "transparent", M_TRANSPARENT },
    { "two-sided",   M_TWO_SIDED },
    { "particle",    M_PARTICLE },
    { "lit",         M_LIT },
};

int mtrl_read(struct b_mtrl *mp, const char *name)
{
    static char line[MAXSTR];
    static char word[MAXSTR];

    fs_file fp;
    int i;

    if (mp && name && *name)
    {
        SAFECPY(mp->f, name);

        mp->a[0] = mp->a[1] = mp->a[2] = 0.2f;
        mp->d[0] = mp->d[1] = mp->d[2] = 0.8f;
        mp->s[0] = mp->s[1] = mp->s[2] = 0.0f;
        mp->e[0] = mp->e[1] = mp->e[2] = 0.0f;
        mp->a[3] = mp->d[3] = mp->s[3] = mp->e[3] = 1.0f;
        mp->h[0] = 0.0f;
        mp->fl   = 0;
        mp->angle = 45.0f;

        mp->alpha_func = 0;
        mp->alpha_ref  = 0.0f;

        fp = NULL;

        for (i = 0; i < ARRAYSIZE(mtrl_paths); i++)
        {
            CONCAT_PATH(line, &mtrl_paths[i], name);

            if ((fp = fs_open_read(line)))
                break;
        }

        if (fp)
        {
            char str[16] = "";

            while (fs_gets(line, sizeof (line), fp))
            {
                char *p = strip_newline(line);

                if (sscanf(p, "diffuse %f %f %f %f",
                           &mp->d[0], &mp->d[1],
                           &mp->d[2], &mp->d[3]) == 4)
                {
                }
                else if (sscanf(p, "ambient %f %f %f %f",
                                &mp->a[0], &mp->a[1],
                                &mp->a[2], &mp->a[3]) == 4)
                {
                }
                else if (sscanf(p, "specular %f %f %f %f",
                                &mp->s[0], &mp->s[1],
                                &mp->s[2], &mp->s[3]) == 4)
                {
                }
                else if (sscanf(p, "emissive %f %f %f %f",
                                &mp->e[0], &mp->e[1],
                                &mp->e[2], &mp->e[3]) == 4)
                {
                }
                else if (sscanf(p, "shininess %f", &mp->h[0]) == 1)
                {
                }
                else if (strncmp(p, "flags ", 6) == 0)
                {
                    int f = 0;
                    int n;

                    p += 6;

                    while (sscanf(p, "%s%n", word, &n) > 0)
                    {
                        for (i = 0; i < ARRAYSIZE(mtrl_flags); i++)
                            if (strcmp(word, mtrl_flags[i].name) == 0)
                            {
                                f |= mtrl_flags[i].flag;
                                break;
                            }

                        p += n;
                    }

                    mp->fl = f;
                }
                else if (sscanf(p, "angle %f", &mp->angle) == 1)
                {
                }
                else if (sscanf(p, "alpha-test %15s %f",
                                str, &mp->alpha_ref) == 2)
                {
                    mp->fl |= M_ALPHA_TEST;

                    for (i = 0; i < ARRAYSIZE(mtrl_func_names); i++)
                        if (strcmp(str, mtrl_func_names[i]) == 0)
                        {
                            mp->alpha_func = i;
                            break;
                        }
                }
                else /* Unknown directive */;
            }

            fs_close(fp);
            return 1;
        }
        else /* Unknown material */;
    }
    return 0;
}

/*---------------------------------------------------------------------------*/
