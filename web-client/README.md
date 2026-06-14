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
VITE_SERVER_URL=https://tu-backend.onrender.com
```

También podés editar `public/runtime-config.js` si necesitás una configuración runtime sin rebuild.

## Build

```bash
npm run build
```

## Deploy

### Backend en Render

- Root directory: `server`
- Build command: `npm install`
- Start command: `npm start`

Variables:

```env
MONGODB_URI=mongodb+srv://...
CLIENT_URL=https://tu-frontend.vercel.app
NODE_ENV=production
JWT_SECRET=un_secreto_largo
JWT_EXPIRES_IN=7d
```

Rutas útiles:

- `GET /`
- `GET /health`

### Frontend en Vercel

- Root directory: `web-client`
- Build command: `npm run build`
- Output directory: `dist`

Variable:

```env
VITE_SERVER_URL=https://tu-backend.onrender.com
```

## Convertir a APK con WebIntoApp / WebsiteToAPK

1. Deployá `web-client` a Vercel.
2. Confirmá que el frontend apunte a `VITE_SERVER_URL`.
3. Copiá la URL pública final de Vercel.
4. Abrí WebIntoApp o WebsiteToAPK.
5. Pegá esa URL.
6. Elegí orientación horizontal.
7. Generá el APK WebView.

## Backend requerido

El backend Node actual debe quedar desplegado aparte con:

- `CLIENT_URL` = URL pública del frontend web
- `NODE_ENV=production`
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
