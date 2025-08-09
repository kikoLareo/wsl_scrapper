# WSL Spanish Surfers Data Scraper

Sistema avanzado de scraping y análisis estadístico para obtener datos de surfistas españoles de la World Surf League (WSL).

## 🏄‍♂️ Características

- **Scraping completo**: Extrae datos de surfistas de España, País Vasco y Canarias
- **Análisis estadístico avanzado**: Calcula medias por playas, rondas, tendencias temporales
- **Arquitectura modular**: Sistema de subagentes especializados 
- **Exportación múltiple**: JSON, CSV, Excel con análisis detallado
- **Ejecución manual**: Optimizado para actualizaciones periódicas

## 📋 Surfistas Incluidos

El sistema está configurado para extraer datos de surfistas españoles incluyendo:
- **España**: Surfistas con nacionalidad española
- **País Vasco**: Competidores representando al País Vasco  
- **Canarias**: Surfistas de las Islas Canarias

### Surfistas Confirmados
- Aritz Aranburu (País Vasco)
- Juan Fernández (España)  
- Alex Hontoria (España)
- Juanjo Fernández (España)

## 🚀 Instalación

```bash
# Clonar archivos del proyecto
# Instalar dependencias
pip install -r requirements.txt
```

> **Nota:** las dependencias son de Python, por lo que debe usarse `pip`.
> Comandos como `npm install requirements.txt` fallarán.

## ⚙️ Configuración

El sistema incluye varios componentes especializados:

### Subagentes Claude Code
- **wsl-scraper-orchestrator**: Coordinador principal
- **wsl-web-analyzer**: Análisis técnico de la web WSL
- **wsl-data-extractor**: Extracción masiva de datos

### Estructura de Datos
- `wsl_data_structure.py`: Definición completa de modelos de datos
- `wsl_scraper_main.py`: Script principal de scraping
- `wsl_statistics_analyzer.py`: Sistema de análisis estadístico

## 📊 Uso

### 1. Scraping Básico (Modo Test)
```bash
python wsl_scraper_main.py --test
```
Ejecuta análisis técnico sin scraping completo.

### 2. Extracción Completa
```bash
python wsl_scraper_main.py
```
Ejecuta extracción completa de todos los surfistas españoles.

### 3. Análisis Estadístico
```bash
python wsl_statistics_analyzer.py data/exports/wsl_spanish_surfers_[timestamp].json
```

## 📁 Estructura de Archivos Generados

```
data/
├── checkpoints/          # Puntos de control durante extracción
├── exports/              # Datos exportados finales
│   ├── wsl_spanish_surfers_[timestamp].json
│   ├── wsl_spanish_surfers_[timestamp]_surfers.csv  
│   ├── wsl_spanish_surfers_[timestamp]_events.csv
│   └── wsl_spanish_surfers_[timestamp]_heats.csv
└── analysis_[timestamp].xlsx  # Análisis estadístico completo
```

## 📈 Análisis Estadístico Incluye

### Por Surfista
- Puntuación media por manga
- Tasa de avance entre rondas
- Porcentaje de olas excelentes (8.0+)
- Índice de consistencia
- Progresión temporal de rendimiento

### Por Ubicación/Playa
- Rendimiento medio por tipo de ola (Beach Break, Reef Break, Point Break)
- Comparativas entre ubicaciones geográficas
- Análisis de condiciones óptimas

### Por Tipo de Competición
- Championship Tour (CT) vs Challenger Series (CS)
- Rendimiento por ronda (Round 1, Cuartos, Semifinales, Final)
- Análisis de presión por eliminatorias

### Comparativas
- Rankings entre surfistas españoles
- Comparación País Vasco vs España vs Canarias
- Evolución temporal del surf español
- Identificación de actuaciones pico

## 🔧 Configuración Avanzada

### Rate Limiting
```python
# En wsl_scraper_main.py
MIN_DELAY = 1.0  # Mínimo 1 segundo entre requests  
MAX_DELAY = 3.0  # Máximo 3 segundos
```

### Países/Regiones Objetivo  
```python
TARGET_COUNTRIES = [
    "Spain",
    "Basque Country", 
    "Canary Islands"
]
```

### URLs Base Analizadas
- `https://www.worldsurfleague.com/athletes/tour/mct` - Men's Championship Tour
- `https://www.worldsurfleague.com/athletes/tour/wct` - Women's Championship Tour  
- `https://www.worldsurfleague.com/athletes/tour/mcs` - Men's Challenger Series
- `https://www.worldsurfleague.com/athletes/tour/wcs` - Women's Challenger Series

## 🛠️ Arquitectura Técnica

### Análisis Web Realizado
- ✅ Identificación de URLs de perfil de surfistas
- ✅ Patrones de extracción de datos HTML
- ✅ Selectores CSS para información de atletas
- ✅ Sistema de filtrado por país
- ✅ Manejo de paginación y limitaciones

### Protecciones Anti-Scraping
- Rate limiting ético implementado
- Headers de navegador real configurados
- Delays aleatorios entre requests
- Sistema robusto de reintentos
- Manejo gracioso de errores

## 📋 Datos Extraídos

### Por Surfista
- **Información personal**: Nombre, país, stance, hometown
- **Carrera profesional**: Años activos, títulos mundiales
- **Estadísticas**: Victorias, earnings, rankings

### Por Competición  
- **Evento**: Nombre, ubicación, fechas, tipo de tour
- **Condiciones**: Tipo de ola, condiciones del mar
- **Resultados**: Posición final, puntos ganados

### Por Manga
- **Ronda**: Nombre de la ronda, duración
- **Puntuaciones**: Score total, puntuaciones individuales de olas
- **Resultado**: Posición, si avanzó, oponentes

### Por Ola Individual
- **Puntuación**: Score de 0-10
- **Características**: Excelencia (8.0+), prioridad, interferencias
- **Timing**: Momento en la manga

## 🚨 Consideraciones Legales

- ✅ Respeta términos de servicio de WSL
- ✅ Rate limiting ético implementado  
- ✅ Solo datos públicos accedidos
- ✅ No sobrecarga servidores WSL
- ✅ Uso educativo/analítico de datos

## 📞 Soporte

Para soporte oficial de WSL API:
- Email: support@worldsurfleague.com
- Teléfono: +1 310 450 1212

## 🔄 Actualizaciones

Ejecutar manualmente el script de forma periódica (recomendado cada 2-3 meses) para mantener datos actualizados con nuevas competiciones y resultados.

## 📊 Ejemplos de Análisis

### Comando Completo de Ejecución
```bash
# 1. Scraping completo
python wsl_scraper_main.py

# 2. Análisis estadístico  
python wsl_statistics_analyzer.py data/exports/wsl_spanish_surfers_20250808_143022.json

# Resultado: Análisis comprehensivo en Excel y JSON
```

### Métricas Clave Generadas
- **Overall Score**: Puntuación general ponderada (0-100)
- **Consistency Index**: Medida de regularidad en el rendimiento  
- **Pressure Performance**: Rendimiento bajo presión (finales vs rondas tempranas)
- **Wave Type Affinity**: Preferencias por tipos de ola
- **Career Progression**: Evolución temporal del surfista

El sistema está diseñado para proporcionar insights profundos sobre el rendimiento de los surfistas españoles en el circuito mundial, facilitando análisis comparativos y identificación de patrones de rendimiento.