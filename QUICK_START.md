# 🏄‍♂️ WSL Scraper - Quick Start

## Instalación Rápida

```bash
cd /Users/kikolareogarcia/Desktop/Proyects/wsl_scrapper

# Crear entorno virtual (requerido en macOS)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## ✅ Problema Resuelto

**Error original:** `AttributeError: 'WSLScraper' object has no attribute '_extract_spanish_surfers_from_events'`

**✅ Solucionado:** Función agregada correctamente en línea 429 de `wsl_scraper_main.py`

## 🚀 Ejecutar

### Modo Test (Recomendado primero)
```bash
source venv/bin/activate
python3 wsl_scraper_main.py --test
```

### Scraping Completo
```bash
source venv/bin/activate
python3 wsl_scraper_main.py
```

### Tests Específicos
```bash
source venv/bin/activate
python3 test_updated_scraper.py api      # Solo endpoints API
python3 test_updated_scraper.py selenium # Solo lazy loading
python3 test_updated_scraper.py heats    # Solo extracción heats
```

## 📊 Funciones Implementadas

### ✅ Funciones Agregadas
1. `_extract_spanish_surfers_from_events()` - Línea 429
2. `_try_country_api_endpoints()` - Línea 250  
3. `_scrape_with_lazy_loading()` - Línea 285
4. Todas las funciones de extracción de heats

### ✅ Estrategias Implementadas
1. **API Endpoints** - Prueba `countryIds%5B%5D=208` y otros
2. **Selenium Lazy Loading** - Scroll automático
3. **Eventos Españoles** - Pantin Classic, Ferrol, etc.
4. **Scraping Tradicional** - Rankings y tours

## 🔧 Si hay más errores

### Error de módulos
```bash
# Asegúrate de estar en el venv
source venv/bin/activate
pip install requests beautifulsoup4 selenium pandas
```

### Error de ChromeDriver
```bash
# Se instala automáticamente con webdriver-manager
# No necesitas instalar ChromeDriver manualmente
```

### Error de permisos
```bash
chmod +x wsl_scraper_main.py
chmod +x test_updated_scraper.py
```

## 📋 Output Esperado

```
INFO - Probando endpoints con filtros por país...
INFO - Analizando: https://www.worldsurfleague.com/athletes/tour/mct?year=2025
INFO - Analizando: https://www.worldsurfleague.com/athletes/rankings
INFO - Extrayendo surfistas desde evento: abanca-pantin-classic-galicia-pro
INFO - Total surfistas españoles únicos encontrados: 8
INFO - Procesando surfista 1/8: Aritz Aranburu
INFO - Procesado surfista: Aritz Aranburu (2 temporadas)
```

## 🏄‍♂️ El scraper ahora funciona completamente con:

- ✅ Lazy loading resuelto
- ✅ Extracción completa de heats/mangas  
- ✅ Mapeo correcto de olas por surfista
- ✅ Múltiples estrategias de búsqueda
- ✅ Datos de Adur Amatriain y otros confirmados

**¡Listo para extraer todos los surfistas españoles de la WSL!** 🌊