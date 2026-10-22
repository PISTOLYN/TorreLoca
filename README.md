# TORRE LOCA · Desafíos Locos

Videojuego de PC para dos jugadores (Equipo Azul vs. Equipo Rojo). Cada equipo tiene su propio
tablero y su propio pulsador: una barra de bloques va y viene por la fila actual, el jugador la
detiene, **solo se conserva lo que coincide con la fila de abajo** y el primero en llegar a la cima gana.

> **Estado de la entrega:** `TorreLoca.exe` e `InstalarTorreLoca.exe` **todavía no están generados ni
> probados**: se crean en una PC con Windows ejecutando `build.bat` (ver abajo). Qué se probó y qué no
> está en la sección *Pruebas*.

## Estructura

```
TorreLoca/
├── main.py                    Punto de entrada (--probar-controles para diagnosticar pulsadores)
├── requirements.txt           pygame (opcional: opencv-python para demo.mp4)
├── build.bat                  Pruebas + TorreLoca.exe + InstalarTorreLoca.exe
├── installer/TorreLoca.iss    Script de Inno Setup 6
├── assets/                    logo.png, (sonidos/*.wav, demo.mp4, icono.ico opcionales)
├── torreloca/
│   ├── logica.py              Torre y Partida (reglas, puntos, victoria, bloqueo) - sin pygame
│   ├── jugadores.py           Nombres/colores, teclas y pulsadores físicos, diagnóstico
│   ├── tableros.py            Dibujo de cada tablero: rejilla, bloques, marcador, parpadeo, X
│   ├── menu.py                Menú del operador (tecla M)
│   ├── configuracion.py       Preferencias guardadas en JSON
│   ├── audio.py               Sonidos sintetizados (o WAV propios)
│   ├── graficos.py            Fondo neón, textos, luces, logo, bloques
│   ├── instrucciones.py       Pantalla de instrucciones y demostración
│   ├── juego.py               Bucle principal y estados
│   └── rutas.py               Rutas de recursos/datos (válidas dentro del .exe)
└── tests/                     test_logica.py y test_funcional.py
```

## Cómo se juega

1. **ENTER** en la pantalla de inicio → instrucciones → **ENTER** → cuenta regresiva 3-2-1-¡YA!
2. Cada equipo presiona su pulsador (por defecto **A** = Azul, **L** = Rojo) para detener su barra.
3. Cada apilación válida suma los puntos configurados (100 por defecto). Si una apilación no toca la
   fila de abajo, esa torre se derrumba y vuelve a empezar (los puntos se conservan).
4. El primero en llenar todas las filas gana: su tablero **parpadea** y suena la victoria una vez;
   el otro muestra una **X** fija. Pulsadores y contadores quedan bloqueados.
5. El operador reinicia con **R** (o **ENTER**) en la pantalla final, o desde el menú.

Teclas del operador: **M** menú · **R** reiniciar · **ENTER** continuar · **F11** pantalla completa · **D** demo (en instrucciones).

## Menú del operador (M)

La partida queda en pausa mientras está abierto. Permite: continuar, reiniciar, asignar tecla o
pulsador a cada equipo, volumen, sonidos, puntos por apilación, filas, columnas, velocidad, efectos
visuales, pantalla completa/ventana, restaurar valores predeterminados, leer instrucciones, ver la
demostración y cerrar el programa. Las preferencias se guardan en `%APPDATA%\TorreLoca\configuracion.json`
y se conservan al reabrir. Cambiar puntos, filas, columnas o velocidad reinicia la partida al salir del menú.
La resolución es adaptable: la ventana se puede redimensionar y el juego se escala conservando la proporción 16:9.

## Compilar e instalar (Windows 10/11)

Requisitos: Python 3.10+ (marcando "Add to PATH") y, para el instalador, [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```bat
build.bat
```

Hace, en orden: crea `.venv`, instala `pygame` y `pyinstaller`, **ejecuta las pruebas** (si fallan, se detiene),
genera `dist\TorreLoca.exe` y, si Inno Setup está instalado, `dist\InstalarTorreLoca.exe`. Comandos equivalentes a mano:

```bat
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt pyinstaller
python -m unittest discover -s tests -v
pyinstaller --noconfirm --clean --onefile --windowed --name TorreLoca --add-data "assets;assets" main.py
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\TorreLoca.iss
```

Para probar sin compilar: `pip install -r requirements.txt` y `python main.py`.
El juego funciona **sin internet**: todos los recursos van dentro del ejecutable.

## Pulsadores físicos

- **Botoneras arcade con interfaz USB tipo teclado** (Zero Delay, I-PAC, etc.): se comportan como teclas.
  Programa cada pulsador para que envíe una tecla y asígnala en el menú (M → "CONTROL EQUIPO ...").
- **Mandos/pulsadores USB (HID joystick)**: conéctalos antes de abrir el juego (o con el juego abierto)
  y, en el menú, elige "CONTROL EQUIPO ..." y **presiona el pulsador**; se guarda como `joy:<dispositivo>:<botón>`.
- **Diagnóstico:** `TorreLoca.exe --probar-controles` (o `python main.py --probar-controles`) muestra el
  código de cada tecla/pulsador detectado y cuántos dispositivos ve Windows. ESC para salir.
- El teclado siempre sigue funcionando como alternativa. No se admiten como pulsadores M, R, ENTER, ESC ni F11.
- Si cambias el orden de conexión de dos mandos, vuelve a asignarlos (el identificador depende del orden).

## Personalización

- `assets/logo.png`: logo central (se incluyó el de DESAFÍOS LOCOS tomado de tu tablero de referencia).
- `assets/sonidos/<nombre>.wav`: reemplaza un sonido (`inicio, cuenta, ya, apilar, fallo, menu, reinicio, victoria`).
- `demo.mp4`: colócalo junto a `TorreLoca.exe` (o en `assets/` antes de compilar). Requiere `pip install opencv-python`
  y se reproduce sin audio. Si no existe o no se puede abrir, se muestra la demostración animada integrada.
- Errores inesperados se registran en `%APPDATA%\TorreLoca\error.log`.

## Pruebas

```bat
python -m unittest discover -s tests -v
```

| Requisito del documento | Prueba |
|---|---|
| Competencia simultánea, puntuación | `test_competencia_simultanea_y_puntuacion`, `test_ambas_barras_se_mueven_a_la_vez` |
| Victoria, parpadeo del ganador, X del perdedor, sonido una vez | `test_victoria_parpadeo_x_y_bloqueo` |
| Bloqueo de controles y contadores congelados al terminar | `test_victoria_parpadeo_x_y_bloqueo`, `test_primero_en_la_cima_gana_y_se_bloquea_todo` |
| Reinicio borra ambos tableros y restablece contadores | `test_reinicio_borra_tableros_y_rehabilita_controles` |
| Tecla M (pausa) | `test_tecla_m_pausa_y_reanuda` |
| Controles configurables y persistentes | `test_controles_configurables_y_persistentes` |
| Sonidos, pantalla completa | `test_sonidos_disponibles`, `test_pantalla_completa_con_f11` |
| Funcionamiento sin conexión | `test_funciona_sin_conexion` (falla si el juego abre un socket) |

**Qué se ejecutó al preparar esta entrega:** las 15 pruebas de `test_logica.py` (reglas y configuración) con
Python real, y las 14 de `test_funcional.py` contra un sustituto mínimo de pygame, lo que valida los estados,
eventos, menú, pausa, bloqueo y reinicio. **No se ejecutó pygame real**, así que falta confirmar en tu PC el
aspecto visual (neón, parpadeo, X, tamaños), el audio real, el pulsador físico, la pantalla completa y la
generación de `TorreLoca.exe`/`InstalarTorreLoca.exe`. Correr `build.bat` ejecuta las pruebas con pygame real.

## Compilar en GitHub (sin instalar nada en tu PC)

1. Crea un repositorio en GitHub y sube **todo el contenido** de la carpeta `TorreLoca` (incluida `.github/`).
2. Abre la pestaña **Actions**: el flujo "Compilar TORRE LOCA" corre solo con cada subida
   (o con el botón *Run workflow*). Usa un servidor Windows, ejecuta las pruebas con pygame real y compila.
3. Cuando termine en verde, entra a esa ejecución y descarga el artefacto **TorreLoca-Windows**
   (contiene `TorreLoca.exe` e `InstalarTorreLoca.exe`).
4. Para publicarlo como versión descargable: crea una etiqueta, p. ej. `git tag v1.0.0 && git push origin v1.0.0`;
   los dos archivos aparecerán en **Releases**.
Si algún paso sale en rojo, abre el registro de ese paso: las pruebas fallidas muestran cuál requisito falló.
