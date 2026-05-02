import pygame
import sys
import math
import random
import struct
import wave
import io

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

WALL_THICKNESS = 22
PLAY_X1 = WALL_THICKNESS
PLAY_Y1 = 70 + WALL_THICKNESS
PLAY_X2 = SCREEN_W - WALL_THICKNESS
PLAY_Y2 = SCREEN_H - WALL_THICKNESS - 30

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("MISSION: IMPOSSIBLE")
clock = pygame.time.Clock()

pygame.mouse.set_visible(True)

cursor_x = float(SCREEN_W // 2)
cursor_y = float(SCREEN_H // 2)

BLACK      = (0,   0,   0)
DEEP_RED   = (80,  0,   0)
DARK_RED   = (140, 10,  10)
RED        = (220, 30,  30)
BRIGHT_RED = (255, 60,  60)
CRIMSON    = (180, 0,   20)
BLOOD      = (100, 0,   10)
CHARCOAL   = (18,  18,  18)
DARK_GRAY  = (28,  28,  28)
MID_GRAY   = (45,  45,  45)
GRAY       = (70,  70,  70)
LIGHT_GRAY = (110, 110, 110)
WHITE      = (230, 230, 230)
DIM_WHITE  = (160, 160, 160)
ORANGE     = (220, 100, 20)
GOLD       = (200, 160, 30)
DIM_GOLD   = (120, 90,  15)
AMBER      = (255, 140, 0)
CYAN_DIM   = (0,   80,  100)
CYAN       = (0,   180, 220)
TEAL       = (0,   120, 100)
GREEN_DIM  = (20,  80,  20)
GREEN      = (40,  200, 80)
PURPLE     = (140, 30,  200)
DARK_BG    = (6,   6,   8)
WALL_COL   = (22,  8,   8)
WALL_EDGE  = (60,  15,  15)
WALL_LIT   = (120, 25,  25)

NEON_TEAL  = (0, 230, 200)
NEON_PINK  = (255, 40, 120)
DEEP_NAVY  = (5, 8, 18)
CAPE_DARK  = (10, 5, 30)
CAPE_MID   = (30, 10, 80)
CAPE_LIGHT = (80, 30, 180)
CAPE_SHINE = (140, 60, 255)

MAX_PARTICLES = {1: 200, 2: 180, 3: 160, 4: 140, 5: 120}
_current_level = 1


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_sound(freq=440, duration=0.15, wave_type='square', volume=0.3,
               attack=0.01, decay=0.05, freq_sweep=0):
    rate = 44100
    n = int(rate * duration)
    samples = []
    for i in range(n):
        t = i / rate
        env_t = i / n
        if env_t < attack:
            env = env_t / attack
        elif env_t < attack + decay:
            env = 1.0 - (env_t - attack) / decay * 0.4
        else:
            env = 0.6 * (1.0 - (env_t - attack - decay) / max(0.001, 1 - attack - decay))
        env = max(0, env)
        f = freq + freq_sweep * env_t
        phase = 2 * math.pi * f * t
        if wave_type == 'square':
            v = 1.0 if math.sin(phase) > 0 else -1.0
        elif wave_type == 'sawtooth':
            v = 2.0 * ((f * t) % 1.0) - 1.0
        elif wave_type == 'noise':
            v = random.uniform(-1, 1)
        else:
            v = math.sin(phase)
        samples.append(int(v * env * volume * 32767))
    raw = struct.pack(f'<{n}h', *samples)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(raw)
    buf.seek(0)
    try:
        return pygame.mixer.Sound(buf)
    except:
        return None


SFX = {}
try:
    SFX['shoot']         = make_sound(900,  0.07, 'square',   0.2,  freq_sweep=-500)
    SFX['missile']       = make_sound(180,  0.3,  'sawtooth', 0.3,  freq_sweep=700)
    SFX['explode']       = make_sound(100,  0.45, 'noise',    0.5,  decay=0.35)
    SFX['hit']           = make_sound(280,  0.1,  'square',   0.25, freq_sweep=-150)
    SFX['die']           = make_sound(140,  0.5,  'sawtooth', 0.4,  freq_sweep=-80)
    SFX['powerup']       = make_sound(480,  0.3,  'sine',     0.3,  freq_sweep=960)
    SFX['player_hit']    = make_sound(160,  0.2,  'noise',    0.4)
    SFX['portal']        = make_sound(640,  0.4,  'sine',     0.28, freq_sweep=180)
    SFX['boss_hit']      = make_sound(90,   0.22, 'sawtooth', 0.45, freq_sweep=-40)
    SFX['boss_ability']  = make_sound(60,   0.6,  'sawtooth', 0.5,  freq_sweep=200)
    SFX['boss_teleport'] = make_sound(440,  0.25, 'sine',     0.35, freq_sweep=-300)
    SFX['boss_shield']   = make_sound(320,  0.4,  'square',   0.3,  freq_sweep=100)
except Exception:
    SFX = {}


def play(name):
    if name in SFX and SFX[name]:
        try:
            SFX[name].play()
        except:
            pass


def load_fonts():
    fonts = {}
    for fname in ["couriernew", "lucidaconsole", "consolas", None]:
        try:
            fonts['title'] = pygame.font.SysFont(fname, 56, bold=True)
            fonts['big']   = pygame.font.SysFont(fname, 34, bold=True)
            fonts['med']   = pygame.font.SysFont(fname, 22, bold=True)
            fonts['small'] = pygame.font.SysFont(fname, 16)
            fonts['tiny']  = pygame.font.SysFont(fname, 13)
            fonts['micro'] = pygame.font.SysFont(fname, 11)
            break
        except:
            pass
    return fonts


FONTS = load_fonts()


def glow_circle(surf, color, cx, cy, r, layers=3, base_alpha=80):
    if r <= 0:
        return
    actual_layers = max(1, layers - (_current_level // 3))
    for i in range(actual_layers):
        rr = r + i * 4
        a  = max(0, int(base_alpha * (1 - i / actual_layers) ** 1.5))
        s  = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color[:3], a), (rr + 1, rr + 1), rr)
        surf.blit(s, (cx - rr - 1, cy - rr - 1))


def draw_text_centered(surf, text, font, color, cx, cy, glow_col=None):
    if glow_col:
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx or dy:
                    gs = font.render(text, True, glow_col)
                    surf.blit(gs, gs.get_rect(center=(cx + dx, cy + dy)))
    shadow = font.render(text, True, BLACK)
    surf.blit(shadow, shadow.get_rect(center=(cx + 2, cy + 2)))
    main = font.render(text, True, color)
    surf.blit(main, main.get_rect(center=(cx, cy)))


def draw_text_left(surf, text, font, color, x, y):
    shadow = font.render(text, True, BLACK)
    surf.blit(shadow, (x + 1, y + 1))
    main = font.render(text, True, color)
    surf.blit(main, (x, y))


def particles_burst(particles, x, y, color, count=12, speed=4, gravity=0.08, life=1.0):
    cap = MAX_PARTICLES.get(_current_level, 120)
    if len(particles) >= cap:
        count = max(2, count // 2)
    for _ in range(count):
        if len(particles) >= cap:
            break
        angle = random.uniform(0, math.pi * 2)
        spd   = random.uniform(0.5, speed)
        particles.append({
            'x': float(x), 'y': float(y),
            'vx': math.cos(angle) * spd,
            'vy': math.sin(angle) * spd,
            'life': life * random.uniform(0.6, 1.0),
            'max_life': life,
            'color': color[:3],
            'size': random.randint(2, 4),
            'gravity': gravity,
        })


def update_particles(particles, dt):
    for p in particles[:]:
        p['x']  += p['vx']
        p['y']  += p['vy']
        p['vy'] += p['gravity']
        p['vx'] *= 0.96
        p['life'] -= dt * 1.8
        if p['life'] <= 0:
            particles.remove(p)


def draw_particles(surf, particles):
    for p in particles:
        a = max(0, min(255, int(p['life'] / p['max_life'] * 220)))
        s = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*p['color'], a), (p['size'], p['size']), p['size'])
        surf.blit(s, (int(p['x']) - p['size'], int(p['y']) - p['size']))


def shockwave(shockwaves, x, y, color=RED):
    shockwaves.append({'x': x, 'y': y, 'r': 4, 'max_r': 70, 'life': 1.0, 'color': color})


def update_shockwaves(shockwaves, dt):
    for sw in shockwaves[:]:
        sw['r']    += 180 * dt
        sw['life'] -= dt * 2.8
        if sw['r'] > sw['max_r'] or sw['life'] <= 0:
            shockwaves.remove(sw)


def draw_shockwaves(surf, shockwaves):
    for sw in shockwaves:
        a = max(0, int(sw['life'] * 100))
        r = int(sw['r'])
        if r > 0:
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*sw['color'][:3], a), (r + 2, r + 2), r, 3)
            surf.blit(s, (int(sw['x']) - r - 2, int(sw['y']) - r - 2))


_stars = None


def make_stars():
    global _stars
    if _stars:
        return _stars
    _stars = []
    for _ in range(80):  
        _stars.append({
            'x': random.randint(PLAY_X1, PLAY_X2),
            'y': random.randint(PLAY_Y1, PLAY_Y2),
            'r': random.uniform(0.5, 2.2),
            'twinkle': random.uniform(0, math.pi * 2),
            'speed': random.uniform(0.02, 0.06),
            'color': random.choice([(180,140,140),(140,140,200),(160,180,200),(200,160,140)])
        })
    return _stars


_scanline_surf = None


def get_scanline_surf():
    global _scanline_surf
    if _scanline_surf is None:
        _scanline_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 3):
            pygame.draw.line(_scanline_surf, (0, 0, 0, 18), (0, y), (SCREEN_W, y), 1)
    return _scanline_surf


_bg_cache = {}
_grid_cache = {}


def draw_background(surf, frame, level):
    if level not in _bg_cache:
        bg = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            c = lerp_color(DEEP_NAVY, (12, 4, 6), t)
            pygame.draw.line(bg, c, (0, y), (SCREEN_W, y))
        _bg_cache[level] = bg
    surf.blit(_bg_cache[level], (0, 0))

    grid_size = 48
    ox = int(frame * 0.18) % grid_size
    oy = int(frame * 0.09) % grid_size
    gc = (40, 10, 10) if level >= 3 else (25, 10, 12)
    play_w = PLAY_X2 - PLAY_X1
    play_h = PLAY_Y2 - PLAY_Y1
    for gx in range(-grid_size, play_w + grid_size, grid_size):
        pygame.draw.line(surf, gc, (PLAY_X1 + gx + ox, PLAY_Y1), (PLAY_X1 + gx + ox, PLAY_Y2), 1)
    for gy_val in range(-grid_size, play_h + grid_size, grid_size):
        pygame.draw.line(surf, gc, (PLAY_X1, PLAY_Y1 + gy_val + oy), (PLAY_X2, PLAY_Y1 + gy_val + oy), 1)

    if level < 4 or frame % 2 == 0:
        stars = make_stars()
        for st in stars:
            tw = abs(math.sin(frame * st['speed'] + st['twinkle']))
            a  = int(50 + tw * 140)
            r  = st['r'] * (0.6 + 0.4 * tw)
            sc = pygame.Surface((int(r * 4) + 2, int(r * 4) + 2), pygame.SRCALPHA)
            pygame.draw.circle(sc, (*st['color'], a), (int(r * 2) + 1, int(r * 2) + 1), max(1, int(r)))
            surf.blit(sc, (int(st['x']) - int(r * 2) - 1, int(st['y']) - int(r * 2) - 1))

    draw_walls(surf, level, frame)

    vg = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for i in range(0, 90, 12):
        a2 = int(80 * (i / 90) ** 2)
        pygame.draw.rect(vg, (0, 0, 0, a2), (PLAY_X1 + i, PLAY_Y1 + i,
            PLAY_X2 - PLAY_X1 - i * 2, PLAY_Y2 - PLAY_Y1 - i * 2), 6)
    surf.blit(vg, (0, 0))

    surf.blit(get_scanline_surf(), (0, 0))


def draw_walls(surf, level, frame):
    pulse = abs(math.sin(frame * 0.04))
    edge_col = lerp_color(WALL_EDGE, WALL_LIT, pulse * 0.6)

    for rect_params in [
        (0, 0, SCREEN_W, PLAY_Y1),
        (0, PLAY_Y2, SCREEN_W, SCREEN_H - PLAY_Y2),
        (0, PLAY_Y1, PLAY_X1, PLAY_Y2 - PLAY_Y1),
        (PLAY_X2, PLAY_Y1, WALL_THICKNESS, PLAY_Y2 - PLAY_Y1),
    ]:
        rx, ry, rw, rh = rect_params
        wall_s = pygame.Surface((rw, rh))
        wall_s.fill(WALL_COL)
        surf.blit(wall_s, (rx, ry))

    pygame.draw.rect(surf, edge_col, (PLAY_X1, PLAY_Y1, PLAY_X2 - PLAY_X1, PLAY_Y2 - PLAY_Y1), 2)

    for cx2, cy2 in [(PLAY_X1, PLAY_Y1), (PLAY_X2, PLAY_Y1),
                     (PLAY_X1, PLAY_Y2), (PLAY_X2, PLAY_Y2)]:
        glow_circle(surf, RED, cx2, cy2, 7, 2, 90)
        pygame.draw.circle(surf, RED, (cx2, cy2), 5)
        pygame.draw.circle(surf, WHITE, (cx2, cy2), 2)


def draw_cape(surf, cx, cy, scale, frame, move_dx=0, move_dy=0):
    s = scale
    wind = math.sin(frame * 0.12) * 0.3
    drift_x = -move_dx * 0.5 + wind * 8 * s
    drift_y = abs(move_dy) * 0.2 + math.sin(frame * 0.08) * 2 * s

    shoulder_l = (int(cx - 10 * s), int(cy + 6 * s))
    shoulder_r = (int(cx + 10 * s), int(cy + 6 * s))

    mid_x = cx + drift_x
    mid_y = cy + 28 * s + drift_y
    tip_l = (int(mid_x - 18 * s + drift_x * 0.3), int(cy + 46 * s + drift_y))
    tip_r = (int(mid_x + 18 * s - drift_x * 0.3), int(cy + 46 * s + drift_y))
    mid_l = (int(mid_x - 14 * s), int(mid_y))
    mid_r = (int(mid_x + 14 * s), int(mid_y))

    inner_pts = [
        shoulder_l, shoulder_r,
        (int(mid_x + 10 * s), int(cy + 26 * s + drift_y * 0.7)),
        (int(mid_x - 10 * s), int(cy + 26 * s + drift_y * 0.7)),
    ]
    if len(inner_pts) >= 3:
        pygame.draw.polygon(surf, CAPE_DARK, inner_pts)

    cape_pts = [shoulder_l, shoulder_r, mid_r, tip_r, tip_l, mid_l]
    if len(cape_pts) >= 3:
        pygame.draw.polygon(surf, CAPE_MID, cape_pts)

    shine_pts = [
        shoulder_l,
        (int(shoulder_l[0] - 2 * s), int(cy + 16 * s)),
        (int(mid_l[0] - 2 * s), int(mid_l[1])),
        (tip_l[0], tip_l[1]),
        mid_l,
    ]
    if len(shine_pts) >= 3:
        shine_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(shine_surf, (*CAPE_LIGHT, 120), shine_pts)
        surf.blit(shine_surf, (0, 0))


def draw_ethan(surf, cx, cy, scale=1.0, frame=0, health_ratio=1.0, missiles=0, move_dx=0, move_dy=0):
    s   = scale
    bob = math.sin(frame * 0.2) * 1.5 * s
    cy  = int(cy)
    cx  = int(cx)

    SKIN     = (195, 155, 115)
    SKIN_D   = (165, 128, 92)
    SUIT     = (15, 20, 40)
    SUIT_L   = (25, 35, 65)
    SUIT_A   = (8, 12, 28)
    HAIR     = (22, 16, 10)
    BOOT_COL = (8, 8, 14)

    sh = pygame.Surface((int(32 * s), int(9 * s)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surf.blit(sh, (cx - int(16 * s), cy + int(36 * s)))

    if missiles > 0:
        glow_circle(surf, GOLD, cx, cy + int(12 * s), int(24 * s), 3, 30)

    draw_cape(surf, cx, cy, s, frame, move_dx, move_dy)

    ls = math.sin(frame * 0.35) * 5 * s
    for ox, lv in [(-5, ls), (5, -ls)]:
        pygame.draw.rect(surf, SUIT, (int(cx + ox * s - 4 * s), int(cy + 21 * s + bob), int(8 * s), int(15 * s)), border_radius=2)
        pygame.draw.line(surf, SUIT_L, (int(cx + ox * s), int(cy + 21 * s + bob)), (int(cx + ox * s), int(cy + 34 * s + bob)), max(1, int(s)))
    for ox in [-5, 5]:
        pygame.draw.rect(surf, BOOT_COL, (int(cx + ox * s - 6 * s), int(cy + 35 * s + bob), int(12 * s), int(5 * s)), border_radius=2)

    body_r = pygame.Rect(int(cx - 10 * s), int(cy + 6 * s + bob), int(20 * s), int(17 * s))
    pygame.draw.rect(surf, SUIT, body_r, border_radius=int(3 * s))
    pygame.draw.rect(surf, SUIT_L, (int(cx - 9 * s), int(cy + 7 * s + bob), int(7 * s), int(6 * s)), border_radius=2)
    pygame.draw.rect(surf, SUIT_L, (int(cx + 2 * s), int(cy + 7 * s + bob), int(7 * s), int(6 * s)), border_radius=2)
    glow_circle(surf, CYAN, cx, int(cy + 11 * s + bob), max(1, int(3 * s)), 2, 60)
    pygame.draw.circle(surf, CYAN, (cx, int(cy + 11 * s + bob)), max(1, int(1.5 * s)))
    pygame.draw.rect(surf, SUIT_A, (int(cx - 10 * s), int(cy + 20 * s + bob), int(20 * s), int(3 * s)))
    pygame.draw.rect(surf, GOLD, (int(cx - 2 * s), int(cy + 20 * s + bob), int(4 * s), int(3 * s)))

    arm_sw = math.sin(frame * 0.35) * 6 * s
    for side, sw in [(-1, arm_sw), (1, -arm_sw)]:
        pygame.draw.line(surf, SUIT, (int(cx + side * 9 * s), int(cy + 8 * s + bob)), (int(cx + side * 16 * s), int(cy + 20 * s + bob + sw * 0.5)), max(1, int(5 * s)))
        pygame.draw.ellipse(surf, SUIT_A, (int(cx + side * 13 * s - 3 * s), int(cy + 18 * s + bob + sw * 0.5), int(7 * s), int(4 * s)))

    gx = int(cx + 16 * s)
    gy = int(cy + 19 * s + bob - arm_sw * 0.5)
    pygame.draw.rect(surf, (6, 8, 16), (gx, gy, int(10 * s), int(4 * s)), border_radius=1)
    pygame.draw.rect(surf, (28, 36, 60), (gx, gy, int(10 * s), int(2 * s)), border_radius=1)
    pygame.draw.rect(surf, GOLD, (gx + int(8 * s), gy + int(1 * s), int(3 * s), int(2 * s)))

    if missiles > 0:
        lx = int(cx - 17 * s)
        ly = int(cy + 18 * s + bob + arm_sw * 0.5)
        pygame.draw.rect(surf, (45, 30, 6), (lx - int(2 * s), ly, int(10 * s), int(4 * s)), border_radius=1)
        pygame.draw.circle(surf, GOLD, (lx + int(8 * s), ly + int(2 * s)), max(1, int(2 * s)))
        glow_circle(surf, GOLD, lx + int(8 * s), ly + int(2 * s), max(1, int(3 * s)), 2, 80)

    pygame.draw.rect(surf, SKIN_D, (int(cx - 3 * s), int(cy - 2 * s + bob), int(6 * s), int(8 * s)))
    pygame.draw.ellipse(surf, SKIN, (int(cx - 9 * s), int(cy - 14 * s + bob), int(18 * s), int(16 * s)))
    pygame.draw.ellipse(surf, HAIR, (int(cx - 9 * s), int(cy - 14 * s + bob), int(18 * s), int(7 * s)))
    pygame.draw.rect(surf, HAIR, (int(cx - 9 * s), int(cy - 12 * s + bob), int(18 * s), int(3 * s)))

    ey = int(cy - 4 * s + bob)
    for ex_off, pupil_off in [(-4, -0.3), (3, 0.3)]:
        pygame.draw.ellipse(surf, (240, 240, 245), (int(cx + ex_off * s - 2 * s), ey, int(5 * s), int(4 * s)))
        pygame.draw.circle(surf, (20, 35, 110), (int(cx + (ex_off + pupil_off * 2) * s), ey + int(2 * s)), max(1, int(1.5 * s)))

    for bside in [-1, 1]:
        pygame.draw.line(surf, HAIR, (int(cx + bside * 2 * s), int(cy - 7 * s + bob)), (int(cx + bside * 7 * s), int(cy - 9 * s + bob)), max(1, int(2 * s)))

    pygame.draw.circle(surf, CYAN, (int(cx + 9 * s), int(cy - 1 * s + bob)), max(1, int(2 * s)))
    glow_circle(surf, NEON_TEAL, int(cx + 9 * s), int(cy - 1 * s + bob), max(1, int(2 * s)), 2, 70)

    if health_ratio < 0.45:
        ov = pygame.Surface((int(30 * s), int(52 * s)), pygame.SRCALPHA)
        ov.fill((220, 0, 0, int(50 * (1 - health_ratio * 2))))
        surf.blit(ov, (int(cx - 15 * s), int(cy - 14 * s + bob)))


def draw_robot(surf, cx, cy, scale=1.0, frame=0, alert=False, hp_ratio=1.0):
    s   = scale
    bob = math.sin(frame * 0.26 + cx * 0.01) * 1.8 * s
    cx  = int(cx)
    cy  = int(cy)

    ec  = (200, 20, 20) if alert else (80, 80, 80)
    ec2 = (160, 0, 0)  if alert else (50, 50, 50)

    CHASSIS   = (28, 28, 35)
    CHASSIS_L = (44, 44, 52)
    CHASSIS_D = (18, 18, 24)
    JOINT     = (58, 58, 68)
    VISOR_BG  = (8, 0, 0) if alert else (5, 5, 8)

    leg_walk = math.sin(frame * 0.3) * 5 * s
    for ox, lw in [(-6, leg_walk), (6, -leg_walk)]:
        pygame.draw.rect(surf, CHASSIS, (int(cx + ox * s - 4 * s), int(cy + 18 * s + bob), int(8 * s), int(8 * s)), border_radius=2)
        pygame.draw.rect(surf, CHASSIS_D, (int(cx + ox * s - 3 * s), int(cy + 25 * s + bob), int(7 * s), int(7 * s)), border_radius=2)
        pygame.draw.rect(surf, (16, 16, 20), (int(cx + ox * s - 6 * s), int(cy + 31 * s + bob), int(12 * s), int(3 * s)), border_radius=2)

    t_rect = pygame.Rect(int(cx - 12 * s), int(cy + 2 * s + bob), int(24 * s), int(18 * s))
    pygame.draw.rect(surf, CHASSIS, t_rect, border_radius=int(3 * s))
    pygame.draw.rect(surf, CHASSIS_D, (int(cx - 7 * s), int(cy + 5 * s + bob), int(14 * s), int(10 * s)), border_radius=2)

    core_pulse = (math.sin(frame * 0.18) + 1) * 0.5
    core_r     = max(2, int((2.5 + core_pulse * 0.8) * s))
    core_col   = BRIGHT_RED if alert else lerp_color(GRAY, (80, 80, 90), core_pulse)
    pygame.draw.circle(surf, core_col, (cx, int(cy + 10 * s + bob)), core_r)

    arm_sw = math.sin(frame * 0.3) * 7 * s
    for side, sw in [(-1, arm_sw), (1, -arm_sw)]:
        pygame.draw.line(surf, CHASSIS, (int(cx + side * 11 * s), int(cy + 4 * s + bob)), (int(cx + side * 18 * s), int(cy + 13 * s + bob + sw * 0.4)), max(1, int(5 * s)))
        muzz_x = int(cx + side * 22 * s)
        muzz_y = int(cy + 14 * s + bob + sw * 0.4)
        pygame.draw.circle(surf, ec, (muzz_x, muzz_y), max(1, int(1.5 * s)))

    head_rect = pygame.Rect(int(cx - 10 * s), int(cy - 15 * s + bob), int(20 * s), int(17 * s))
    pygame.draw.rect(surf, CHASSIS_L, head_rect, border_radius=int(3 * s))

    visor_rect = pygame.Rect(int(cx - 8 * s), int(cy - 10 * s + bob), int(16 * s), max(2, int(4 * s)))
    pygame.draw.rect(surf, VISOR_BG, visor_rect, border_radius=2)
    for ex_off in [-4, 0, 4]:
        eye_col = lerp_color(ec2, ec, (math.sin(frame * 0.15 + ex_off) + 1) * 0.5)
        pygame.draw.circle(surf, eye_col, (int(cx + ex_off * s), int(cy - 8 * s + bob)), max(1, int(1.5 * s)))

    pygame.draw.line(surf, JOINT, (int(cx), int(cy - 15 * s + bob)), (int(cx - 3 * s), int(cy - 22 * s + bob)), max(1, int(2 * s)))
    pygame.draw.circle(surf, BRIGHT_RED if alert else GRAY, (int(cx - 3 * s), int(cy - 22 * s + bob)), max(1, int(2 * s)))


def draw_solomon(surf, cx, cy, scale=1.0, frame=0, hp_ratio=1.0, shielded=False, teleporting=False):
    s    = scale
    bob  = math.sin(frame * 0.16) * 1.8 * s
    rage = 1.0 - hp_ratio
    cx   = int(cx)
    cy   = int(cy)

    SUIT_W  = (210, 210, 218)
    SUIT_WD = (190, 190, 200)
    SUIT_WL = (225, 225, 235)
    SHIRT   = (10,  6,  14)
    HAIR_C  = (20,  15, 10)
    SHOE_C  = (12,  8,  8)
    SKIN_S  = (175, 140, 108)

    if teleporting:
        if (frame // 2) % 2 == 0:
            return

    if shielded:
        for r2, a2 in [(42, 80), (38, 120), (34, 160)]:
            shield_col = lerp_color(PURPLE, (200, 200, 255), abs(math.sin(frame * 0.1)))
            gs = pygame.Surface((int(r2 * s * 2 + 4), int(r2 * s * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*shield_col, a2), (int(r2 * s) + 2, int(r2 * s) + 2), int(r2 * s), 3)
            surf.blit(gs, (cx - int(r2 * s) - 2, cy - int(r2 * s) + int(14 * s) - 2))
    else:
        for r2, a2 in [(40, 12), (30, 22), (22, 38), (14, 60)]:
            aura_c = lerp_color(PURPLE, DARK_RED, rage)
            glow_circle(surf, aura_c, cx, int(cy + 14 * s), int(r2 * s), 2, int(a2 * (0.6 + rage * 1.4)))

    sh = pygame.Surface((int(34 * s), int(10 * s)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 100), sh.get_rect())
    surf.blit(sh, (int(cx - 17 * s), int(cy + 41 * s)))

    ls = math.sin(frame * 0.18) * 2 * s
    for ox, lv in [(-7, ls), (7, -ls)]:
        pygame.draw.rect(surf, SUIT_W, (int(cx + ox * s - 5 * s), int(cy + 22 * s + bob), int(10 * s), int(19 * s)), border_radius=2)
    for ox in [-7, 7]:
        pygame.draw.rect(surf, SHOE_C, (int(cx + ox * s - 7 * s), int(cy + 40 * s + bob), int(14 * s), int(4 * s)), border_radius=2)

    pygame.draw.rect(surf, SUIT_W, (int(cx - 13 * s), int(cy + 3 * s + bob), int(26 * s), int(21 * s)), border_radius=int(3 * s))
    pygame.draw.polygon(surf, SHIRT, [(int(cx - 2 * s), int(cy + 3 * s + bob)), (int(cx + 2 * s), int(cy + 3 * s + bob)), (int(cx + 2 * s), int(cy + 16 * s + bob)), (int(cx - 2 * s), int(cy + 16 * s + bob))])
    for side in [-1, 1]:
        pygame.draw.polygon(surf, SUIT_WL, [(int(cx + side * 2 * s), int(cy + 3 * s + bob)), (int(cx + side * 13 * s), int(cy + 3 * s + bob)), (int(cx + side * 8 * s), int(cy + 15 * s + bob)), (int(cx + side * 2 * s), int(cy + 11 * s + bob))])
    blood_pulse = lerp_color(CRIMSON, RED, abs(math.sin(frame * 0.08)) * rage + 0.2)
    pygame.draw.rect(surf, blood_pulse, (int(cx - 9 * s), int(cy + 6 * s + bob), int(5 * s), int(4 * s)))

    arm_sw = math.sin(frame * 0.16) * 4 * s
    for side, sw in [(-1, arm_sw), (1, -arm_sw)]:
        pygame.draw.rect(surf, SUIT_W, (int(cx + side * 11 * s), int(cy + 3 * s + bob + sw * 0.3), int(10 * s), int(16 * s)), border_radius=3)
        pygame.draw.rect(surf, SHIRT, (int(cx + side * 11 * s), int(cy + 17 * s + bob + sw * 0.3), int(10 * s), int(5 * s)), border_radius=2)

    pygame.draw.rect(surf, SKIN_S, (int(cx - 3 * s), int(cy - 4 * s + bob), int(6 * s), int(8 * s)))
    pygame.draw.ellipse(surf, (178, 145, 112), (int(cx - 11 * s), int(cy - 17 * s + bob), int(22 * s), int(20 * s)))
    pygame.draw.ellipse(surf, HAIR_C, (int(cx - 11 * s), int(cy - 17 * s + bob), int(22 * s), int(9 * s)))
    pygame.draw.rect(surf, HAIR_C, (int(cx - 11 * s), int(cy - 13 * s + bob), int(22 * s), int(4 * s)))

    eye_y = int(cy - 6 * s + bob)
    rage_eye = lerp_color((60, 20, 100), (220, 0, 20), rage)
    for ex_off in [-4, 4]:
        pygame.draw.ellipse(surf, (230, 225, 232), (int(cx + ex_off * s - 3 * s), eye_y, int(7 * s), int(5 * s)))
        pygame.draw.circle(surf, rage_eye, (int(cx + ex_off * s), eye_y + int(2 * s)), max(1, int(2 * s)))
        if shielded:
            glow_circle(surf, PURPLE, int(cx + ex_off * s), eye_y + int(2 * s), max(1, int(3 * s)), 2, 120)
        pygame.draw.circle(surf, WHITE, (int(cx + ex_off * s) + 1, eye_y + int(s)), max(1, int(0.7 * s)))

    for side in [-1, 1]:
        pygame.draw.line(surf, HAIR_C, (int(cx + side * 2 * s), int(cy - 9 * s + bob)), (int(cx + side * 9 * s), int(cy - 12 * s + bob)), max(1, int(2 * s)))

    mouth_col = lerp_color((85, 45, 45), (200, 10, 10), rage)
    pygame.draw.line(surf, mouth_col, (int(cx - 6 * s), int(cy + bob)), (int(cx + 6 * s), int(cy + bob)), max(1, int(2 * s)))
    pygame.draw.polygon(surf, HAIR_C, [(int(cx - 4 * s), int(cy + bob)), (int(cx + 4 * s), int(cy + bob)), (int(cx), int(cy + 7 * s + bob))])


def draw_custom_cursor(surf, cx, cy, frame, has_missile=False, is_shooting=False):
    cx, cy = int(cx), int(cy)
    pulse = abs(math.sin(frame * 0.1))
    outer_r = 16 + int(pulse * 3)

    if is_shooting:
        col = NEON_PINK
        inner_col = WHITE
    elif has_missile:
        col = AMBER
        inner_col = GOLD
    else:
        col = CYAN
        inner_col = (200, 240, 255)

    glow_circle(surf, col, cx, cy, outer_r + 4, 2, 30)

    gap = 6
    length = 11
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        x1 = cx + int(math.cos(rad) * gap)
        y1 = cy + int(math.sin(rad) * gap)
        x2 = cx + int(math.cos(rad) * (gap + length))
        y2 = cy + int(math.sin(rad) * (gap + length))
        pygame.draw.line(surf, col, (x1, y1), (x2, y2), 2)

    for i in range(0, 360, 30):
        if (i // 30) % 2 == 0:
            rad = math.radians(i)
            px = cx + int(math.cos(rad) * outer_r)
            py = cy + int(math.sin(rad) * outer_r)
            pygame.draw.circle(surf, col, (px, py), 1)

    pygame.draw.circle(surf, inner_col, (cx, cy), 2)

    for i in range(4):
        angle = frame * 0.05 + i * math.pi / 2
        px2 = cx + int(math.cos(angle) * 8)
        py2 = cy + int(math.sin(angle) * 8)
        pygame.draw.circle(surf, (*col, 180), (px2, py2), 2)


class Bullet:
    SPEED = 11

    def __init__(self, x, y, dx, dy, color=GOLD, is_enemy=False):
        self.x, self.y = float(x), float(y)
        ln = max(0.001, math.hypot(dx, dy))
        self.dx = dx / ln * self.SPEED
        self.dy = dy / ln * self.SPEED
        self.alive    = True
        self.age      = 0
        self.color    = color
        self.is_enemy = is_enemy
        self.trail    = []

    def update(self, obstacles=None):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.x += self.dx
        self.y += self.dy
        self.age += 1
        if self.age > 120 or not (PLAY_X1 < self.x < PLAY_X2) or not (PLAY_Y1 < self.y < PLAY_Y2):
            self.alive = False
        if obstacles:
            for obs in obstacles:
                if obs.rect.collidepoint(self.x, self.y):
                    self.alive = False
                    break

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            a = int(160 * (i / max(1, len(self.trail))))
            r = max(1, int(2 * (i / max(1, len(self.trail)))))
            ts = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*self.color[:3], a), (r, r), r)
            surf.blit(ts, (int(tx) - r, int(ty) - r))
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 3)

    @property
    def rect(self):
        return pygame.Rect(self.x - 5, self.y - 5, 10, 10)


class GuidedMissile:
    SPEED      = 6.5
    TURN_SPEED = 0.09

    def __init__(self, x, y, dx, dy, targets):
        self.x, self.y = float(x), float(y)
        ln = max(0.001, math.hypot(dx, dy))
        self.angle   = math.atan2(dy / ln, dx / ln)
        self.speed   = self.SPEED
        self.alive   = True
        self.age     = 0
        self.targets = targets
        self.target  = None
        self.trail   = []
        self.smoke   = []

    def _find_target(self):
        best, bd = None, 9999
        for t in self.targets:
            alive = getattr(t, 'alive', True)
            if not alive:
                continue
            d = math.hypot(self.x - t.x, self.y - t.y)
            if d < bd:
                best, bd = t, d
        return best

    def update(self):
        self.age += 1
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        if self.age % 3 == 0:
            self.smoke.append({'x': self.x, 'y': self.y, 'vx': random.uniform(-0.4, 0.4), 'vy': random.uniform(-0.4, 0.4), 'life': 0.7, 'size': random.randint(2, 4)})
        for sp in self.smoke[:]:
            sp['x'] += sp['vx']
            sp['y'] += sp['vy']
            sp['life'] -= 0.05
            if sp['life'] <= 0:
                self.smoke.remove(sp)
        if self.age > 10:
            if not self.target or not getattr(self.target, 'alive', True):
                self.target = self._find_target()
            if self.target:
                desired = math.atan2(self.target.y - self.y, self.target.x - self.x)
                diff    = (desired - self.angle + math.pi) % (2 * math.pi) - math.pi
                self.angle += diff * self.TURN_SPEED
                self.speed  = min(10, self.speed + 0.08)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if self.age > 220 or not (PLAY_X1 < self.x < PLAY_X2) or not (PLAY_Y1 < self.y < PLAY_Y2):
            self.alive = False

    def draw(self, surf):
        for sp in self.smoke:
            a2 = int(sp['life'] * 80)
            ss = pygame.Surface((sp['size'] * 2, sp['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (160, 100, 50, a2), (sp['size'], sp['size']), sp['size'])
            surf.blit(ss, (int(sp['x']) - sp['size'], int(sp['y']) - sp['size']))
        for i, (tx, ty) in enumerate(self.trail):
            t2 = i / max(1, len(self.trail))
            a2 = int(200 * t2)
            r2 = max(1, int(3 * t2))
            tc = lerp_color(ORANGE, AMBER, t2)
            ts = pygame.Surface((r2 * 2, r2 * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*tc, a2), (r2, r2), r2)
            surf.blit(ts, (int(tx) - r2, int(ty) - r2))
        bx, by = int(self.x), int(self.y)
        nx = bx + int(math.cos(self.angle) * 9)
        ny = by + int(math.sin(self.angle) * 9)
        perp = self.angle + math.pi / 2
        f1x  = bx + int(math.cos(perp) * 5 - math.cos(self.angle) * 7)
        f1y  = by + int(math.sin(perp) * 5 - math.sin(self.angle) * 7)
        f2x  = bx - int(math.cos(perp) * 5 - math.cos(self.angle) * 7)
        f2y  = by - int(math.sin(perp) * 5 - math.sin(self.angle) * 7)
        glow_circle(surf, AMBER, bx, by, 8, 2, 80)
        pygame.draw.polygon(surf, ORANGE, [(nx, ny), (f1x, f1y), (f2x, f2y)])
        pygame.draw.circle(surf, WHITE, (nx, ny), 2)

    @property
    def rect(self):
        return pygame.Rect(self.x - 10, self.y - 10, 20, 20)


class Obstacle:
    def __init__(self, x, y, w, h, level=1):
        self.rect  = pygame.Rect(x, y, w, h)
        self.level = level
        self.hp    = 4
        self.max_hp= 4
        self._crack_seed = random.randint(0, 9999)

    def draw(self, surf, frame):
        x, y, w, h = self.rect.x, self.rect.y, self.rect.width, self.rect.height
        hp_ratio = self.hp / self.max_hp

        THEMES = {
            1: {'base': (18, 6, 6),   'mid': (32, 10, 10), 'edge': (120, 25, 25), 'core': DARK_RED},
            2: {'base': (12, 6, 22),  'mid': (20, 10, 36), 'edge': (90, 25, 160), 'core': PURPLE},
            3: {'base': (28, 5, 5),   'mid': (48, 9, 9),   'edge': (190, 35, 35), 'core': RED},
            4: {'base': (6, 18, 8),   'mid': (10, 32, 13), 'edge': (30, 160, 65), 'core': GREEN},
            5: {'base': (28, 13, 3),  'mid': (48, 22, 5),  'edge': (210, 110, 18),'core': ORANGE},
        }
        th = THEMES.get(self.level, THEMES[1])

        for i in range(h):
            ratio = i / max(h, 1)
            c = lerp_color(th['mid'], th['base'], ratio)
            pygame.draw.line(surf, c, (x, y + i), (x + w, y + i))

        pulse = abs(math.sin(frame * 0.06)) * hp_ratio
        border_col = lerp_color(th['edge'], lerp_color(th['edge'], WHITE, 0.3), pulse * 0.4)
        pygame.draw.rect(surf, border_col, self.rect, 2, border_radius=3)

        for corner in [(x + 3, y + 3), (x + w - 5, y + 3), (x + 3, y + h - 5), (x + w - 5, y + h - 5)]:
            pygame.draw.circle(surf, th['edge'], corner, 3)

        if hp_ratio < 0.4:
            warn_a = int(abs(math.sin(frame * 0.18)) * 60)
            ws = pygame.Surface((w, h), pygame.SRCALPHA)
            ws.fill((*RED, warn_a))
            surf.blit(ws, (x, y))

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    @property
    def alive(self):
        return self.hp > 0


class Enemy:
    BASE_SPEED    = 1.9
    MIN_CHASE_DIST= 80
    MAX_CHASE_DIST= 360

    def __init__(self, x, y, patrol_range=110, level=1):
        self.x, self.y   = float(x), float(y)
        self.sx, self.sy  = float(x), float(y)
        self.hp           = 3 + level
        self.max_hp       = self.hp
        self.alive        = True
        self.frame        = 0
        self.dir          = random.choice([-1, 1])
        self.patrol_range = patrol_range
        self.alert        = False
        self.alert_timer  = 0
        self.shoot_cd     = 0
        self.bullets      = []
        self.level        = level
        self.death_anim   = 0

    @property
    def rect(self):
        return pygame.Rect(self.x - 14, self.y - 18, 28, 38)

    def update(self, player_rect, obstacles, dt):
        if not self.alive:
            return
        self.frame    += 1
        self.shoot_cd  = max(0, self.shoot_cd - 1)
        if self.alert_timer > 0:
            self.alert_timer -= 1
            if self.alert_timer == 0:
                self.alert = False

        px, py = player_rect.centerx, player_rect.centery
        dist   = math.hypot(self.x - px, self.y - py)
        speed  = self.BASE_SPEED + self.level * 0.18

        if dist < self.MAX_CHASE_DIST:
            self.alert       = True
            self.alert_timer = 100
            if dist > self.MIN_CHASE_DIST:
                angle = math.atan2(py - self.y, px - self.x)
                nx = self.x + math.cos(angle) * speed * 1.5
                ny = self.y + math.sin(angle) * speed * 1.5
                nr = pygame.Rect(nx - 14, ny - 18, 28, 38)
                if not any(nr.colliderect(o.rect) for o in obstacles if o.alive):
                    self.x, self.y = nx, ny
            if dist < 360 and self.shoot_cd == 0:
                interval = max(50, 90 - self.level * 8)
                self.shoot_cd = interval
                spread = 0.12 * self.level
                offsets = [-spread, 0, spread] if self.level >= 3 else [0]
                for a_off in offsets:
                    angle2 = math.atan2(py - self.y, px - self.x) + a_off
                    self.bullets.append(Bullet(self.x, self.y, math.cos(angle2) * 5, math.sin(angle2) * 5, DARK_RED, is_enemy=True))
        else:
            nx = self.x + self.dir * speed
            ny = self.y
            nr = pygame.Rect(nx - 14, ny - 18, 28, 38)
            if not any(nr.colliderect(o.rect) for o in obstacles if o.alive):
                self.x = nx
            if abs(self.x - self.sx) > self.patrol_range:
                self.dir *= -1

        self.x = max(PLAY_X1 + 15, min(PLAY_X2 - 15, self.x))
        self.y = max(PLAY_Y1 + 20, min(PLAY_Y2 - 20, self.y))

        for b in self.bullets[:]:
            b.update(obstacles)
            if not b.alive:
                self.bullets.remove(b)

    def draw(self, surf):
        if not self.alive:
            return
        hp_r = self.hp / self.max_hp
        bar_w = 36
        bx, by = int(self.x) - 18, int(self.y) - 44
        pygame.draw.rect(surf, (25, 8, 8), (bx, by, bar_w, 4), border_radius=2)
        col = lerp_color(BRIGHT_RED, AMBER, hp_r)
        pygame.draw.rect(surf, col, (bx, by, max(0, int(bar_w * hp_r)), 4), border_radius=2)
        draw_robot(surf, int(self.x), int(self.y), 1.0, self.frame, self.alert, hp_r)
        for b in self.bullets:
            b.draw(surf)

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
            return True
        return False


class Boss:
    
    ABILITY_COOLDOWN = 420   
    SHIELD_DURATION  = 180   
    TELEPORT_FLASH   = 40    

    def __init__(self, x, y):
        self.x, self.y   = float(x), float(y)
        self.hp           = 20
        self.max_hp       = 20
        self.alive        = True
        self.frame        = 0
        self.shoot_cd     = 0
        self.move_angle   = 0
        self.bullets      = []
        self.phase        = 1

        self.ability_cd       = 180   
        self.shielded         = False
        self.shield_timer     = 0
        self.teleport_timer   = 0
        self.last_ability     = ''
        self.afterimages      = []   
        self.nova_warning     = 0    
        self.ability_floater  = None 

    @property
    def rect(self):
        return pygame.Rect(self.x - 20, self.y - 24, 40, 50)

    def _trigger_ability(self, player_rect):
        px, py = player_rect.centerx, player_rect.centery

        options = ['shield', 'teleport', 'nova']
        if self.phase == 2:
            options.append('nova') 
        choices = [a for a in options if a != self.last_ability]
        ability = random.choice(choices)
        self.last_ability = ability

        if ability == 'shield':
            self.shielded     = True
            self.shield_timer = self.SHIELD_DURATION
            play('boss_shield')
            self.ability_floater = {'text': '⬡ SHIELD ACTIVATED', 'x': self.x, 'y': self.y - 60,
                                     'life': 1.8, 'color': (180, 100, 255)}

        elif ability == 'teleport':
            self.afterimages.append({'x': self.x, 'y': self.y, 'alpha': 200, 'frame': self.frame})
            for _ in range(20):
                nx = random.randint(PLAY_X1 + 80, PLAY_X2 - 80)
                ny = random.randint(PLAY_Y1 + 80, PLAY_Y2 - 80)
                if math.hypot(nx - px, ny - py) > 150:
                    self.x, self.y = float(nx), float(ny)
                    break
            self.teleport_timer = self.TELEPORT_FLASH
            play('boss_teleport')
            self.ability_floater = {'text': '⬢ PHASE SHIFT', 'x': self.x, 'y': self.y - 60,
                                     'life': 1.5, 'color': NEON_TEAL}

        elif ability == 'nova':
            self.nova_warning = 30
            play('boss_ability')
            self.ability_floater = {'text': '✦ SYNDICATE NOVA', 'x': self.x, 'y': self.y - 60,
                                     'life': 2.0, 'color': (255, 60, 60)}

    def _fire_nova(self):
        count = 12 if self.phase == 1 else 18
        for i in range(count):
            angle = i * (2 * math.pi / count)
            spd = 4.5
            self.bullets.append(Bullet(self.x, self.y, math.cos(angle) * spd, math.sin(angle) * spd, PURPLE, is_enemy=True))

    def update(self, player_rect, dt):
        if not self.alive:
            return
        self.frame    += 1
        self.shoot_cd  = max(0, self.shoot_cd - 1)
        self.ability_cd = max(0, self.ability_cd - 1)
        px, py         = player_rect.centerx, player_rect.centery
        self.phase     = 1 if self.hp > self.max_hp * 0.5 else 2

        if self.shielded:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shielded = False

        if self.teleport_timer > 0:
            self.teleport_timer -= 1

        if self.nova_warning > 0:
            self.nova_warning -= 1
            if self.nova_warning == 0:
                self._fire_nova()

        for ai in self.afterimages[:]:
            ai['alpha'] -= 6
            if ai['alpha'] <= 0:
                self.afterimages.remove(ai)

        if self.ability_floater:
            self.ability_floater['y'] -= 0.8
            self.ability_floater['life'] -= dt * 1.2
            if self.ability_floater['life'] <= 0:
                self.ability_floater = None

        if self.ability_cd == 0:
            self._trigger_ability(player_rect)
            cd_base = self.ABILITY_COOLDOWN if self.phase == 1 else 280
            self.ability_cd = cd_base + random.randint(-60, 60)

        spd = 0.020 * (1.7 if self.phase == 2 else 1.0)
        self.move_angle += spd
        orb = 140 if self.phase == 1 else 100
        tx  = px + math.cos(self.move_angle) * orb
        ty  = py + math.sin(self.move_angle) * orb
        self.x += (tx - self.x) * 0.055
        self.y += (ty - self.y) * 0.055
        self.x  = max(PLAY_X1 + 60, min(PLAY_X2 - 60, self.x))
        self.y  = max(PLAY_Y1 + 60, min(PLAY_Y2 - 60, self.y))

        interval = 28 if self.phase == 2 else 52
        if self.shoot_cd == 0 and self.nova_warning == 0:
            self.shoot_cd = interval
            base  = math.atan2(py - self.y, px - self.x)
            count = 7 if self.phase == 2 else 3
            for i in range(count):
                spread = (i - count // 2) * 0.25
                a2 = base + spread
                self.bullets.append(Bullet(self.x, self.y, math.cos(a2) * 5.5, math.sin(a2) * 5.5, PURPLE, is_enemy=True))

        for b in self.bullets[:]:
            b.update()
            if not b.alive:
                self.bullets.remove(b)

    def draw(self, surf):
        if not self.alive:
            return

        for ai in self.afterimages:
            gs = pygame.Surface((80, 100), pygame.SRCALPHA)
            gs.fill((140, 60, 255, min(80, ai['alpha'] // 3)))
            surf.blit(gs, (int(ai['x']) - 40, int(ai['y']) - 30))
            pygame.draw.ellipse(surf, (*PURPLE, min(120, ai['alpha'])),
                                (int(ai['x']) - 20, int(ai['y']) - 20, 40, 50), 2)

        if self.nova_warning > 0:
            warn_frac = self.nova_warning / 30
            for r2 in range(20, 100, 18):
                wa = int(warn_frac * 80)
                ws = pygame.Surface((r2 * 2 + 4, r2 * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ws, (255, 40, 40, wa), (r2 + 2, r2 + 2), r2, 3)
                surf.blit(ws, (int(self.x) - r2 - 2, int(self.y) - r2 - 2))

        hp_r = self.hp / self.max_hp
        bw = 80
        bx = int(self.x) - 40
        by = int(self.y) - 66

        glow_s = pygame.Surface((bw + 10, 15), pygame.SRCALPHA)
        glow_s.fill((*DEEP_RED, 38))
        surf.blit(glow_s, (bx - 5, by - 4))
        pygame.draw.rect(surf, (20, 8, 8), (bx, by, bw, 11), border_radius=5)
        col = lerp_color(DARK_RED, CRIMSON, 1 - hp_r)
        if int(bw * hp_r) > 0:
            pygame.draw.rect(surf, col, (bx, by, int(bw * hp_r), 11), border_radius=5)
        pygame.draw.rect(surf, RED, (bx, by, bw, 11), 1, border_radius=5)

        if self.shielded:
            shield_frac = self.shield_timer / self.SHIELD_DURATION
            sw = int(bw * shield_frac)
            if sw > 0:
                pygame.draw.rect(surf, PURPLE, (bx, by, sw, 11), border_radius=5)
            lbl2 = FONTS['micro'].render("■ SHIELDED", True, (200, 150, 255))
            surf.blit(lbl2, lbl2.get_rect(center=(int(self.x), by - 20)))

        lbl = FONTS['micro'].render("SOLOMON LANE", True, RED)
        surf.blit(lbl, lbl.get_rect(center=(int(self.x), by - 10)))

        draw_solomon(surf, int(self.x), int(self.y), 1.3, self.frame, hp_r,
                     shielded=self.shielded, teleporting=self.teleport_timer > 0)

        if self.ability_floater:
            fl = self.ability_floater
            a = min(255, int(fl['life'] * 180))
            ft = FONTS['small'].render(fl['text'], True, fl['color'])
            fs = pygame.Surface((ft.get_width(), ft.get_height()), pygame.SRCALPHA)
            fs.blit(ft, (0, 0))
            fs.set_alpha(a)
            surf.blit(fs, fs.get_rect(center=(int(fl['x']), int(fl['y']))))

        for b in self.bullets:
            b.draw(surf)

    def hit(self):
        if self.shielded:
            self.shield_timer = max(0, self.shield_timer - 20)
            if self.shield_timer <= 0:
                self.shielded = False
            play('boss_shield')
            return False   # no damage
        self.hp -= 1
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
            return True
        return False


class Player:
    SPEED = 5.5

    def __init__(self, x, y):
        self.x, self.y    = float(x), float(y)
        self.hp            = 10
        self.max_hp        = 10
        self.alive         = True
        self.frame         = 0
        self.bullets       = []
        self.missiles      = []
        self.shoot_cd      = 0
        self.invincible    = 0
        self.score         = 0
        self.hit_streak    = 0
        self.missile_count = 0
        self.hit_flash     = 0
        self.move_dx       = 0.0
        self.move_dy       = 0.0

    @property
    def rect(self):
        return pygame.Rect(self.x - 13, self.y - 22, 26, 46)

    def update(self, keys, obstacles, dt):
        self.frame     += 1
        self.shoot_cd   = max(0, self.shoot_cd - 1)
        self.invincible = max(0, self.invincible - 1)
        self.hit_flash  = max(0, self.hit_flash - 1)

        dx, dy = 0, 0
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= self.SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += self.SPEED
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.SPEED
        if dx and dy:
            dx *= 0.707
            dy *= 0.707

        self.move_dx = dx
        self.move_dy = dy

        nx, ny = self.x + dx, self.y + dy
        nx = max(PLAY_X1 + 14, min(PLAY_X2 - 14, nx))
        ny = max(PLAY_Y1 + 24, min(PLAY_Y2 - 24, ny))
        tr = pygame.Rect(nx - 13, ny - 22, 26, 46)
        if not any(tr.colliderect(o.rect) for o in obstacles if o.alive):
            self.x, self.y = nx, ny

        for b in self.bullets[:]:
            b.update(obstacles)
            if not b.alive:
                self.bullets.remove(b)
        for m in self.missiles[:]:
            m.update()
            if not m.alive:
                self.missiles.remove(m)

    def shoot(self, tx, ty, enemies, boss):
        if self.shoot_cd > 0:
            return
        self.shoot_cd = 6
        dx, dy = tx - self.x, ty - self.y
        length = math.hypot(dx, dy)
        if length > 0:
            self.bullets.append(Bullet(self.x, self.y, dx, dy, AMBER))
            play('shoot')

    def launch_missile(self, enemies, boss):
        if self.missile_count <= 0:
            return
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        if not targets:
            return
        self.missile_count -= 1
        dx = random.uniform(-1, 1)
        dy = -1
        m = GuidedMissile(self.x, self.y - 10, dx, dy, targets)
        self.missiles.append(m)
        play('missile')

    def register_hit(self):
        """Returns True if milestone reached (every 3 hits = +1 missile)."""
        self.hit_streak += 1
        if self.hit_streak >= 3:
            self.hit_streak    = 0
            self.missile_count = min(5, self.missile_count + 1)
            play('powerup')
            return True
        return False

    def take_damage(self, amt=1):
        if self.invincible > 0:
            return False
        self.hp         -= amt
        self.invincible  = 65
        self.hit_flash   = 14
        self.hit_streak  = 0   
        if self.hp <= 0:
            self.alive = False
        return True

    def draw(self, surf):
        if self.invincible > 0 and (self.invincible // 6) % 2 == 0:
            return
        draw_ethan(surf, int(self.x), int(self.y - 14), 1.0, self.frame,
                   self.hp / self.max_hp, self.missile_count,
                   self.move_dx, self.move_dy)
        for b in self.bullets:
            b.draw(surf)
        for m in self.missiles:
            m.draw(surf)


def draw_exit_portal(surf, cx, cy, frame, locked=False):
    col  = GRAY if locked else RED
    col2 = MID_GRAY if locked else DARK_RED
    r    = 26
    for i in range(3):
        ri = r + i * 6 + int(math.sin(frame * 0.07 + i) * 2)
        a  = max(0, int((75 - i * 16) * (0.25 if locked else 1.0)))
        gs = pygame.Surface((ri * 2 + 4, ri * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col[:3], a), (ri + 2, ri + 2), ri, 2)
        surf.blit(gs, (cx - ri - 2, cy - ri - 2))
    if not locked:
        for i in range(10):
            angle = frame * 0.06 + i * math.pi * 2 / 10
            px2   = cx + math.cos(angle) * r
            py2   = cy + math.sin(angle) * r
            pygame.draw.circle(surf, col, (int(px2), int(py2)), 3)
    glow_circle(surf, col2, cx, cy, r // 2, 2, 80 if not locked else 18)
    pygame.draw.circle(surf, WHITE if not locked else GRAY, (cx, cy), 10)
    pygame.draw.circle(surf, col, (cx, cy), 10, 2)
    lbl = FONTS['tiny'].render("LOCKED" if locked else "EXIT", True, col)
    surf.blit(lbl, lbl.get_rect(center=(cx, cy + r + 16)))


def draw_hud(surf, player, level, enemies_left, has_boss, boss=None, frame=0):
    hud_s = pygame.Surface((SCREEN_W, 66), pygame.SRCALPHA)
    hud_s.fill((4, 2, 2, 220))
    surf.blit(hud_s, (0, 0))
    pygame.draw.line(surf, DARK_RED, (0, 66), (SCREEN_W, 66), 1)
    pygame.draw.line(surf, CRIMSON, (0, 68), (SCREEN_W, 68), 1)

    draw_text_left(surf, "HP", FONTS['small'], GRAY, 14, 22)
    bx, by, bw, bh = 40, 22, 170, 14
    pygame.draw.rect(surf, (20, 6, 6), (bx, by, bw, bh), border_radius=7)
    hp_r   = player.hp / player.max_hp
    hp_col = lerp_color(RED, AMBER, hp_r)
    fw     = max(0, int(bw * hp_r))
    if fw > 0:
        pygame.draw.rect(surf, hp_col, (bx, by, fw, bh), border_radius=7)
    pygame.draw.rect(surf, hp_col, (bx, by, bw, bh), 1, border_radius=7)
    hp_txt = FONTS['tiny'].render(f"{player.hp}/{player.max_hp}", True, WHITE)
    surf.blit(hp_txt, hp_txt.get_rect(center=(bx + bw // 2, by + bh // 2)))

    lname = LEVEL_DATA[level]['name']
    draw_text_centered(surf, f"LVL {level}  ·  {lname}", FONTS['small'], RED, SCREEN_W // 2, 33, glow_col=DARK_RED)

    draw_text_left(surf, "SCORE", FONTS['tiny'], GRAY, SCREEN_W - 210, 14)
    draw_text_left(surf, f"{player.score:06d}", FONTS['med'], AMBER, SCREEN_W - 210, 30)

    draw_text_left(surf, "HOSTILES", FONTS['tiny'], GRAY, SCREEN_W - 360, 14)
    draw_text_left(surf, str(enemies_left), FONTS['med'], RED if enemies_left > 0 else GREEN, SCREEN_W - 360, 30)

    mis_x = 228
    draw_text_left(surf, "MISSILES", FONTS['tiny'], GRAY, mis_x, 14)
    for mi in range(5):
        mx2    = mis_x + mi * 20
        filled = mi < player.missile_count
        col_m  = AMBER if filled else (30, 12, 12)
        pygame.draw.polygon(surf, col_m, [(mx2 + 4, 28), (mx2 + 7, 36), (mx2 + 11, 28), (mx2 + 7, 24)])
        if filled:
            glow_circle(surf, AMBER, mx2 + 7, 30, 5, 2, 50)

    streak_x = 370
    draw_text_left(surf, "STREAK", FONTS['tiny'], GRAY, streak_x, 14)
    for si in range(3):
        filled = si < player.hit_streak
        sx2    = streak_x + si * 17
        col_s  = lerp_color(ORANGE, AMBER, si / 2) if filled else (30, 10, 10)
        pygame.draw.circle(surf, col_s, (sx2 + 7, 32), 5)
        if filled:
            glow_circle(surf, col_s, sx2 + 7, 32, 5, 1, 60)

    hint = FONTS['micro'].render("WASD: move  |  MOUSE: aim & fire  |  SPACE/R: missile (earn per 3 hits)  |  ESC: quit", True, (55, 22, 22))
    surf.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 10)))

    if has_boss and boss and boss.alive:
        bbw = 480
        bbx = (SCREEN_W - bbw) // 2
        bby = SCREEN_H - 46

        bot_s = pygame.Surface((SCREEN_W, 48), pygame.SRCALPHA)
        bot_s.fill((4, 2, 2, 220))
        surf.blit(bot_s, (0, SCREEN_H - 48))
        pygame.draw.line(surf, DARK_RED, (0, SCREEN_H - 48), (SCREEN_W, SCREEN_H - 48), 1)

        br   = boss.hp / boss.max_hp
        bcol = lerp_color(DARK_RED, RED, 1 - br)
        draw_text_centered(surf, "SOLOMON LANE", FONTS['small'], RED, SCREEN_W // 2, bby - 10, glow_col=BLOOD)
        pygame.draw.rect(surf, (20, 6, 6), (bbx, bby, bbw, 12), border_radius=6)
        if int(bbw * br) > 0:
            pygame.draw.rect(surf, bcol, (bbx, bby, int(bbw * br), 12), border_radius=6)
        if boss.shielded:
            sf = boss.shield_timer / boss.SHIELD_DURATION
            pygame.draw.rect(surf, PURPLE, (bbx, bby, int(bbw * sf), 12), border_radius=6)
        pygame.draw.rect(surf, RED, (bbx, bby, bbw, 12), 1, border_radius=6)
        phase_lbl = FONTS['micro'].render(f"PHASE {'II — ENRAGED' if boss.phase == 2 else 'I'}  |  " +
                                          ('■ SHIELDED' if boss.shielded else ''), True,
                                          RED if boss.phase == 2 else ORANGE)
        surf.blit(phase_lbl, phase_lbl.get_rect(center=(SCREEN_W // 2, bby + 20)))

    if player.hit_flash > 0:
        fl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fl.fill((200, 0, 0, int(player.hit_flash * 8)))
        surf.blit(fl, (0, 0))


LEVEL_DATA = {
    1: {'enemies': 2, 'boss': False, 'obstacles': 5,  'name': "AGENCY BREACH"},
    2: {'enemies': 3, 'boss': False, 'obstacles': 7,  'name': "ROGUE NATION"},
    3: {'enemies': 4, 'boss': False, 'obstacles': 9,  'name': "GHOST PROTOCOL"},
    4: {'enemies': 5, 'boss': False, 'obstacles': 11, 'name': "DEAD RECKONING"},
    5: {'enemies': 3, 'boss': True,  'obstacles': 7,  'name': "FINAL RECKONING"},
}


def make_level(level):
    cfg = LEVEL_DATA[level]
    obstacles, enemies = [], []
    boss = None
    cx0  = (PLAY_X1 + PLAY_X2) // 2
    cy0  = (PLAY_Y1 + PLAY_Y2) // 2
    safe = pygame.Rect(cx0 - 120, cy0 - 120, 240, 240)

    attempts = 0
    while len(obstacles) < cfg['obstacles'] and attempts < 800:
        attempts += 1
        w = random.randint(65, 140)
        h = random.randint(20, 40)
        x = random.randint(PLAY_X1 + 30, PLAY_X2 - w - 30)
        y = random.randint(PLAY_Y1 + 30, PLAY_Y2 - h - 30)
        r = pygame.Rect(x, y, w, h)
        if not r.colliderect(safe) and not any(r.inflate(22, 22).colliderect(o.rect) for o in obstacles):
            obstacles.append(Obstacle(x, y, w, h, level))

    ex_x = random.randint(PLAY_X1 + 80, PLAY_X2 - 80)
    ex_y = random.randint(PLAY_Y1 + 50, PLAY_Y1 + 140)
    exit_pos = (ex_x, ex_y)

    attempts = 0
    while len(enemies) < cfg['enemies'] and attempts < 800:
        attempts += 1
        ex2 = random.randint(PLAY_X1 + 50, PLAY_X2 - 50)
        ey2 = random.randint(PLAY_Y1 + 50, PLAY_Y2 - 50)
        if math.hypot(ex2 - cx0, ey2 - cy0) > 200:
            er = pygame.Rect(ex2 - 16, ey2 - 16, 32, 32)
            if not any(er.colliderect(o.rect) for o in obstacles):
                enemies.append(Enemy(ex2, ey2, random.randint(60, 140), level))

    if cfg['boss']:
        boss = Boss(random.randint(PLAY_X1 + 200, PLAY_X2 - 200), random.randint(PLAY_Y1 + 100, PLAY_Y1 + 220))

    return obstacles, enemies, boss, exit_pos


def transition_screen(level, direction='in'):
    global cursor_x, cursor_y
    duration = 40
    lname    = LEVEL_DATA[level]['name']
    particles = []

    for frame in range(duration):
        t = frame / duration
        if direction == 'in':
            alpha   = int(255 * (1 - t))
            t_alpha = min(255, int(255 * t * 2))
        else:
            alpha   = int(255 * t)
            t_alpha = int(255 * (1 - t))

        screen.fill(DARK_BG)
        draw_background(screen, frame, level)

        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        screen.blit(ov, (0, 0))

        if t_alpha > 50:
            panel = pygame.Surface((620, 130), pygame.SRCALPHA)
            panel.fill((6, 2, 2, min(210, t_alpha)))
            screen.blit(panel, (SCREEN_W // 2 - 310, SCREEN_H // 2 - 65))
            pygame.draw.rect(screen, DARK_RED, (SCREEN_W // 2 - 310, SCREEN_H // 2 - 65, 620, 130), 1, border_radius=5)
            sa = min(255, t_alpha)
            draw_text_centered(screen, f"LEVEL {level}", FONTS['big'], (*RED, sa), SCREEN_W // 2, SCREEN_H // 2 - 20)
            draw_text_centered(screen, lname, FONTS['med'], (*AMBER, sa), SCREEN_W // 2, SCREEN_H // 2 + 20)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()
        clock.tick(FPS)


def title_screen():
    global cursor_x, cursor_y
    pygame.mouse.set_visible(True)
    frame = 0
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return 'start'
                if e.key == pygame.K_h:
                    return 'howto'
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                return 'start'

        frame += 1
        screen.fill(DARK_BG)
        draw_background(screen, frame, 1)

        t = frame * 0.018
        for i in range(10):
            px2 = int((math.sin(t + i * 0.7) * 0.4 + 0.5) * SCREEN_W)
            py2 = int((math.cos(t * 0.65 + i * 1.0) * 0.35 + 0.5) * SCREEN_H)
            glow_circle(screen, BLOOD, px2, py2, 9 + i, 2, 12)

        panel = pygame.Surface((680, 250), pygame.SRCALPHA)
        panel.fill((5, 2, 2, 195))
        screen.blit(panel, (SCREEN_W // 2 - 340, 74))
        pygame.draw.rect(screen, DARK_RED, (SCREEN_W // 2 - 340, 74, 680, 250), 1, border_radius=4)

        cl = FONTS['small'].render("CLASSIFIED  ·  IMF FILE #4829  ·  TOP SECRET", True, CRIMSON)
        screen.blit(cl, cl.get_rect(center=(SCREEN_W // 2, 92)))

        pulse = abs(math.sin(frame * 0.04))
        draw_text_centered(screen, "MISSION", FONTS['title'], WHITE, SCREEN_W // 2, 158, glow_col=BLOOD)
        glow_c = lerp_color(DARK_RED, RED, pulse)
        draw_text_centered(screen, "IMPOSSIBLE", FONTS['title'], glow_c, SCREEN_W // 2, 218, glow_col=lerp_color(BLOOD, DARK_RED, pulse))

        pygame.draw.line(screen, DARK_RED, (SCREEN_W // 2 - 260, 252), (SCREEN_W // 2 + 260, 252), 1)

        char_y = 442
        for cx2, fn, lbl, col in [
            (SCREEN_W // 2 - 240, lambda: draw_ethan(screen, SCREEN_W // 2 - 240, char_y, 1.25, frame, 1.0, 0, 0, 0), "ETHAN HUNT", AMBER),
            (SCREEN_W // 2,       lambda: draw_robot(screen, SCREEN_W // 2, char_y, 1.25, frame, True, 1.0), "SYNDICATE UNIT", RED),
            (SCREEN_W // 2 + 240, lambda: draw_solomon(screen, SCREEN_W // 2 + 240, char_y, 1.25, frame), "SOLOMON LANE", PURPLE),
        ]:
            fn()
            lbl_t = FONTS['tiny'].render(lbl, True, col)
            screen.blit(lbl_t, lbl_t.get_rect(center=(cx2, char_y + 56)))

        btn_pulse = abs(math.sin(frame * 0.06))
        bc = lerp_color(DARK_RED, RED, btn_pulse)
        draw_text_centered(screen, "[ ENTER / CLICK ]  START MISSION", FONTS['med'], bc, SCREEN_W // 2, 544, glow_col=BLOOD)
        draw_text_centered(screen, "[ H ]  HOW TO PLAY", FONTS['small'], GRAY, SCREEN_W // 2, 580)
        draw_text_centered(screen, "[ ESC ]  EXIT", FONTS['small'], MID_GRAY, SCREEN_W // 2, 602)

        pygame.display.flip()
        clock.tick(FPS)


def howto_screen():
    pygame.mouse.set_visible(True)
    frame = 0
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                return
        frame += 1
        screen.fill(DARK_BG)
        draw_background(screen, frame, 1)
        draw_text_centered(screen, "MISSION BRIEFING", FONTS['big'], RED, SCREEN_W // 2, 60, glow_col=BLOOD)

        lines = [
            ("MOVE",     "WASD  or  ARROW KEYS",                              WHITE),
            ("AIM",      "MOUSE — crosshair tracks cursor in arena",           WHITE),
            ("SHOOT",    "LEFT CLICK  (hold for rapid fire)",                  AMBER),
            ("MISSILE",  "SPACE or R  — earn 1 per 3 successful hits",         AMBER),
            ("",         "", WHITE),
            ("GOAL",     "Eliminate all enemies → reach EXIT portal",          GREEN),
            ("BOSS",     "Level 5: Defeat Solomon Lane to win",                RED),
            ("",         "", WHITE),
            ("ENEMIES",  "Robots patrol, chase & fire spread shots",           RED),
            ("BOSS AI",  "Lane orbits you. Phase 2 = 7-way spread!",           PURPLE),
            ("SHIELD",   "Boss activates purple shield — bullets deflect!",    (180,100,255)),
            ("TELEPORT", "Boss phase-shifts to new location, leaves afterimage",(0,230,200)),
            ("NOVA",     "Boss fires 12-way bullet ring — watch the warning!",  RED),
            ("OBSTACLES","Shoot obstacles to destroy them (4 hits)",            ORANGE),
        ]
        for i, (k, v, vc) in enumerate(lines):
            if k:
                draw_text_left(screen, k + ":", FONTS['med'], DARK_RED, SCREEN_W // 2 - 310, 110 + i * 34)
                draw_text_left(screen, v, FONTS['small'], vc, SCREEN_W // 2 - 50, 117 + i * 34)

        draw_text_centered(screen, "[ ANY KEY ]  RETURN", FONTS['small'], GRAY, SCREEN_W // 2, SCREEN_H - 42)
        pygame.display.flip()
        clock.tick(FPS)


def level_clear_screen(level, score):
    pygame.mouse.set_visible(True)
    frame = 0
    particles = []
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                return
        frame += 1
        screen.fill(DARK_BG)
        draw_background(screen, frame, level)
        if frame % 5 == 0:
            particles_burst(particles, random.randint(PLAY_X1, PLAY_X2), random.randint(PLAY_Y1, PLAY_Y1 + 100), RED, 4, 3, -0.04)
        update_particles(particles, 1 / FPS)
        draw_particles(screen, particles)

        panel = pygame.Surface((520, 190), pygame.SRCALPHA)
        panel.fill((6, 2, 2, 215))
        screen.blit(panel, (SCREEN_W // 2 - 260, SCREEN_H // 2 - 95))
        pygame.draw.rect(screen, DARK_RED, (SCREEN_W // 2 - 260, SCREEN_H // 2 - 95, 520, 190), 1, border_radius=5)

        pulse = abs(math.sin(frame * 0.06))
        c = lerp_color(DARK_RED, RED, pulse)
        draw_text_centered(screen, f"LEVEL {level} CLEARED", FONTS['big'], c, SCREEN_W // 2, SCREEN_H // 2 - 50, glow_col=BLOOD)
        draw_text_centered(screen, LEVEL_DATA[level]['name'], FONTS['med'], AMBER, SCREEN_W // 2, SCREEN_H // 2 - 10)
        draw_text_centered(screen, f"SCORE  {score:06d}", FONTS['med'], WHITE, SCREEN_W // 2, SCREEN_H // 2 + 30)
        draw_text_centered(screen, "[ ANY KEY ]  NEXT LEVEL", FONTS['small'], GRAY, SCREEN_W // 2, SCREEN_H // 2 + 70)
        pygame.display.flip()
        clock.tick(FPS)


def game_over_screen(score, won=False):
    pygame.mouse.set_visible(True)
    frame = 0
    particles = []
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                return
        frame += 1
        screen.fill(DARK_BG)
        draw_background(screen, frame, 5)
        if won and frame % 4 == 0:
            cx2   = random.randint(PLAY_X1, PLAY_X2)
            cy2   = random.randint(PLAY_Y1, PLAY_Y2)
            col   = random.choice([AMBER, RED, ORANGE])
            particles_burst(particles, cx2, cy2, col, 5, 3, -0.04)
        if not won and frame % 8 == 0:
            particles_burst(particles, random.randint(PLAY_X1, PLAY_X2), random.randint(PLAY_Y1, PLAY_Y2), BLOOD, 3, 2, -0.02)
        update_particles(particles, 1 / FPS)
        draw_particles(screen, particles)

        panel = pygame.Surface((580, 210), pygame.SRCALPHA)
        panel.fill((6, 2, 2, 218))
        screen.blit(panel, (SCREEN_W // 2 - 290, SCREEN_H // 2 - 105))
        pygame.draw.rect(screen, DARK_RED if not won else CRIMSON, (SCREEN_W // 2 - 290, SCREEN_H // 2 - 105, 580, 210), 1, border_radius=5)

        if won:
            pulse = abs(math.sin(frame * 0.05))
            c     = lerp_color(DARK_RED, RED, pulse)
            draw_text_centered(screen, "MISSION COMPLETE", FONTS['title'], c, SCREEN_W // 2, SCREEN_H // 2 - 60, glow_col=BLOOD)
            draw_text_centered(screen, "IMF CONGRATULATES AGENT HUNT", FONTS['med'], WHITE, SCREEN_W // 2, SCREEN_H // 2 - 10)
        else:
            draw_text_centered(screen, "MISSION FAILED", FONTS['title'], DARK_RED, SCREEN_W // 2, SCREEN_H // 2 - 60, glow_col=BLOOD)
            draw_text_centered(screen, "AGENT HUNT IS DOWN", FONTS['med'], GRAY, SCREEN_W // 2, SCREEN_H // 2 - 10)

        draw_text_centered(screen, f"FINAL SCORE  {score:06d}", FONTS['big'], AMBER, SCREEN_W // 2, SCREEN_H // 2 + 40)
        draw_text_centered(screen, "[ ANY KEY ]  MAIN MENU", FONTS['small'], GRAY, SCREEN_W // 2, SCREEN_H // 2 + 84)
        pygame.display.flip()
        clock.tick(FPS)


def run_level(level):
    global cursor_x, cursor_y, _current_level
    _current_level = level

    pygame.mouse.set_visible(False)

    obstacles, enemies, boss, exit_pos = make_level(level)
    player = Player((PLAY_X1 + PLAY_X2) // 2, (PLAY_Y1 + PLAY_Y2) // 2)
    player.score         = getattr(run_level, '_score', 0)
    player.missile_count = getattr(run_level, '_missiles', 0)

    particles  = []
    shockwaves = []
    frame      = 0
    has_boss   = LEVEL_DATA[level]['boss']
    floaters   = []

    mx, my = pygame.mouse.get_pos()
    cursor_x = float(max(PLAY_X1 + 8, min(PLAY_X2 - 8, mx)))
    cursor_y = float(max(PLAY_Y1 + 8, min(PLAY_Y2 - 8, my)))

    transition_screen(level, 'out')

    pygame.mouse.set_visible(False)

    pygame.mouse.set_pos(SCREEN_W // 2, SCREEN_H // 2)
    cursor_x = float(SCREEN_W // 2)
    cursor_y = float(SCREEN_H // 2)
    pygame.event.clear()

    def exit_open():
        return (all(not e.alive for e in enemies) and
                (not has_boss or boss is None or not boss.alive))

    is_shooting = False

    while True:
        dt    = clock.tick(FPS) / 1000.0
        dt    = min(dt, 0.033)  
        frame += 1
        is_shooting = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.mouse.set_visible(True)
                    return 'quit'
                if e.key in (pygame.K_SPACE, pygame.K_r):
                    all_targets = [en for en in enemies if en.alive]
                    if has_boss and boss and boss.alive:
                        all_targets.append(boss)
                    player.launch_missile(all_targets, boss)

            if e.type == pygame.MOUSEMOTION:
                abs_x, abs_y = e.pos
                cursor_x = float(max(PLAY_X1 + 8, min(PLAY_X2 - 8, abs_x)))
                cursor_y = float(max(PLAY_Y1 + 8, min(PLAY_Y2 - 8, abs_y)))

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                all_e = [en for en in enemies if en.alive]
                player.shoot(cursor_x, cursor_y, all_e, boss)
                is_shooting = True

        if pygame.mouse.get_pressed()[0]:
            all_e = [en for en in enemies if en.alive]
            player.shoot(cursor_x, cursor_y, all_e, boss)
            is_shooting = True

        keys = pygame.key.get_pressed()
        player.update(keys, obstacles, dt)

        for enemy in enemies:
            if enemy.alive:
                enemy.update(player.rect, obstacles, dt)
        if has_boss and boss and boss.alive:
            boss.update(player.rect, dt)

        for pb in player.bullets[:]:
            if not pb.alive:
                continue
            for obs in obstacles:
                if obs.alive and obs.rect.collidepoint(pb.x, pb.y):
                    pb.alive = False
                    particles_burst(particles, pb.x, pb.y, ORANGE, 6, 3)
                    play('hit')
                    if obs.hit():
                        particles_burst(particles, obs.rect.centerx, obs.rect.centery, RED, 14, 6)
                        shockwave(shockwaves, obs.rect.centerx, obs.rect.centery, ORANGE)
                    break

        for pb in player.bullets[:]:
            if not pb.alive:
                continue
            for enemy in enemies:
                if enemy.alive and pb.rect.colliderect(enemy.rect):
                    pb.alive = False
                    earned   = player.register_hit()
                    killed   = enemy.hit()
                    particles_burst(particles, pb.x, pb.y, RED, 10, 5)
                    play('hit')
                    if killed:
                        player.score += 100 * level
                        particles_burst(particles, enemy.x, enemy.y, DARK_RED, 20, 7)
                        shockwave(shockwaves, enemy.x, enemy.y, RED)
                        floaters.append({'x': enemy.x, 'y': enemy.y - 20, 'text': f"+{100 * level}", 'life': 1.2, 'color': AMBER})
                        play('die')
                    if earned:
                        floaters.append({'x': player.x, 'y': player.y - 40, 'text': "+1 MISSILE", 'life': 1.5, 'color': AMBER})
                    break

        for pb in player.bullets[:]:
            if not pb.alive:
                continue
            if has_boss and boss and boss.alive and pb.rect.colliderect(boss.rect):
                pb.alive = False
                if boss.shielded:
                    # Deflect flash
                    particles_burst(particles, pb.x, pb.y, PURPLE, 8, 4)
                    floaters.append({'x': boss.x, 'y': boss.y - 50, 'text': "BLOCKED!", 'life': 0.8, 'color': PURPLE})
                    boss.hit()
                else:
                    earned   = player.register_hit()
                    killed   = boss.hit()
                    particles_burst(particles, pb.x, pb.y, PURPLE, 12, 5)
                    play('boss_hit')
                    if killed:
                        player.score += 1000
                        for _ in range(5):
                            particles_burst(particles, boss.x + random.randint(-30, 30), boss.y + random.randint(-30, 30), RED, 20, 8)
                        shockwave(shockwaves, boss.x, boss.y, PURPLE)
                        shockwave(shockwaves, boss.x, boss.y, RED)
                        floaters.append({'x': boss.x, 'y': boss.y - 40, 'text': "+1000", 'life': 2.0, 'color': AMBER})
                        play('explode')
                    if earned:
                        floaters.append({'x': player.x, 'y': player.y - 40, 'text': "+1 MISSILE", 'life': 1.5, 'color': AMBER})

        for m in player.missiles[:]:
            if not m.alive:
                continue
            hit = False
            for enemy in enemies:
                if enemy.alive and m.rect.colliderect(enemy.rect):
                    m.alive = False
                    hit     = True
                    killed  = enemy.hit()
                    particles_burst(particles, m.x, m.y, ORANGE, 22, 8, 0.05)
                    shockwave(shockwaves, m.x, m.y, ORANGE)
                    play('explode')
                    if killed:
                        player.score += 150 * level
                        floaters.append({'x': enemy.x, 'y': enemy.y - 20, 'text': f"+{150 * level}", 'life': 1.2, 'color': ORANGE})
                    break
            if not hit and has_boss and boss and boss.alive and m.rect.colliderect(boss.rect):
                m.alive = False
                if boss.shielded:
                    particles_burst(particles, m.x, m.y, PURPLE, 14, 6, 0.05)
                    floaters.append({'x': boss.x, 'y': boss.y - 50, 'text': "MISSILE BLOCKED!", 'life': 1.0, 'color': PURPLE})
                    boss.shield_timer = max(0, boss.shield_timer - 40)
                    if boss.shield_timer <= 0:
                        boss.shielded = False
                else:
                    for _ in range(3):
                        particles_burst(particles, m.x + random.randint(-20, 20), m.y + random.randint(-20, 20), ORANGE, 16, 7, 0.05)
                    shockwave(shockwaves, m.x, m.y, ORANGE)
                    killed = boss.hit()
                    play('explode')
                    if killed:
                        player.score += 1500
                        floaters.append({'x': boss.x, 'y': boss.y - 40, 'text': "+1500", 'life': 2.0, 'color': ORANGE})

        for enemy in enemies:
            if not enemy.alive:
                continue
            for eb in enemy.bullets[:]:
                if not eb.alive:
                    continue
                if eb.rect.colliderect(player.rect):
                    eb.alive = False
                    if player.take_damage(1):
                        particles_burst(particles, player.x, player.y, RED, 10, 3)
                        play('player_hit')

        if has_boss and boss and boss.alive:
            for bb in boss.bullets[:]:
                if not bb.alive:
                    continue
                if bb.rect.colliderect(player.rect):
                    bb.alive = False
                    if player.take_damage(2):
                        particles_burst(particles, player.x, player.y, RED, 16, 5)
                        shockwave(shockwaves, player.x, player.y, RED)
                        play('player_hit')

        if exit_open():
            er = pygame.Rect(exit_pos[0] - 26, exit_pos[1] - 26, 52, 52)
            if er.colliderect(player.rect):
                run_level._score    = player.score
                run_level._missiles = player.missile_count
                play('portal')
                transition_screen(level, 'in')
                pygame.mouse.set_visible(True)
                return 'next'

        if not player.alive:
            run_level._score = 0
            play('die')
            pygame.mouse.set_visible(True)
            return 'dead'

        draw_background(screen, frame, level)
        draw_exit_portal(screen, exit_pos[0], exit_pos[1], frame, not exit_open())

        for obs in obstacles:
            if obs.alive:
                obs.draw(screen, frame)

        for enemy in enemies:
            if enemy.alive:
                enemy.draw(screen)

        if has_boss and boss and boss.alive:
            boss.draw(screen)

        player.draw(screen)

        update_shockwaves(shockwaves, dt)
        draw_shockwaves(screen, shockwaves)
        update_particles(particles, dt)
        draw_particles(screen, particles)

        for fl in floaters[:]:
            ft = FONTS['med'].render(fl['text'], True, fl['color'])
            gt = FONTS['med'].render(fl['text'], True, lerp_color(fl['color'], BLACK, 0.4))
            screen.blit(gt, gt.get_rect(center=(int(fl['x']) + 1, int(fl['y']) + 1)))
            screen.blit(ft, ft.get_rect(center=(int(fl['x']), int(fl['y']))))
            fl['y']    -= 1.1
            fl['life'] -= dt * 1.3
            if fl['life'] <= 0:
                floaters.remove(fl)

        draw_custom_cursor(screen, cursor_x, cursor_y, frame, player.missile_count > 0, is_shooting)

        enemies_left = sum(1 for e in enemies if e.alive)
        if has_boss and boss and boss.alive:
            enemies_left += 1

        draw_hud(screen, player, level, enemies_left, has_boss, boss if has_boss else None, frame)
        pygame.display.flip()

    return 'quit'


def main():
    run_level._score    = 0
    run_level._missiles = 0

    while True:
        result = title_screen()
        if result == 'howto':
            howto_screen()
            continue

        for level in range(1, 6):
            result = run_level(level)
            if result == 'dead':
                game_over_screen(getattr(run_level, '_score', 0), False)
                break
            elif result == 'quit':
                break
            elif result == 'next':
                if level < 5:
                    level_clear_screen(level, run_level._score)
                else:
                    game_over_screen(run_level._score, True)
                    break


if __name__ == "__main__":
    main()