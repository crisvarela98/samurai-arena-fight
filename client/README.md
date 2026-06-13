# Cliente Pygame

Ejecutar en PC:

```bash
pip install -r requirements.txt
python main.py
```

La aplicacion detecta PC o Android automáticamente. PC usa teclado; Android usa controles táctiles y una superficie lógica 1280x720 escalada a la pantalla física.

La campaña está en `data/story/`, los perfiles PvP en `data/online/` y la URL pública en `config/settings.json`.

La Mision 1, `Entre los muertos`, funciona como FTUE narrativo integrado. Incluye prologo, controles, combate, memoria y regreso al menu en un maximo de 2 minutos.

Los siete rivales visuales del modo historia estan en `assets/fighters/story/`; sus retratos se encuentran en `assets/fighters/portraits/story/`.

Para compilar Android desde Linux:

```bash
buildozer -v android debug
```

En GitHub se recomienda usar `.github/workflows/build-apk.yml` y descargar el artifact generado.
