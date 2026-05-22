"""Catalogue des commandes Fleet API (vehicle commands)."""
from __future__ import annotations

from typing import TypedDict


class CommandDef(TypedDict):
    name: str
    method: str
    path_suffix: str
    category: str
    label_fr: str
    needs_body: bool
    body_hint: str | None


def _cmd(
    name: str,
    category: str,
    label_fr: str,
    *,
    needs_body: bool = False,
    body_hint: str | None = None,
) -> CommandDef:
    return {
        "name": name,
        "method": "POST",
        "path_suffix": f"/command/{name}",
        "category": category,
        "label_fr": label_fr,
        "needs_body": needs_body,
        "body_hint": body_hint,
    }


COMMANDS: list[CommandDef] = [
    _cmd("wake_up", "essentiel", "Réveiller le véhicule"),
    _cmd("door_lock", "sécurité", "Verrouiller"),
    _cmd("door_unlock", "sécurité", "Déverrouiller"),
    _cmd("flash_lights", "sécurité", "Clignoter les phares"),
    _cmd("honk_horn", "sécurité", "Klaxonner"),
    _cmd("charge_start", "recharge", "Démarrer la charge"),
    _cmd("charge_stop", "recharge", "Arrêter la charge"),
    _cmd("charge_port_door_open", "recharge", "Ouvrir trappe de charge"),
    _cmd("charge_port_door_close", "recharge", "Fermer trappe de charge"),
    _cmd("set_charge_limit", "recharge", "Limite de charge (%)", needs_body=True, body_hint='{"percent": 80}'),
    _cmd("charge_max_range", "recharge", "Charge max range"),
    _cmd("charge_standard", "recharge", "Charge standard"),
    _cmd("media_toggle_playback", "média", "Lecture / pause"),
    _cmd("media_next_track", "média", "Piste suivante"),
    _cmd("media_prev_track", "média", "Piste précédente"),
    _cmd("media_next_fav", "média", "Favori suivant"),
    _cmd("media_prev_fav", "média", "Favori précédent"),
    _cmd("media_volume_down", "média", "Volume -"),
    _cmd("adjust_volume", "média", "Volume précis", needs_body=True, body_hint='{"volume": 5}'),
    _cmd("auto_conditioning_start", "climat", "Préconditionnement ON"),
    _cmd("auto_conditioning_stop", "climat", "Préconditionnement OFF"),
    _cmd("set_temps", "climat", "Température cabine", needs_body=True, body_hint='{"driver_temp": 21, "passenger_temp": 21}'),
    _cmd("set_climate_keeper_mode", "climat", "Mode climat", needs_body=True, body_hint='{"climate_keeper_mode": 1}'),
    _cmd("remote_start_drive", "conduite", "Démarrage à distance"),
    _cmd("actuate_trunk", "carrosserie", "Coffre", needs_body=True, body_hint='{"which_trunk": "rear"}'),
    _cmd("window_control", "carrosserie", "Vitres", needs_body=True, body_hint='{"command": "vent"}'),
    _cmd("sun_roof_control", "carrosserie", "Toit ouvrant", needs_body=True, body_hint='{"state": "vent"}'),
    _cmd("set_sentry_mode", "sécurité", "Mode Sentinelle", needs_body=True, body_hint='{"on": true}'),
    _cmd("remote_boombox", "divers", "Son extérieur", needs_body=True, body_hint='{"sound": 2000}'),
    _cmd("navigation_request", "navigation", "Envoyer une adresse", needs_body=True),
    _cmd("guest_mode", "flotte", "Mode invité", needs_body=True, body_hint='{"on": true}'),
]


def list_by_category() -> dict[str, list[CommandDef]]:
    out: dict[str, list[CommandDef]] = {}
    for c in COMMANDS:
        out.setdefault(c["category"], []).append(c)
    return out


def get_command(name: str) -> CommandDef | None:
    for c in COMMANDS:
        if c["name"] == name:
            return c
    return None
