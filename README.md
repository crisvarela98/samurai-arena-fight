# Samurai Arena Fight

Juego de pelea 2D en `Python + Pygame` con backend `Node.js + Express + Socket.IO + MongoDB`.

La primera version incluye:

- campaña narrativa de Kenji con 6 misiones y 13 peleas;
- FTUE narrativo de maximo 2 minutos integrado en la Mision 1, sin modo entrenamiento separado;
- escenas tipo manga con paneles estaticos y boton `SALTAR VIDEO`;
- cuentas con JWT y contraseñas bcrypt;
- guerrero online separado de Kenji, con clan, arma, nombre y color;
- salas Socket.IO autenticadas;
- combate al mejor de tres en online;
- preparacion Android con Buildozer y GitHub Actions;
- compatibilidad con `python start.py` en PC.

## Menu principal

El menu contiene solamente:

- `HISTORIA`
- `ONLINE`
- `CUENTA`
- `OPCIONES`
- `SALIR`

No existe entrenamiento, practice mode ni sandbox. Los controles se aprenden dentro del FTUE narrativo.

## Ejecutar en PC

Instala cliente y servidor:

```bash
cd client
pip install -r requirements.txt

cd ../server
npm install
```

Desde la raiz:

```bash
python start.py
```

`start.py` inicia el servidor local y entrega al cliente el override `SAMURAI_SERVER_URL=http://localhost:3000`. La configuracion empaquetada conserva una URL publica para Android.

## FTUE y primera apertura

El splash aparece durante 2 segundos en cada apertura.

En la primera ejecucion, si `first_time_completed` es `false`, el juego entra automaticamente a:

1. Acto 1: `El Despertar`.
2. Mision 1: `Entre los muertos`.
3. Prologo en paneles manga.
4. Objetivos de movimiento, aproximacion, golpe rapido, golpe fuerte, bloqueo y esquive.
5. Combate corto contra un soldado debilitado.
6. Fragmento de memoria y regreso al menu.

El episodio completo dura como maximo 2 minutos y usa un unico reloj narrativo:

- `0:00-0:20`: pantalla negra, lluvia, despertar de Kenji y perdida de memoria;
- `0:20-0:45`: movimiento, aproximacion y primer dialogo;
- `0:45-1:15`: golpe rapido, golpe fuerte y stamina;
- `1:15-1:40`: bloqueo, esquive e inicio del combate real;
- `1:40-2:00`: victoria, fragmento de memoria, voz misteriosa, guardado y menu principal.

No se presenta como un tutorial separado. Los objetivos aparecen dentro de la mision y avanzan automaticamente si el jugador se demora, preservando el limite de 120 segundos.

Al completar la mision se guarda:

```json
{
  "first_time_completed": true,
  "story_act": 1,
  "story_mission": 1,
  "unlocked_modes": ["Historia", "Online"]
}
```

En PC se usa `client/data/progress.json`. En Android se copia el progreso al almacenamiento privado escribible de la aplicacion.

## Campaña inicial

Los datos viven en `client/data/story/`.

| Mision | Titulo | Peleas |
| --- | --- | ---: |
| 1 | Entre los muertos | 1 |
| 2 | Los cazadores | 2 |
| 3 | Arena de sangre | 3 |
| 4 | El clan roto | 2 |
| 5 | El campeon del coliseo | 2 |
| 6 | El nombre prohibido | 3 |

Total inicial: 13 peleas.

### Cambiar textos o misiones

- Capitulo/acto: `client/data/story/chapters.json`
- Misiones y secuencia de peleas: `client/data/story/missions.json`
- Kenji: `client/data/story/story_fighter.json`
- Enemigos: `client/data/story/enemies.json`
- Dialogos: `client/data/story/dialogues.json`
- Recuerdos: `client/data/story/memory_fragments.json`

Cada enemigo debe respetar los campos de `FighterStats`: vida, stamina, velocidad, ataque, defensa, arma, sheet y retrato.

### Agregar escenas manga

Edita `client/data/story/cutscenes.json`.

Cada cutscene contiene:

```json
{
  "id": "scene_id",
  "mission_before": 1,
  "mission_after": 2,
  "skippable": true,
  "next_scene": "story_map",
  "panels": [
    {
      "image": "assets/story/panel.png",
      "text": "Texto narrativo",
      "speaker": "TAKEDA",
      "duration": 3.5,
      "sound": null
    }
  ]
}
```

El boton pequeño `SALTAR VIDEO` aparece arriba a la derecha cuando `skippable` es `true`. Saltar y terminar normalmente usan el mismo `next_scene`.

Para agregar un acto nuevo:

1. Agrega el acto en `chapters.json`.
2. Agrega sus misiones en `missions.json`.
3. Crea enemigos, recuerdos y cutscenes.
4. Amplia el limite actual del mapa en `story_map.py`.

## Historia y online no se mezclan

Historia usa exclusivamente a Kenji, sus recuerdos y enemigos diseñados.

Online usa un guerrero generado desde:

- nombre;
- clan;
- arma;
- color principal;
- estadisticas base + bonus de clan + bonus de arma.

Los archivos son:

- `client/data/online/clans.json`
- `client/data/online/online_weapons.json`
- `client/data/online/online_fighters.json`

Para agregar un clan, crea un objeto con `id`, `name`, `style`, colores y `bonuses`. Los bonus aceptan campos como `speed`, `attack_power`, `defense`, `max_health` y `max_stamina`.

Para agregar un arma, define daño rapido/fuerte, costo de stamina, alcance, cooldown y bonus. La fabrica `online_fighter_factory.py` combina y limita las estadisticas finales.

## Cuentas y seguridad

Online requiere sesion iniciada. Historia funciona localmente y sincroniza progreso si existe una cuenta activa.

Rutas:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `PUT /api/users/me/progress`

El token JWT se guarda en `client/data/session.json`, archivo ignorado por Git. En Android se guarda en el directorio privado de la aplicacion.

Las contraseñas nunca se guardan en texto plano. El servidor usa `bcryptjs` con hashes bcrypt.

Socket.IO exige JWT durante el handshake. Sin token valido no se permite crear sala, unirse, enviar inputs, atacar ni reportar impactos.

## Configurar MongoDB y Render

1. Crea un cluster en MongoDB Atlas.
2. Crea un Web Service en Render conectado al repositorio.
3. Usa `server` como Root Directory.
4. Build Command: `npm install`.
5. Start Command: `npm start`.
6. Configura las variables de `server/.env.example`:

```env
MONGODB_URI=mongodb+srv://...
JWT_SECRET=un_secreto_largo_y_privado
JWT_EXPIRES_IN=7d
CLIENT_URL=*
```

7. Verifica `https://TU-SERVICIO.onrender.com/health`.
8. Cambia `server_url` en `client/config/settings.json` por esa URL HTTPS.

No subas `server/.env` ni `client/data/session.json`.

Sin `MONGODB_URI`, el servidor usa memoria temporal para desarrollo local. Las cuentas y salas se pierden al reiniciar.

## APK Android

La configuracion esta en:

- `client/buildozer.spec`
- `client/p4a-recipes/pygame-ce/`
- `.github/workflows/build-apk.yml`

El cliente mantiene Pygame. No requiere Java/Kotlin.

Características Android preparadas:

- orientación horizontal;
- pantalla completa;
- superficie logica 1280x720 escalada con letterbox 16:9;
- coordenadas tactiles convertidas a la superficie logica;
- controles tactiles de combate;
- campos de texto compatibles con teclado en pantalla;
- limite de 45 FPS en Android;
- caché de assets y carga de chroma key optimizada;
- progreso y sesion en almacenamiento privado;
- URL publica configurable;
- arquitecturas `arm64-v8a` y `armeabi-v7a`.

### Compilar con GitHub Actions

1. Sube los cambios a GitHub.
2. Abre la pestaña `Actions`.
3. Selecciona `Build Android APK`.
4. Pulsa `Run workflow` o haz push a `main` con cambios en `client/`.
5. Espera a que termine `Build debug APK`.
6. Descarga el artifact `samurai-arena-fight-apk`.
7. Extrae el ZIP e instala el `.apk` en Android habilitando origenes desconocidos.

El workflow usa Ubuntu, Java 17, Buildozer, python-for-android SDL2 y `actions/upload-artifact@v4`.

La receta local de `pygame-ce` existe porque Pygame no dispone de una receta oficial estable integrada en la rama actual de python-for-android. Debe validarse el APK generado en un dispositivo real antes de distribuirlo.

## Controles

PC:

- `A/D`: movimiento
- `W`: salto
- `S`: agacharse
- `J`: golpe rapido
- `K`: golpe fuerte
- `L`: patada
- `I`: bloqueo
- `O`: esquive
- `ESC`: pausa

Android muestra automáticamente joystick/botones táctiles equivalentes.

## Estructura principal

- `client/src/scenes/story_*`: flujo narrativo y combates de historia
- `client/src/scenes/login_scene.py`: login
- `client/src/scenes/register_scene.py`: registro
- `client/src/scenes/account_scene.py`: perfil y logout
- `client/src/scenes/online_character_create.py`: clan, arma, nombre y color
- `client/src/network/auth_client.py`: REST JWT
- `client/src/network/network_client.py`: Socket.IO autenticado
- `server/src/routes/auth.routes.js`: endpoints de cuenta
- `server/src/middleware/auth.middleware.js`: validacion JWT
- `server/src/socket.js`: salas y combate online
