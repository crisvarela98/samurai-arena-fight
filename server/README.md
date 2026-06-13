# Backend Samurai Arena Fight

Backend Express + Socket.IO + MongoDB con JWT.

```bash
npm install
copy .env.example .env
npm start
```

Variables:

- `PORT`
- `MONGODB_URI`
- `CLIENT_URL`
- `JWT_SECRET`
- `JWT_EXPIRES_IN`

Sin MongoDB se habilita un almacenamiento temporal en memoria para pruebas locales.

Online requiere token JWT tanto para REST como para el handshake Socket.IO.
