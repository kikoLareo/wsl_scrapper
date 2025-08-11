## Quick Start

1) Crear entorno e instalar dependencias
```bash
cd /Users/kikolareogarcia/Desktop/Proyects/wsl_scrapper/wsl_scrapper
python3 -m venv venv
source venv/bin/activate
pip3 install --disable-pip-version-check -r requirements.txt
```

2) Interfaz web (recomendada)
```bash
python ui_app.py
```
Abrir: `http://127.0.0.1:5000`

3) CLI (opcional)
```bash
python wsl_surfer_focused.py --years 2025 --countries ESP BAS CAN --tours CT CS QS --max-workers 8 --request-delay 0.4
```

Salidas en `data/runs/<timestamp>/` y copias estables en `data/stable/`.