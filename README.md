# Samurai Arena Fight

Base jugable de un juego de pelea 2D samurai con cliente en `Python/Pygame` y backend online en `Node.js + Socket.IO + MongoDB`.

## Arranque unico

Desde la raiz del proyecto:

```bash
python start.py
```

En Windows tambien puedes usar:

```bat
start.bat
```

Eso levanta:
- el servidor en `server/`
- el cliente en `client/`

## Instalacion previa

Cliente:

```bash
cd client
pip install -r requirements.txt
```

Servidor:

```bash
cd server
npm install
```

## Configuracion

- Edita `client/config/settings.json` para resolucion, plataforma y URL del servidor.
- Copia `server/.env.example` a `server/.env` y define `MONGODB_URI`.

## Online entre plataformas

- En `ONLINE`, primero eliges personaje y arena, igual que en local.
- El host crea la sala usando una IP o URL accesible para ambos dispositivos.
- Si juegas entre PC y Android en la misma red, no uses `localhost`; usa la IP LAN del host, por ejemplo `192.168.0.10:3000`.
- El segundo jugador usa esa misma IP/URL y se une con el codigo de sala.

## Ejecutar por separado

Cliente:

```bash
cd client
python main.py
```

Servidor:

```bash
cd server
npm run dev
```

## Que incluye

- Menu principal con estilo samurai oscuro
- Seleccion de plataforma PC o Android
- Seleccion de personaje y arena
- Combate local con vida, stamina, ataques, bloqueo, esquive e IA
- Base online con salas por codigo y Socket.IO

## Siguientes pasos

1. Sustituir placeholders por sprites y animaciones reales.
2. Mejorar la sincronizacion online de posicion y combate.
3. Agregar sonidos, musica y efectos.
4. Expandir personajes, armas y arenas desde los JSON.
