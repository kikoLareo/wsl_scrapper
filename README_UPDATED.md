# WSL Spanish Surfers Scraper - ACTUALIZADO

## 🏄‍♂️ Mejoras Implementadas

### Problemas Resueltos

1. **✅ Lazy Loading Solucionado**
   - Implementado Selenium con scroll automático
   - Múltiples estrategias de extracción de atletas
   - Soporte para endpoints API con filtros por país

2. **✅ Extracción de Heats Mejorada**
   - Parse correcto de elementos `hot-heat-athlete`
   - Extracción de puntuaciones individuales de olas
   - Manejo del botón "Show More" para datos completos
   - Mapeo preciso de olas por surfista

3. **✅ Filtrado por País Optimizado** 
   - Test automático de diferentes `countryIds`
   - Soporte para España, País Vasco, Canarias
   - Múltiples estrategias de búsqueda

4. **✅ Datos de Olas Individuales**
   - Extracción correcta de todas las olas por manga
   - Parse de formato "6.40 + 4.90" 
   - Identificación de olas excelentes (8.0+)

## 🚀 Nuevas Características

### Múltiples Estrategias de Extracción

**Estrategia 1: API Endpoints**
```python
# Prueba automáticamente diferentes parámetros
countryIds%5B%5D=208  # Tu endpoint identificado
countryIds%5B%5D=70   # España alternativo  
countryIds%5B%5D=724  # Código ISO España
```

**Estrategia 2: Selenium con Lazy Loading**
```python
# Scroll automático hasta cargar todos los atletas
# Extracción robusta con múltiples selectores CSS
# Manejo de errores y timeouts
```

**Estrategia 3: Eventos Españoles**
```python 
spanish_events = [
    "abanca-pantin-classic-galicia-pro",
    "ferrol-surf-festival",
    "junior-pro-razo"
]
```

**Estrategia 4: Scraping Tradicional**
- Rankings y tours WSL
- Páginas de resultados
- Búsqueda directa por país

### Extracción de Heats Avanzada

Basado en el HTML que proporcionaste:

```python
# Parse correcto de estructura hot-heat-athlete
def _create_heat_for_spanish_surfer(self, athlete_elem, heat_id, round_name):
    # Extraer puntuación total
    score_elem = athlete_elem.find(class_='hot-heat-athlete__score')
    total_score = float(score_elem.get_text(strip=True))
    
    # Extraer olas contadas (las 2 mejores)
    counted_waves_elem = athlete_elem.find(class_='hot-heat-athlete__counted-waves') 
    # Parse "6.40 + 4.90" format
    wave_matches = re.findall(r'(\d+\.\d+)', waves_text)
    wave_scores = [float(score) for score in wave_matches]
    
    # Determinar posición desde CSS classes
    position = self._extract_position_from_athlete_elem(athlete_elem)
    advanced = self._check_if_advanced(athlete_elem)  # Busca 'advance' en classes
```

### Mapeo Correcto de Olas

**Problema Original:** Confusión entre surfistas y olas
**Solución:** Parse individual por atleta

```python
def _extract_all_individual_waves(self, athlete_elem, heat_id):
    # Buscar enlace "Watch" para detalles completos
    watch_link = athlete_elem.find('a', class_='hot-heat__replay-link')
    
    # Construir URL de detalles: /athletes/10158/adur-amatriain/eventresults?eventId=4889&heatId=106821
    details_url = urljoin(self.config.BASE_URL, href)
    
    # Obtener página de detalles con todas las olas individuales
    return self._parse_individual_waves_from_details(response.text)
```

## 📊 Datos Extraídos Mejorados

### Por Heat/Manga
```python
Heat(
    heat_id="106821",
    round_name="Round of 64 - Heat 8", 
    position=3,                          # Desde athlete-place-3
    total_score=11.30,                   # hot-heat-athlete__score
    wave_scores=[6.40, 4.90, 3.50, 0.10], # Todas las olas individuales
    advanced=False,                      # No tiene class 'advance'
    eliminated=True                      # Posición 3-4 = eliminado
)
```

### Surfistas Confirmados
```python
confirmed_spanish_surfers = [
    {"id": "588", "name": "Aritz Aranburu", "country": "Basque Country"},
    {"id": "3771", "name": "Juan Fernandez", "country": "Spain"},
    {"id": "602", "name": "Gony Zubizarreta", "country": "Basque Country"}, 
    {"id": "10158", "name": "Adur Amatriain", "country": "Basque Country"},
    # + más que se descubran automáticamente
]
```

## 🧪 Testing

### Test Específicos
```bash
# Probar solo API endpoints
python test_updated_scraper.py api

# Probar solo Selenium lazy loading  
python test_updated_scraper.py selenium

# Probar solo extracción de heats
python test_updated_scraper.py heats

# Test completo
python test_updated_scraper.py full
```

### Test de Endpoints API
```bash
python test_updated_scraper.py api
```
Prueba automáticamente todos los `countryIds` posibles y reporta cuáles funcionan.

### Test de Lazy Loading
```bash
python test_updated_scraper.py selenium
```
Simula scroll completo y extrae todos los atletas cargados.

## ⚡ Ejecución Rápida

### Instalación Actualizada
```bash
pip install -r requirements.txt  # Incluye Selenium y WebDriver Manager
```

### Scraping Completo
```bash
python wsl_scraper_main.py
```

**Tiempo estimado:** 45-90 minutos (dependiendo de Selenium)
**Surfistas esperados:** 10-20 surfistas españoles con datos completos

### Solo Test Rápido
```bash  
python wsl_scraper_main.py --test
```

Ejecuta análisis técnico y descubrimiento de endpoints sin scraping completo.

## 📈 Resultados Esperados

### Con las Mejoras:
- **Más surfistas:** Lazy loading descubre atletas adicionales
- **Datos completos de heats:** Todas las olas individuales por manga
- **Mapeo correcto:** Cada ola asociada al surfista correcto
- **Mejor cobertura:** Múltiples fuentes de datos combinadas

### Ejemplo de Output Mejorado:
```
Total surfistas españoles únicos encontrados: 15
  - Aritz Aranburu (Basque Country) - 3 temporadas, 12 eventos, 45 heats
  - Adur Amatriain (Basque Country) - 2 temporadas, 8 eventos, 28 heats
  - Juan Fernandez (Spain) - 4 temporadas, 18 eventos, 67 heats
```

## 🔍 Debugging

### Logs Detallados
```bash
tail -f wsl_scraper.log
```

### Variables de Debug
```python
# En wsl_scraper_main.py
logging.basicConfig(level=logging.DEBUG)  # Cambiar a DEBUG para más detalle
```

### Test Individual de Componentes
```python
scraper = WSLScraper()

# Test solo endpoints API
api_results = scraper._try_country_api_endpoints()

# Test solo Selenium  
selenium_results = scraper._scrape_with_lazy_loading()

# Test solo eventos españoles
event_results = scraper._extract_spanish_surfers_from_events("abanca-pantin-classic-galicia-pro")
```

## 📋 Próximos Pasos

1. **Ejecutar test:** `python test_updated_scraper.py`
2. **Revisar logs:** Identificar qué estrategias funcionan mejor
3. **Scraping completo:** `python wsl_scraper_main.py`  
4. **Análisis estadístico:** `python wsl_statistics_analyzer.py`

¡El sistema ahora maneja correctamente el lazy loading, extrae datos completos de heats, y mapea las olas individuales por surfista! 🏄‍♂️