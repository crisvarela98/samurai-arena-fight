import "./style.css";
import { loadGameData } from "./data.js";
import { SamuraiArenaWebApp } from "./app.js";

async function bootstrap() {
  const root = document.querySelector("#app");
  root.innerHTML = `<div class="loading-screen"><p>Cargando Samurai Arena Fight Web...</p></div>`;
  try {
    const data = await loadGameData();
    const app = new SamuraiArenaWebApp(root, data);
    await app.init();
  } catch (error) {
    root.innerHTML = `
      <div class="loading-screen error">
        <h1>Error de carga</h1>
        <p>${error.message}</p>
        <p>Verificá que exista la carpeta \`client/\` y ejecutá \`npm run dev\` desde \`web-client/\`.</p>
      </div>
    `;
  }
}

bootstrap();
