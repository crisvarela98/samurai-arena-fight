# Samurai Arena Fight - Cliente

Cliente base en `Python + Pygame`.

## Ejecutar

```bash
pip install -r requirements.txt
python main.py
```

## Online

- Para jugar entre distintas plataformas, ambos clientes deben apuntar a la misma URL/IP del servidor.
- Si juegas en red local, no uses `localhost` en el dispositivo invitado; usa la IP LAN del host, por ejemplo `192.168.0.10:3000`.

## Estructura

- `src/core`: arranque, constantes y gestor de escenas
- `src/scenes`: pantallas del juego
- `src/combat`: combate, IA y movimientos
- `src/entities`: personajes, armas y hitboxes
- `src/ui`: botones, barras y controles táctiles
- `src/network`: cliente online
- `src/utils`: carga de JSON y assets
