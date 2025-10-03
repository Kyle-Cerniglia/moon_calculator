#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tucson, AZ sky info (Windows 10 friendly)

Prints:
- Unicode art of the current moon
- Current moon phase (named)
- Current moon illumination (%)
- End of astronomical twilight (astronomical dusk)
- Start of astronomical twilight (astronomical dawn)
- Moonrise
- Moonset

Requires:
    pip install astral pytz
"""

from datetime import datetime
import math

from astral import LocationInfo
from astral.sun import dawn, dusk
from astral import moon
import pytz


# --- Configuration for Tucson, AZ ---
TUCSON = LocationInfo(
    name="Tucson",
    region="USA",
    timezone="America/Phoenix",
    latitude=32.2226,
    longitude=-110.9747,
)

PHOENIX_TZ = pytz.timezone("America/Phoenix")

# Synodic month length
SYNODIC_MONTH = 29.53058867


def local_now():
    """Return the current local datetime in America/Phoenix."""
    return datetime.now(PHOENIX_TZ)


def moon_phase_name(age_days: float) -> str:
    """Map lunar age to a common phase name."""
    a = age_days % SYNODIC_MONTH
    if a < 1.0:
        return "New Moon"
    elif a < 6.0:
        return "Waxing Crescent"
    elif a < 8.0:
        return "First Quarter"
    elif a < 13.0:
        return "Waxing Gibbous"
    elif a < 16.0:
        return "Full Moon"
    elif a < 21.0:
        return "Waning Gibbous"
    elif a < 23.0:
        return "Last Quarter"
    elif a < 29.0:
        return "Waning Crescent"
    else:
        return "New Moon"


def moon_illumination_pct(age_days: float) -> float:
    """Approximate fractional illumination from lunar age."""
    phase_angle = 2.0 * math.pi * (age_days / SYNODIC_MONTH)
    frac = (1.0 - math.cos(phase_angle)) / 2.0
    return frac * 100.0


def unicode_moon(illum_frac: float, waxing: bool, width: int = 23, height: int = 13) -> str:
    """
    Render a Unicode moon with a soft terminator:
      - illum_frac: 0..1
      - waxing: True if waxing, False if waning
    Uses block shades for the boundary for a cleaner look.
    """
    illum_frac = max(0.0, min(1.0, illum_frac))

    # Terminator offset b in [-1, 1]:
    # b = 1 → new (no lit), b = -1 → full (all lit), b = 0 → half lit
    b = 1.0 - 2.0 * illum_frac

    # Characters
    #   FULL: fully illuminated
    #   EDGE2/EDGE1: near the terminator (softer transition)
    #   DARK: unilluminated interior
    #   OUT: outside the disk
    FULL = "█"
    EDGE2 = "▓"
    EDGE1 = "▒"
    DARK = "░"
    OUT = " "

    # Edge thickness tuning (in “x” units; try to keep small)
    t1 = 0.025   # innermost soft edge
    t2 = 0.07    # wider soft edge

    rows = []
    for j in range(height):
        # y in [-1, 1]; stretch a bit to look circular in console
        y = (2.0 * j / (height - 1)) - 1.0
        y_adj = y * 1.15

        row_chars = []
        for i in range(width):
            x = (2.0 * i / (width - 1)) - 1.0

            # Inside disk?
            if x * x + y_adj * y_adj > 1.0:
                row_chars.append(OUT)
                continue

            # Which side is lit?
            term = b if waxing else -b
            dist = x - term
            lit = dist > 0 if waxing else dist < 0
            adist = abs(dist)

            if lit:
                # Close to terminator? Use edge shades.
                if adist < t1:
                    ch = EDGE1
                elif adist < t2:
                    ch = EDGE2
                else:
                    ch = FULL
            else:
                # Dark side: softer near the edge
                if adist < t2:
                    ch = EDGE1
                else:
                    ch = DARK

            row_chars.append(ch)

        rows.append("".join(row_chars))

    return "\n".join(rows)


def main():
    now_local = local_now()
    today_local = now_local.date()

    # Moon phase/illumination
    age = moon.phase(today_local)  # 0..~29.53 days
    phase = moon_phase_name(age)

    try:
        illum_frac = float(moon.illumination(today_local))  # Astral v3+ returns 0..1
    except Exception:
        illum_frac = moon_illumination_pct(age) / 100.0

    illum_pct = illum_frac * 100.0

    # Determine waxing vs waning from age
    waxing = age < (SYNODIC_MONTH / 2.0)

    # Astronomical twilight (note: printing END before START)
    astro_dawn = dawn(
        observer=TUCSON.observer,
        date=today_local,
        tzinfo=PHOENIX_TZ,
        depression=18.0,
    )
    astro_dusk = dusk(
        observer=TUCSON.observer,
        date=today_local,
        tzinfo=PHOENIX_TZ,
        depression=18.0,
    )

    # Moonrise & Moonset
    moonrise = moon.moonrise(TUCSON.observer, date=today_local, tzinfo=PHOENIX_TZ)
    moonset = moon.moonset(TUCSON.observer, date=today_local, tzinfo=PHOENIX_TZ)

    # Output
    print(f"Location: {TUCSON.name}, {TUCSON.region}  (TZ: {TUCSON.timezone})")
    print(f"Local system time: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Unicode Moon
    print(unicode_moon(illum_frac, waxing))
    print()

    print(f"Current moon phase: {phase}")
    print(f"Current moon illumination: {illum_pct:.1f}%")
    print()
    print("Astronomical twilight (today):")
    # Flipped order: End (dusk) first, then Start (dawn)
    print(f"  End   (astronomical dusk): {astro_dusk.strftime('%Y-%m-%d %H:%M:%S %Z') if astro_dusk else 'N/A'}")
    print(f"  Start (astronomical dawn): {astro_dawn.strftime('%Y-%m-%d %H:%M:%S %Z') if astro_dawn else 'N/A'}")
    print()
    print("Moon events (today):")
    print(f"  Moonrise: {moonrise.strftime('%Y-%m-%d %H:%M:%S %Z') if moonrise else 'N/A'}")
    print(f"  Moonset : {moonset .strftime('%Y-%m-%d %H:%M:%S %Z') if moonset  else 'N/A'}")
    
    input("")


if __name__ == "__main__":
    main()
