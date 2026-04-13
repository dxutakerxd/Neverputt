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

#ifndef HAPTIC_H
#define HAPTIC_H

void haptic_init(void);
void haptic_free(void);

void haptic_bump(float intensity);   /* Ball bounces off wall        */
void haptic_putt(void);              /* Player executes putt         */
void haptic_goal(void);              /* Ball enters hole             */
void haptic_fall(void);              /* Ball falls off course        */
void haptic_switch(void);            /* Ball hits switch             */
void haptic_jump(void);              /* Ball hits jump pad           */

#endif
