# 🌐 Guía Completa: Cómo Alojar y Jugar Bomberman Multijugador a Distancia (Nube o Internet)

Esta guía te explica cómo alojar el servidor de Bomberman para jugar por internet con tus amigos desde cualquier lugar del mundo.

---

## ⚡ Resumen de Compatibilidad Implementada
- **Soporte Headless en Servidor**: El servidor (`server.py`) corre sin necesidad de monitor o entorno gráfico (`SDL_VIDEODRIVER=dummy`), compatible con Linux, Docker y la nube.
- **Entrada dinámica Host:Puerto**: El cliente ahora acepta tanto IPs (`192.168.1.50`) como dominios con puertos personalizados (`0.tcp.ngrok.io:14256` o `servidor.ejemplo.com:5555`).
- **Soporte Ctrl+V**: Puedes copiar y pegar directamente la dirección en el menú del juego sin tener que escribirla a mano.
- **Auto-escalado Completo**: El multijugador se adapta en pantalla completa a cualquier resolución de monitor.
- **Sincronización Total**: Se sincronizan los 8 tipos de enemigos, los personajes 3D, bombas, explosiones, power-ups y la puerta de salida para avanzar de nivel.

---

## 🚀 OPCIÓN 1: La Más Fácil y Rápida (ngrok o playit.gg - 100% Gratis en 2 Minutos)
Esta opción es ideal para jugar de inmediato sin tener que configurar servidores complejos ni abrir puertos en tu router.

### Con **ngrok**:
1. Descarga **ngrok** gratis desde [ngrok.com](https://ngrok.com/) y crea una cuenta gratuita.
2. Abre tu terminal (PowerShell o CMD) y vincula tu token (el comando que te da ngrok en su web, ej: `ngrok config add-authtoken TU_TOKEN`).
3. En tu computadora, inicia el servidor ejecutando el archivo **`iniciar_servidor.bat`** (o con `python server.py`).
4. En otra ventana de terminal, ejecuta:
   ```bash
   ngrok tcp 5555
   ```
5. ngrok te mostrará una línea como esta:
   ```
   Forwarding   tcp://0.tcp.ngrok.io:14522 -> localhost:5555
   ```
6. **¡Listo!**
   - Tú te conectas escribiendo en el juego: `127.0.0.1:5555` (o dando clic en "Hostear Partida").
   - Tus amigos en sus casas escriben en el juego: `0.tcp.ngrok.io:14522` (pueden pegarlo con `Ctrl+V`).

### Con **playit.gg**:
1. Descarga el programa desde [playit.gg](https://playit.gg/).
2. Añade un túnel de tipo **TCP** apuntando al puerto **5555**.
3. Copia la dirección que te asigna (ej: `bomberman-partida.playit.gg:34211`) y pásasela a tus amigos.

---

## ☁️ OPCIÓN 2: Servidor en la Nube 24/7 (Railway / Koyeb / Docker)
Si quieres que el servidor esté encendido todo el tiempo sin depender de tu computadora:

1. El proyecto ya incluye el archivo **`Dockerfile`** y **`requirements.txt`** configurados.
2. Sube la carpeta a un repositorio de **GitHub**.
3. Entra a [railway.app](https://railway.app/) o [koyeb.com](https://www.koyeb.com/) y conecta tu repositorio de GitHub.
4. Railway detectará automáticamente el `Dockerfile`.
5. En la configuración de Railway / Koyeb, activa un **TCP Proxy** exponiendo el puerto `5555`.
6. Railway te dará un dominio público con puerto (por ejemplo: `roundhouse.proxy.rlwy.net:21045`).
7. Todos los jugadores escriben esa dirección en el menú del juego y juegan juntos 24/7.

---

## 🐧 OPCIÓN 3: En un VPS Linux (Oracle Cloud Always Free / DigitalOcean / AWS EC2)
Si tienes un servidor VPS Linux (Ubuntu / Debian):

1. Conéctate por SSH a tu servidor:
   ```bash
   ssh usuario@tu_servidor_ip
   ```
2. Instala Python y las librerías SDL necesarias:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0
   ```
3. Clona o sube los archivos del juego a tu servidor.
4. Instala las dependencias:
   ```bash
   pip3 install -r requirements.txt
   ```
5. Abre el puerto 5555 en tu firewall / Cloud Security Group:
   ```bash
   sudo ufw allow 5555/tcp
   ```
6. Inicia el servidor en segundo plano:
   ```bash
   nohup python3 server.py --host 0.0.0.0 --port 5555 > server.log 2>&1 &
   ```
7. Para unirte, tú y tus amigos simplemente ponen en el juego:
   ```
   TU_IP_PUBLICA_VPS:5555
   ```

---

## 🎮 Cómo Jugar desde el Menú del Juego

1. Ejecuta el juego abriendo **`iniciar.bat`** o con:
   ```bash
   python main.py
   ```
2. En el Menú Principal, selecciona **MODO MULTIJUGADOR**.
3. Haz clic en **CONECTARSE**.
4. Escribe tu nombre de jugador.
5. En el campo de dirección, escribe o pega con `Ctrl+V` la dirección del servidor (ejemplo: `0.tcp.ngrok.io:14522` o `127.0.0.1:5555`).
6. Presiona **CONECTAR**.
7. En la sala de espera, presiona **ENTER** o haz clic en **JUGAR** para iniciar la partida cuando todos estén listos.
8. ¡A divertirse derrotando a los enemigos y encontrando la puerta secreta!

