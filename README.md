## WSL Spanish Surfers Scraper

Sistema de scraping y exportación de datos de surfistas españoles (España, País Vasco, Canarias) de la World Surf League (WSL), con interfaz web para seleccionar filtros y barra de progreso.

### Funcionalidades clave
- Extracción por surfista y año: eventos, rondas y heats con puntuaciones de olas.
- Filtros por años, países/regiones, tours y surfistas concretos. Opcionalmente por ubicaciones/playas cuando se detectan.
- Interfaz web (Flask) con estado, porcentaje y ETA; descargas de resultados.
- Salidas normalizadas en JSON/JSONL/CSV y copias “estables” sin timestamp.

---

## 1) Requisitos e instalación

Recomendado Python 3.9+ y entorno virtual.

```bash
cd wsl_scrapper
python3 -m venv venv
source venv/bin/activate
pip3 install --disable-pip-version-check -r requirements.txt
```

Notas:
- Si ves “bash: pip: command not found”, usa `pip3` como arriba.
- El aviso “NotOpenSSLWarning (LibreSSL)” es solo un warning de urllib3; puede ignorarse.

---

## 2) Interfaz web (recomendada)

Lanzar la app:
```bash
source venv/bin/activate
python ui_app.py
```

Abrir en el navegador: `http://127.0.0.1:5000`

En la página principal podrás:
- Seleccionar años, países/regiones (ESP, BAS, CAN), tours (CT, CS, QS, Longboard, Junior, Big-Wave).
- Especificar surfistas (IDs o nombres) separados EXCLUSIVAMENTE por comas. Ejemplo: `10158, Yago Dominguez, Leticia Canales Bilbao`. Los nombres admiten espacios; el filtrado es por coincidencia parcial (case-insensitive).
- Seleccionar ubicaciones/playas (si existen en la última corrida guardada).
- Ajustar concurrencia (`max_workers`) y retardo entre peticiones (`request_delay`).

Durante la ejecución:
- Verás barra de progreso, porcentaje, y ETA por número de surfistas procesados.
- Logs con eventos relevantes (tours encontrados, heats detectados…).

Al finalizar:
- Descargas directas desde la página de estado del job y la portada: `surfers_raw.json`, `heats_raw.jsonl`, `heats_raw.csv`, `surfers_summary.csv`, `surfers_full.json`, `surfers_2025.json`.
- Persistencia de jobs: si el servidor reinicia, los jobs quedan guardados como `interrupted` y puedes verlos en `/jobs`.

---

## 3) Uso por línea de comandos (CLI)

```bash
source venv/bin/activate
python wsl_surfer_focused.py \
  --years 2025 \
  --countries ESP BAS CAN \
  --tours CT CS QS \
  --surfers 10158 "Adur Amatriain" \
  --max-workers 8 \
  --request-delay 0.4
```

Parámetros disponibles:
- `--years`: uno o varios años (p. ej., 2024 2025).
- `--countries`: códigos `ESP BAS CAN` (España, País Vasco, Canarias).
- `--tours`: CT, CS, QS, LONGBOARD, JUNIOR, BIG-WAVE (opcional).
- `--surfers`: IDs o nombres de surfistas (opcional).
- `--max-workers`: hilos en paralelo (por defecto 5).
- `--request-delay`: retardo entre requests (segundos, por defecto 0.5).

---

## 4) Estructura de directorios y salidas

La ejecución genera datos en `data/` siguiendo estas convenciones:

- `data/runs/<timestamp>/`
  - `surfers_raw.json`: lista simple de surfistas y sus eventos/heats (JSON).
  - `heats_raw.jsonl`: filas planas por heat (JSON Lines, una línea por heat).
  - `heats_raw.csv`: igual que el JSONL pero en CSV.
  - `surfers_summary.csv`: resumen por surfista (conteos y tours).
  - `surfers_full.json`: versión completa de la ejecución (estructura por surfista).
  - `surfers_2025.json`: si la corrida fue de 2025, versión nominal equivalente.

- `data/stable/` (copias “estables”, sobrescritas en cada corrida)
  - `all_surfers_raw.json`
  - `all_heats_raw.jsonl`
  - `all_heats_raw.csv`

- `data/checkpoints/`
  - `options_latest.json`: opciones detectadas (años, tours, surfistas, ubicaciones). La UI usa este archivo para poblar lists.

- `data/surfers/`
  - Un archivo por surfista procesado: `ID_Nombre.json`

---

## 5) Esquemas de datos

### 5.1 Surfer (estructura por surfista)
```json
{
  "surfer_id": "10158",
  "name": "Adur Amatriain",
  "country": "Basque Country",
  "events": [
    {
      "event_id": "4889",
      "event_name": "ABANCA Pantin Classic Galicia Pro",
      "location": "Pantin",
      "tour_type": "WQS",
      "start_date": null,
      "final_position": 9,
      "points_earned": 650,
      "heats": [
        {
          "heat_id": "heat_106821",
          "round_name": "Round of 64",
          "position": 1,
          "total_score": 12.5,
          "wave_scores": [6.4, 4.9, 1.2],
          "advanced": true,
          "heat_date": null
        }
      ]
    }
  ]
}
```

### 5.2 Fila de heat (heats_raw.jsonl / heats_raw.csv)
```json
{
  "surfer_id": "10158",
  "surfer_name": "Adur Amatriain",
  "country": "Basque Country",
  "event_id": "4889",
  "event_name": "ABANCA Pantin Classic Galicia Pro",
  "event_location": "Pantin",
  "tour_type": "WQS",
  "event_final_position": 9,
  "event_points_earned": 650,
  "heat_id": "heat_106821",
  "round_name": "Round of 64",
  "heat_position": 1,
  "heat_total_score": 12.5,
  "heat_advanced": true,
  "heat_date": null,
  "wave_scores": [6.4, 4.9, 1.2]
}
```

Campos clave:
- `wave_scores` en CSV se serializa como string con separador `|`.
- `location` puede inferirse del nombre del evento cuando el HTML no lo aporta explícitamente.

---

## 6) Flujo interno (resumen)
1. `get_surfers()` descarga el directorio de atletas filtrando por países (ESP/BAS/CAN) y resuelve la paginación.
2. Por cada surfista y año seleccionado, `get_surfer_events()` recorre los tours disponibles (selector `yearResultsTourCode`).
3. Para cada evento, `_get_event_details()` extrae heats y resultados; `_extract_surfer_heats()` parsea elementos reales `div.hot-heat`.
4. Se guardan archivos incrementales por surfista y, al final, las salidas agregadas (JSON/JSONL/CSV) y copias estables.
5. Se actualiza `data/checkpoints/options_latest.json` con años/tours/surfistas/ubicaciones detectadas.

---

## 7) Consejos de rendimiento
- Incrementa `--max-workers` en máquinas con buena conexión (p. ej., 8–16). Ajusta `--request-delay` a 0.3–0.5s.
- Filtra por tours o surfistas concretos para recortar tiempo.
- Usa la UI para monitorizar progreso y ETA.

---

## 8) Solución de problemas
- “flask: command not found”: activa el venv y asegúrate de instalar dependencias con `pip3 install -r requirements.txt`.
- “pip: command not found” en el venv: usa `pip3`.
- Aviso `NotOpenSSLWarning`: es un warning de urllib3 (LibreSSL), ignorable.
- `data/stable/*.json` vacío (`[]`): las copias estables se sobrescriben en cada corrida; revisa `data/runs/<timestamp>/` o ejecuta una nueva extracción.

---

## 9) Referencias de archivos clave
- `wsl_surfer_focused.py`: núcleo de scraping (CLI y lógica de extracción/guardado).
- `ui_app.py`: interfaz Flask con filtros, progreso/ETA y descargas.
- `config.py`: años y países/regiones por defecto y mapping de IDs internos de WSL.
- `data/`: salidas y checkpoints.

---

## 10) Licencia y uso
Proyecto para propósitos analíticos/educativos. Respeta los términos de servicio de WSL y no sobrecargues sus servidores (usa delays razonables).
