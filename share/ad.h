/*
 * Copyright (C) 2026 MiniPutt Mobile Contributors
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

#ifndef AD_H
#define AD_H

void ad_init(void);
void ad_free(void);
void ad_show_interstitial(void);
void ad_show_rewarded(void);
void ad_dismiss(void);
int  ad_rewarded_state(void);   /* 0=idle, 1=showing, 2=complete, 3=dismissed */
void ad_rewarded_reset(void);
int  ad_interstitial_state(void);  /* 0=idle, 1=showing, 2=dismissed */
void ad_interstitial_reset(void);

#endif
