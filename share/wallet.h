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

#ifndef WALLET_H
#define WALLET_H

void        wallet_init(void);
void        wallet_free(void);
void        wallet_connect(void);
int         wallet_state(void);     /* 0=disconnected..5=error */
int         wallet_is_seeker(void); /* 1 if SGT verified */
const char *wallet_pubkey(void);    /* base58 pubkey or "" */
void        wallet_disconnect(void);

#endif
