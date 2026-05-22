# Liste des commandes véhicule — Tesla Fleet API

Source : [Vehicle Commands](https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-commands)

Format : `POST /api/1/vehicles/{vin}/command/{nom}`  
Exception : `POST /api/1/vehicles/{vin}/wake_up`

**Prérequis** : token business (ou utilisateur) avec `vehicle_cmds`, véhicule éveillé si besoin, clé virtuelle installée.

## Implémentées dans l’UI (onglet Commandes)

| Commande | Catégorie | Description |
|----------|-----------|-------------|
| `wake_up` | essentiel | Réveiller |
| `door_lock` / `door_unlock` | sécurité | Verrouillage |
| `flash_lights` / `honk_horn` | sécurité | Repérage |
| `charge_*` | recharge | Charge et trappe |
| `media_*` / `adjust_volume` | média | Musique et volume |
| `auto_conditioning_*` / `set_temps` | climat | Climatisation |
| `remote_start_drive` | conduite | Démarrage à distance |
| `actuate_trunk` / `window_control` / `sun_roof_control` | carrosserie | Coffre, vitres, toit |
| `set_sentry_mode` | sécurité | Sentinelle |
| `remote_boombox` | divers | Son extérieur |
| `navigation_request` | navigation | Adresse |
| `guest_mode` | flotte | Mode invité |

## Catalogue complet Tesla (référence)

### Sécurité & accès
- `door_lock`, `door_unlock`
- `flash_lights`, `honk_horn`
- `set_sentry_mode`
- `guest_mode`
- `clear_pin_to_drive_admin`, `set_pin_to_drive`, `reset_pin_to_drive_pin`
- `set_valet_mode`, `reset_valet_pin`
- `speed_limit_activate`, `speed_limit_deactivate`, `speed_limit_set_limit`, `speed_limit_clear_pin`, `speed_limit_clear_pin_admin`

### Média
- `media_toggle_playback`
- `media_next_track`, `media_prev_track`
- `media_next_fav`, `media_prev_fav`
- `media_volume_down`
- `adjust_volume`

### Recharge
- `charge_start`, `charge_stop`
- `charge_port_door_open`, `charge_port_door_close`
- `set_charge_limit`, `set_charging_amps`
- `charge_max_range`, `charge_standard`
- `add_charge_schedule`, `remove_charge_schedule`
- `set_scheduled_charging` (déprécié firmware récent)

### Climat
- `auto_conditioning_start`, `auto_conditioning_stop`
- `set_temps`, `set_climate_keeper_mode`, `set_preconditioning_max`
- `set_cabin_overheat_protection`, `set_cop_temp`
- `remote_seat_heater_request`, `remote_seat_cooler_request`
- `remote_auto_seat_climate_request`
- `remote_steering_wheel_heater_request`, `remote_steering_wheel_heat_level_request`
- `remote_auto_steering_wheel_heat_climate_request`
- `add_precondition_schedule`, `remove_precondition_schedule`
- `set_scheduled_departure` (déprécié)
- `set_bioweapon_mode`

### Carrosserie
- `actuate_trunk`
- `window_control`
- `sun_roof_control`

### Conduite & navigation
- `remote_start_drive`
- `navigation_request`, `navigation_gps_request`, `navigation_sc_request`, `navigation_waypoints_request`

### Logiciel & divers
- `schedule_software_update`, `cancel_software_update`
- `set_vehicle_name`, `erase_user_data`
- `remote_boombox`
- `trigger_homelink`
- `upcoming_calendar_entries`

## Appel via l’API locale

```bash
curl -X POST "http://localhost:8000/api/business/vehicles/VIN_OU_ID/commands/media_next_track" \
  -H "Content-Type: application/json" \
  -d '{"body": {}}'
```

Avec corps JSON :

```bash
curl -X POST "http://localhost:8000/api/business/vehicles/VIN/commands/adjust_volume" \
  -H "Content-Type: application/json" \
  -d '{"body": {"volume": 5}}'
```
