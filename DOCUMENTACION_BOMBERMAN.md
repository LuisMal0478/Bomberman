# 💣 DOCUMENTACIÓN TÉCNICA Y MANUAL DE USUARIO
# PROYECTO FINAL: BOMBERMAN 3D MULTIJUGADOR EN LA NUBE

**Autor:** Luis Maldonado  
**Repositorio GitHub:** [https://github.com/LuisMal0478/Bomberman](https://github.com/LuisMal0478/Bomberman)  
**Servidor Cloud Activo (Railway):** `maglev.proxy.rlwy.net:24413`  
**Tecnologías:** Python 3.12, Pygame 2.6, Sockets TCP, Docker, Railway Cloud  
**Documento Word Generado:** `DOCUMENTACION_BOMBERMAN.docx`  

---

## 1. Resumen Ejecutivo
El presente proyecto corresponde al desarrollo e implementación completa de un videojuego basado en el clásico arcade Bomberman, modernizado con modelos gráficos pseudo-3D, inteligencia artificial adaptativa y un subsistema de redes de alto rendimiento alojado en la nube pública.

El propósito fundamental del software es demostrar la integración de conceptos clave de las ciencias de la computación, tales como el patrón arquitectónico Modelo-Vista-Controlador (MVC), sincronización de estados distribuidos mediante sockets TCP, contenedorización mediante Docker y técnicas de renderizado fluido con corrección de colisiones y deslizamiento de esquinas.

---

## 2. Arquitectura del Software

### 2.1 Módulos y Responsabilidades
| Módulo / Archivo | Rol | Responsabilidad |
| :--- | :--- | :--- |
| `main.py` / `iniciar.bat` | Entrada Principal | Punto de entrada del juego con menú interactivo completo. |
| `main_mvc.py` | Entrada MVC | Ejecuta la versión estructurada estrictamente bajo el patrón MVC. |
| `menu.py` | Controlador de Menú | Gestión de menús, pegado rápido con Ctrl+V, selector de personajes y conexión a red. |
| `game.py` | Motor de Juego | Ciclo principal a 60 FPS, colisiones, mapa, puerta y enemigos. |
| `server.py` | Servidor Headless | Servidor socket TCP multihilo capaz de operar en la nube sin monitor. |
| `client.py` | Cliente de Red | Sincronización socket con el servidor local o remoto en Railway. |
| `modelos/` | Capa Modelo | Entidades lógicas: Jugador, Bomba, Enemigo, Mapa, Mejora y ModeloJuego. |
| `vistas/` | Capa Vista | Renderizado gráfico de pantalla, animaciones, HUD y efectos de sonido. |
| `controladores/` | Capa Controlador | Mapeo de entradas de teclado/mouse y sincronización entre Modelo y Vista. |
| `red/` | Capa de Red | Protocolo socket estructurado para la arquitectura MVC. |

---

## 3. Mecánicas del Videojuego

### 3.1 Clases de Personajes Jugables
| Personaje | Velocidad | Potencia Fuego | Bombas Máx. | Especialidad |
| :--- | :--- | :--- | :--- | :--- |
| **Bomberman** | 3.0 px/frame | 2 casillas | 1 bomba | Equilibrado para todo tipo de juego |
| **Fire Starter** | 2.7 px/frame | 3 casillas | 1 bomba | Explosiones de largo alcance |
| **Speed Demon** | 3.8 px/frame | 1 casilla | 1 bomba | Velocidad extrema para evasión |
| **Tank** | 2.4 px/frame | 2 casillas | 3 bombas | Colocación masiva de trampas |

### 3.2 Los 8 Enemigos Reales
| Enemigo | HP | Velocidad | Puntos | Traspasa Bloques | Comportamiento IA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Balloom (Globo)** | 1 | 1.2 px/f | 100 pts | No | Patrullaje errático lento (30% persecución) |
| **Oneal (Gota Azul)** | 1 | 1.6 px/f | 200 pts | No | Persecución activa al jugador (55%) |
| **Doll (Barril)** | 1 | 1.8 px/f | 300 pts | No | Velocidad media y persecución moderada |
| **Minvo (Minvo)** | 2 | 2.1 px/f | 400 pts | No | Resistente a 2 bombas, alta velocidad |
| **Fantasma** | 1 | 1.9 px/f | 500 pts | Sí (Aura púrpura) | Traspasa ladrillos buscando emboscadas |
| **Ovapi (Masa)** | 1 | 1.7 px/f | 600 pts | Sí (Aura celeste) | Traspasa ladrillos y patrulla pasillos |
| **Pass (Fiera)** | 2 | 2.4 px/f | 700 pts | No | Extrema velocidad, persecución al 90% |
| **Pontan (Pontan)** | 2 | 2.5 px/f | 800 pts | Sí (Aura roja) | Máxima dificultad: veloz y traspasa muros |

### 3.3 Mecánica de la Puerta Secreta
1. **Oculta:** Invisible bajo un ladrillo aleatorio. Se revela al destruir el ladrillo con fuego.
2. **Bloqueada:** Si aún hay enemigos, muestra rejas de hierro y un candado dorado.
3. **Abierta:** Al eliminar a todos los enemigos de la ronda, se transforma en un portal vórtice cósmico interactivo (`EXIT`) que premia con **+1000 puntos** y avanza de nivel.

### 3.4 Paso a través de Bombas (*Bomb Pass*) y Auto-centrado
- **Auto-centrado perpendicular:** El jugador se alinea automáticamente en el eje perpendicular del pasillo mientras camina, evitando choques con las esquinas salientes de los muros.
- **Paso a través de bombas:** Las bombas no bloquean la máscara de colisión de los jugadores. Puedes colocar una bomba y avanzar a través de ella en cualquier dirección sin quedar atrapado, mientras que los enemigos normales quedan bloqueados por ella.

---

## 4. Servidor en la Nube (Railway Cloud)
- **Servidor Headless:** Variables de entorno `SDL_VIDEODRIVER=dummy` y `SDL_AUDIODRIVER=dummy` permiten ejecutar el motor matemático sin monitor.
- **Escucha Dual:** Soporta puertos 5555 y 8080 simultáneamente.
- **Instancia Activa:** `maglev.proxy.rlwy.net:24413`

---

## 5. Manual de Usuario y Controles

| Tecla / Acción | Función |
| :--- | :--- |
| **W, A, S, D / Flechas** | Moverse en las 4 direcciones |
| **ESPACIO** | Colocar bomba |
| **F11** | Alternar Pantalla Completa |
| **ESC** | Pausa o volver al menú principal |
| **Ctrl + V** | Pegar dirección del servidor en el menú multijugador |
| **ENTER** | Iniciar partida en la sala de espera |

---

## 6. Archivos y Lanzadores
- **`iniciar.bat`**: Inicia el juego.
- **`DOCUMENTACION_BOMBERMAN.docx`**: Documentación completa en formato Microsoft Word.
- **`subir_a_github.bat`**: Script para sincronizar con GitHub.
- **`iniciar_servidor_ngrok.bat`**: Alternativa para jugar por túnel ngrok.
- **`iniciar_servidor.bat`**: Servidor local en el puerto 5555.
