# Samurai Arena Fight Web

Cliente web mobile-first para convivir con el cliente Python original.

## Stack

- `Vite`
- `HTML + CSS + JavaScript`
- `Canvas 2D`
- `socket.io-client`

## Desarrollo

Desde `web-client/`:

```bash
npm install
npm run dev
```

El script sincroniza automáticamente:

- `../client/assets` → `web-client/public/game/assets`
- `../client/data` → `web-client/public/game/data`

## Variables

Copiá `.env.example` a `.env` si querés fijar URLs:

```bash
VITE_API_BASE_URL=https://tu-backend.example.com
VITE_SOCKET_URL=https://tu-backend.example.com
```

También podés editar `public/runtime-config.js` si necesitás una configuración runtime sin rebuild.

## Build

```bash
npm run build
```

## Deploy

### Vercel o Netlify

1. Subí este repo a GitHub.
2. En Vercel o Netlify, usá `web-client/` como root del frontend.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Definí:
   - `VITE_API_BASE_URL`
   - `VITE_SOCKET_URL`

## Convertir a APK con WebIntoApp / WebsiteToAPK

1. Deployá `web-client` a Vercel o Netlify.
2. Copiá la URL pública final.
3. Abrí WebIntoApp o WebsiteToAPK.
4. Pegá esa URL.
5. Elegí orientación horizontal.
6. Activá pantalla completa / fullscreen si la plataforma lo permite.
7. Generá el APK WebView.

## Backend requerido

El backend Node actual debe quedar desplegado aparte con:

- `CLIENT_URL` = URL pública del frontend web
- `JWT_SECRET`
- `MONGODB_URI`

El modo online usa:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/rooms`
- `GET /api/ranking`
- Socket.IO del backend existente

## Convivencia

Este cliente no reemplaza:

- `client/` Python + Pygame
- `server/` Node.js + Express + Socket.IO + MongoDB

Convive en paralelo como `web-client/`.
