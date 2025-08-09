#!/usr/bin/env python3
"""
WSL Scraper - Enfoque por Surfista Individual
1. Obtener surfistas por nacionalidad
2. Para cada surfista, obtener todos sus campeonatos de los años configurados
3. Para cada campeonato, obtener heats detallados
"""

import argparse
import requests
import time
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from tqdm import tqdm

from config import DEFAULT_YEARS, DEFAULT_COUNTRIES, COUNTRY_CODE_MAP

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Heat:
    heat_id: str
    round_name: str
    position: int
    total_score: float
    wave_scores: List[float]
    advanced: bool
    heat_date: Optional[str] = None

@dataclass
class Event:
    event_id: str
    event_name: str
    location: str
    tour_type: str  # CT, CS, QS, Longboard, Junior, etc.
    start_date: Optional[str] = None
    final_position: Optional[int] = None
    points_earned: Optional[float] = None
    heats: List[Heat] = None

@dataclass 
class Surfer:
    surfer_id: str
    name: str
    country: str
    events: List[Event] = None

class WSLSurferFocused:
    """Scraper enfocado por surfista individual"""

    def __init__(self, years: List[int] = None, countries: List[str] = None,
                 surfer_filter: Optional[List[str]] = None, max_workers: int = 5):
        self.base_url = "https://www.worldsurfleague.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        self.years = years or DEFAULT_YEARS
        self.country_codes = countries or DEFAULT_COUNTRIES
        self.country_ids = [COUNTRY_CODE_MAP.get(c.upper()) for c in self.country_codes if c.upper() in COUNTRY_CODE_MAP]
        self.surfer_filter = surfer_filter
        self.max_workers = max_workers

        # Crear directorios
        Path("data").mkdir(exist_ok=True)
        Path("data/surfers").mkdir(exist_ok=True)
        Path("data/events").mkdir(exist_ok=True)
        Path("data/heats").mkdir(exist_ok=True)
    
    def get_surfers(self) -> List[Dict]:

        """Obtener todos los surfistas de los países configurados"""
        logger.info("Obteniendo listado de surfistas...")

        query = "&".join([f"countryIds%5B{i}%5D={cid}" for i, cid in enumerate(self.country_ids)])
        url = f"{self.base_url}/athletes?{query}&rnd={int(time.time() * 1000)}"

        try:
            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"Error obteniendo surfistas: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            athlete_names = soup.select('.athlete-name')
            athlete_countries = soup.select('.athlete-country-name')
            pagination_label = soup.select_one('.paginationLabel')
            total_surfers = 0
            if pagination_label:
                match = re.search(r'(\\d+) - (\\d+) of (\\d+) items', pagination_label.get_text(strip=True))
                if match:
                    total_surfers = int(match.group(3))
                    last_index = int(match.group(2))
                    while last_index < total_surfers:
                        new_url = f"{self.base_url}/athletes?{query}&offset={last_index}"
                        resp = self.session.get(new_url)
                        if resp.status_code != 200:
                            break
                        sub = BeautifulSoup(resp.text, 'html.parser')
                        new_names = sub.select('.athlete-name')
                        new_countries = sub.select('.athlete-country-name')
                        athlete_names.extend(new_names)
                        athlete_countries.extend(new_countries)
                        per_page = len(new_names)
                        if per_page == 0:
                            break
                        last_index += per_page

            surfers = []
            for name_elem, country_elem in zip(athlete_names, athlete_countries):
                name = name_elem.get_text(strip=True)
                country = country_elem.get_text(strip=True)
                profile_url = name_elem['href']
                match = re.search(r'/athletes/(\\d+)/', profile_url)
                surfer_id = match.group(1) if match else None
                if surfer_id and name:
                    surfers.append({'id': surfer_id, 'name': name, 'country': country, 'profile_url': profile_url})

            if self.surfer_filter:
                surfers = [s for s in surfers if s['name'] in self.surfer_filter or s['id'] in self.surfer_filter]

            logger.info(f"Encontrados {len(surfers)} surfistas")
            return surfers

        except Exception as e:
            logger.error(f"Error obteniendo surfistas: {e}")
            return []

    def get_surfer_events(self, surfer_data: dict, year: int) -> List[Event]:
        """Obtener todos los eventos del año indicado para un surfista"""
        surfer_id = surfer_data['id']
        surfer_name = surfer_data['name']
        logger.info(f"Obteniendo eventos {year} para {surfer_name} (ID: {surfer_id})")

        base_url = f"{self.base_url}/athletes/{surfer_id}/{surfer_name.lower().replace(' ', '-')}"
        year_results_url = f"{base_url}?section=yearResults"

        try:
            response = self.session.get(year_results_url)
            if response.status_code != 200:
                logger.warning(f"No se pudo acceder al perfil de {surfer_name}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar todos los tour codes del selector
            select = soup.find('select', {'name': 'yearResultsTourCode'})
            if not select:
                logger.warning(f"No se encontró el selector de tours para {surfer_name}")
                return []

            tour_options = select.find_all('option')
            tour_codes = [opt['value'] for opt in tour_options if opt.get('value') ]

            logger.info(f"Tour codes encontrados para {surfer_name}: {tour_codes}")

            all_events: List[Event] = []

            for code in tour_codes:
                url = f"{base_url}?section=yearResults&yearResultsTourCode={code}&year={year}"
                logger.debug(f"Consultando eventos en: {url}")
                res = self.session.get(url)
                if res.status_code != 200:
                    logger.warning(f"  ⚠️ No se pudo acceder a eventos para {surfer_name} en tour {code}")
                    continue

                sub_soup = BeautifulSoup(res.text, 'html.parser')
                event_links = sub_soup.find_all('a', href=re.compile(r'eventresults'))

                logger.info(f"  ➕ {len(event_links)} eventos encontrados en tour {code}")

                for link in event_links:
                    href = link.get('href')
                    event_text = link.get_text(strip=True)
                    if not href or not event_text:
                        continue

                    match_id = re.search(r'eventId=(\d+)', href)
                    event_id = match_id.group(1) if match_id else f"event_{hash(href) % 10000}"

                    event = Event(
                        event_id=event_id,
                        event_name=event_text,
                        location="Unknown",
                        tour_type=code.upper()
                    )

                    event_url = urljoin(self.base_url, href)
                    event_details = self._get_event_details(event_url, surfer_id, surfer_name)
                    if event_details:
                        event.final_position = event_details.get('position')
                        event.points_earned = event_details.get('points')
                        event.heats = event_details.get('heats', [])

                    all_events.append(event)
                    logger.info(f"    ✅ {event_text} ({code.upper()})")

            logger.info(f"🎯 Total eventos {year} para {surfer_name}: {len(all_events)}")
            return all_events

        except Exception as e:
            logger.error(f"Error obteniendo eventos para {surfer_name}: {e}")
            return []

        
    def _extract_tour_type_from_url(self, url: str) -> str:
        """Extraer tipo de tour desde URL"""
        if '/ct/' in url or '/championship-tour/' in url:
            return 'Championship Tour'
        elif '/cs/' in url or '/challenger-series/' in url:
            return 'Challenger Series'
        elif '/qs/' in url or '/qualifying-series/' in url:
            return 'Qualifying Series'
        elif '/longboard/' in url:
            return 'Longboard Tour'
        elif '/junior/' in url:
            return 'Junior Tour'
        elif '/big-wave/' in url:
            return 'Big Wave Tour'
        else:
            return 'Unknown Tour'
    
    def _extract_event_id_from_url(self, url: str) -> str:
        """Extraer ID del evento desde URL"""
        match = re.search(r'/events/\d{4}/[^/]+/[^/]+/(\d+)/', url)
        if match:
            return match.group(1)
        return f"event_{hash(url) % 10000}"
    
    def _extract_location_from_url(self, url: str) -> str:
        """Extraer ubicación desde URL o texto"""
        # Extraer de la URL si es posible
        parts = url.split('/')
        if len(parts) > 6:
            location_part = parts[-2] if parts[-1] == '' else parts[-1]
            return location_part.replace('-', ' ').title()
        return "Unknown Location"
    
    def _search_events_alternative(self, surfer_id: str, surfer_name: str, year: int) -> List[Event]:
        """Búsqueda alternativa de eventos cuando no aparecen en el perfil"""
        logger.info(f"Búsqueda alternativa de eventos para {surfer_name} en {year}...")

        search_urls = [
            f"{self.base_url}/athletes/{surfer_id}/results?year={year}",
            f"{self.base_url}/athletes/{surfer_id}/events?year={year}",
            f"{self.base_url}/events/{year}?athleteId={surfer_id}",
        ]
        
        events = []
        
        for url in search_urls:
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Buscar eventos en esta página
                    event_elements = soup.find_all(['a', 'div'], href=re.compile(rf'/events/{year}/') if hasattr(soup, 'href') else None)
                    
                    for elem in event_elements:
                        href = elem.get('href') if hasattr(elem, 'get') else None
                        if href and f'/events/{year}/' in href:
                            event_name = elem.get_text(strip=True)
                            
                            if event_name and len(event_name) > 3:  # Filtrar textos muy cortos
                                event = Event(
                                    event_id=self._extract_event_id_from_url(href),
                                    event_name=event_name,
                                    location=self._extract_location_from_url(href),
                                    tour_type=self._extract_tour_type_from_url(href)
                                )
                                events.append(event)
                                logger.info(f"  🔍 Evento alternativo: {event_name}")
                    
                    if events:  # Si encontró eventos, no necesita buscar más
                        break
                        
            except Exception as e:
                logger.debug(f"Error en búsqueda alternativa {url}: {e}")
                continue
        
        return events
    
    def _get_event_details(self, event_url: str, surfer_id: str, surfer_name: str) -> Optional[Dict]:
        """Obtener detalles específicos del evento para el surfista"""
        logger.debug(f"Obteniendo detalles de evento: {event_url}")
        
        time.sleep(1)  # Rate limiting
        
        try:
            response = self.session.get(event_url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar datos específicos del surfista en este evento
            event_details = {
                'position': None,
                'points': None,
                'heats': []
            }
            
            # Buscar heats donde participó este surfista
            heats = self._extract_surfer_heats(soup, surfer_id, surfer_name)
            event_details['heats'] = heats
            
            # Buscar posición final si está disponible
            position = self._extract_final_position(soup, surfer_name)
            if position:
                event_details['position'] = position
            
            return event_details
            
        except Exception as e:
            logger.debug(f"Error obteniendo detalles de evento: {e}")
            return None
    
    def _extract_surfer_heats(self, soup: BeautifulSoup, surfer_id: str, surfer_name: str) -> List[Heat]:
        """Extraer heats específicos donde participó el surfista"""
        heats = []
        
        # Buscar contenedores de heat reales
        heat_elements = soup.select('div.hot-heat')
        
        for heat_elem in heat_elements:
            try:
                logger.info(f"Heat found")
                # Verificar si este heat contiene al surfista
                heat_data = self._parse_heat_for_surfer(heat_elem, surfer_name)
                if heat_data:
                    heats.append(heat_data)
                        
            except Exception as e:
                logger.debug(f"Error procesando heat: {e}")
                continue
        
        return heats
    
    def _get_wave_scores_for_athlete(self, heat_elem, athlete_index: int, only_counted: bool = True) -> List[float]:
        """Extraer puntuaciones de olas por columna (índice 1-based) dentro de .hot-heat__waves-details."""
        scores: List[float] = []
        if not heat_elem or not isinstance(athlete_index, int) or athlete_index < 1:
            return scores

        waves_root = heat_elem.select_one('.hot-heat__waves-details')
        if not waves_root:
            return scores

        wave_items = waves_root.select('.wave-item')
        target_col = athlete_index - 1

        for wi in wave_items:
            waves = wi.select('.wave')
            if len(waves) <= target_col:
                continue
            wave_div = waves[target_col]
            if only_counted and 'wave--counted' not in wave_div.get('class', []):
                continue
            score_span = wave_div.select_one('.wave-score')
            if not score_span:
                continue
            try:
                score_val = float(score_span.get_text(strip=True))
                scores.append(score_val)
            except ValueError:
                continue

        return scores
    

    def _parse_heat_for_surfer(self, heat_elem, surfer_name: str) -> Optional[Heat]:
        """Parse de heat específico para el surfista (usando el HTML que proporcionaste)"""
        try:
            # Extraer nombre del heat
            heat_name_elem = heat_elem.find(class_='heat-name')
            round_name = heat_name_elem.get_text(strip=True) if heat_name_elem else "Unknown Round"
            
            # Buscar el atleta específico en este heat (solo dentro del contenedor principal de atletas)
            athletes_container = heat_elem.select_one('.hot-heat__athletes')
            if not athletes_container:
                logger.info(f"No se encontraron atletas en el heat: {round_name}")
                return None
            athletes = athletes_container.select('.hot-heat-athlete')
            
            for athlete in athletes:
                # Verificar si es nuestro surfista
                name_elem = athlete.find(class_='hot-heat-athlete__name')
                if not name_elem:
                    continue
                    
                athlete_name = name_elem.get_text(strip=True)
                
                if surfer_name.lower() in athlete_name.lower():
                    # Extraer datos del surfista
                    score_elem = athlete.find(class_='hot-heat-athlete__score')
                    total_score = float(score_elem.get_text(strip=True)) if score_elem else 0.0
                    
                    position = self._extract_position_from_athlete(athlete)
                    advanced = self._check_if_advanced(athlete)
                    wave_scores = []    

                    # Obtener notas del heat por índice de atleta
                    athlete_index = None
                    try:
                        athlete_index = int(athlete.get('data-athlete-index'))
                    except Exception:
                        athlete_index = None
                    if not athlete_index:
                        class_names = ' '.join(athlete.get('class', []))
                        m_idx = re.search(r'athlete-index-(\d+)', class_names)
                        if m_idx:
                            athlete_index = int(m_idx.group(1))

                    if athlete_index:
                        wave_scores = self._get_wave_scores_for_athlete(heat_elem, athlete_index, only_counted=False)
                   

                    # Determinar posición y si avanzó
                   
                    
                    heat_replay = heat_elem.select_one('a.hot-heat__replay-link')
                    heat_link = heat_replay['href'] if heat_replay and heat_replay.has_attr('href') else '' 

                    #Obtenemos el id del heat: href="/athletes/10158/adur-amatriain/eventresults?eventId=4889&heatId=106821"
                    heat_id = None
                    if heat_link:
                        heat_id_match = re.search(r'heatId=(\d+)', heat_link)
                        if heat_id_match:
                            heat_id = heat_id_match.group(1)
                     
                    heat = Heat(
                        heat_id=f"heat_{heat_id}" if heat_id else f"heat_{hash(round_name) % 100000}",
                        round_name=round_name,
                        position=position,
                        total_score=total_score,
                        wave_scores=wave_scores,
                        advanced=advanced
                    )

                    # wave_scores ya fueron extraídas por columna (si existían)
                    
                    return heat
            
        except Exception as e:
            logger.debug(f"Error parseando heat para {surfer_name}: {e}")
            
        return None
    
    def _extract_position_from_athlete(self, athlete_elem) -> int:
        """Extraer posición desde clases CSS"""
        class_names = athlete_elem.get('class', [])
        for class_name in class_names:
            if 'athlete-place-' in str(class_name):
                match = re.search(r'athlete-place-(\d+)', str(class_name))
                if match:
                    return int(match.group(1))
        return 1
    
    def _check_if_advanced(self, athlete_elem) -> bool:
        """Verificar si avanzó"""
        class_names = athlete_elem.get('class', [])
        return any('advance' in str(class_name) for class_name in class_names)
    
    def _extract_final_position(self, soup: BeautifulSoup, surfer_name: str) -> Optional[int]:
        """Extraer posición final del evento"""
        # Buscar en tablas de resultados
        result_tables = soup.find_all('table')
        for table in result_tables:
            rows = table.find_all('tr')
            for i, row in enumerate(rows):
                if surfer_name.lower() in row.get_text().lower():
                    # La posición podría estar en la primera celda
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        try:
                            return int(cells[0].get_text(strip=True))
                        except ValueError:
                            continue
        return None
    
    def process_all_surfers(self):
        """Procesar todos los surfistas configurados"""
        logger.info("=== PROCESANDO SURFISTAS ===")

        surfers_list = self.get_surfers()
        logger.info(f"Total surfistas a procesar: {len(surfers_list)}")

        def worker(surfer_data: Dict) -> Surfer:
            events: List[Event] = []
            for year in self.years:
                events.extend(self.get_surfer_events(surfer_data, year))
            surfer = Surfer(
                surfer_id=surfer_data['id'],
                name=surfer_data['name'],
                country=surfer_data['country'],
                events=events
            )
            self._save_surfer_data(surfer)
            return surfer

        all_surfers_data: List[Surfer] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for surfer in tqdm(executor.map(worker, surfers_list), total=len(surfers_list), desc="Surfistas"):
                all_surfers_data.append(surfer)

        self._save_final_data(all_surfers_data)
        return all_surfers_data
    
    def _save_surfer_data(self, surfer: Surfer):
        """Guardar datos individuales del surfista"""
        filename = f"data/surfers/{surfer.surfer_id}_{surfer.name.replace(' ', '_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(surfer), f, ensure_ascii=False, indent=2, default=str)
    
    def _save_final_data(self, surfers_data: List[Surfer]):
        """Guardar datos finales consolidados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON completo
        final_data = {
            'timestamp': timestamp,
            'total_surfers': len(surfers_data),
            'surfers': [asdict(surfer) for surfer in surfers_data]
        }
        
        json_file = f"data/surfers_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✅ Datos guardados en: {json_file}")
        
        # CSV de surfistas
        import csv
        
        surfers_csv = f"data/surfers_summary_{timestamp}.csv"
        with open(surfers_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Name', 'Country', 'Events', 'Total_Heats', 'Tours'])
            
            for surfer in surfers_data:
                events_count = len(surfer.events) if surfer.events else 0
                heats_count = sum(len(e.heats) for e in surfer.events if e.heats) if surfer.events else 0
                tours = set(e.tour_type for e in surfer.events) if surfer.events else set()
                
                writer.writerow([
                    surfer.surfer_id,
                    surfer.name,
                    surfer.country,
                    events_count,
                    heats_count,
                    ', '.join(tours)
                ])
        
        logger.info(f"✅ CSV resumen guardado en: {surfers_csv}")

        # === Archivos BRUTOS para análisis de datos ===
        # 1) JSON bruto: lista simple de surfistas con su estructura completa (sin envoltorio decorativo)
        raw_json = f"data/all_surfers_raw_{timestamp}.json"
        with open(raw_json, 'w', encoding='utf-8') as f:
            json.dump([asdict(s) for s in surfers_data], f, ensure_ascii=False, default=str)

        # 2) JSONL y CSV de heats: filas planas por heat para análisis
        heats_jsonl = f"data/all_heats_raw_{timestamp}.jsonl"
        heats_csv = f"data/all_heats_raw_{timestamp}.csv"

        # Construir filas planas por heat
        heat_rows: List[Dict] = []
        for surfer in surfers_data:
            surfer_id = surfer.surfer_id
            surfer_name = surfer.name
            surfer_country = surfer.country
            events = surfer.events or []
            for event in events:
                event_id = event.event_id
                event_name = event.event_name
                event_location = event.location
                tour_type = event.tour_type
                final_position = event.final_position
                points_earned = event.points_earned
                heats = event.heats or []
                for heat in heats:
                    heat_rows.append({
                        'surfer_id': surfer_id,
                        'surfer_name': surfer_name,
                        'country': surfer_country,
                        'event_id': event_id,
                        'event_name': event_name,
                        'event_location': event_location,
                        'tour_type': tour_type,
                        'event_final_position': final_position,
                        'event_points_earned': points_earned,
                        'heat_id': heat.heat_id,
                        'round_name': heat.round_name,
                        'heat_position': heat.position,
                        'heat_total_score': heat.total_score,
                        'heat_advanced': heat.advanced,
                        'heat_date': heat.heat_date,
                        'wave_scores': heat.wave_scores,
                    })

        # Guardar JSONL
        with open(heats_jsonl, 'w', encoding='utf-8') as f:
            for row in heat_rows:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')

        # Guardar CSV de heats (columna wave_scores como string separado por |)
        if heat_rows:
            fieldnames = [
                'surfer_id', 'surfer_name', 'country',
                'event_id', 'event_name', 'event_location', 'tour_type',
                'event_final_position', 'event_points_earned',
                'heat_id', 'round_name', 'heat_position', 'heat_total_score', 'heat_advanced', 'heat_date',
                'wave_scores'
            ]
            with open(heats_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in heat_rows:
                    r_out = dict(r)
                    # Serializar wave_scores a string para CSV
                    wave_scores = r_out.get('wave_scores') or []
                    r_out['wave_scores'] = '|'.join(str(x) for x in wave_scores)
                    writer.writerow(r_out)

        # Copias “estables” sin timestamp para consumo recurrente
        stable_raw_json = 'data/all_surfers_raw.json'
        stable_heats_jsonl = 'data/all_heats_raw.jsonl'
        stable_heats_csv = 'data/all_heats_raw.csv'
        try:
            # Escribir/overwite versiones estables
            with open(stable_raw_json, 'w', encoding='utf-8') as f:
                json.dump([asdict(s) for s in surfers_data], f, ensure_ascii=False, default=str)
            with open(stable_heats_jsonl, 'w', encoding='utf-8') as f:
                for row in heat_rows:
                    f.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
            if heat_rows:
                with open(stable_heats_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in heat_rows:
                        r_out = dict(r)
                        wave_scores = r_out.get('wave_scores') or []
                        r_out['wave_scores'] = '|'.join(str(x) for x in wave_scores)
                        writer.writerow(r_out)
        except Exception as e:
            logger.debug(f"No se pudieron escribir archivos estables: {e}")

        logger.info(f"📦 Archivos brutos guardados: {raw_json}, {heats_jsonl}, {heats_csv}")

def main():
    """Función principal con nuevo enfoque"""
    print("🏄‍♂️ WSL Scraper - Enfoque por Surfista")
    print("=" * 50)
    
    parser = argparse.ArgumentParser(description="WSL scraper")
    parser.add_argument('--years', nargs='+', type=int, default=DEFAULT_YEARS, help='Años a analizar')
    parser.add_argument('--countries', nargs='+', default=DEFAULT_COUNTRIES, help='Códigos de país a incluir')
    parser.add_argument('--surfers', nargs='+', help='IDs o nombres de surfistas específicos')
    parser.add_argument('--max-workers', type=int, default=5, help='Número máximo de hilos')
    args = parser.parse_args()

    scraper = WSLSurferFocused(years=args.years, countries=args.countries,
                               surfer_filter=args.surfers, max_workers=args.max_workers)

    # Procesar surfistas
    surfers_data = scraper.process_all_surfers()
    
    # Estadísticas finales
    total_surfers = len(surfers_data)
    total_events = sum(len(s.events) for s in surfers_data if s.events)
    total_heats = sum(sum(len(e.heats) for e in s.events if e.heats) for s in surfers_data if s.events)
    
    print(f"\n📊 ESTADÍSTICAS FINALES:")
    print(f"Total surfistas procesados: {total_surfers}")
    print(f"Total eventos: {total_events}")
    print(f"Total heats extraídos: {total_heats}")
    
    # Tours representados
    all_tours = set()
    for surfer in surfers_data:
        if surfer.events:
            for event in surfer.events:
                all_tours.add(event.tour_type)
    
    print(f"Tours encontrados: {', '.join(all_tours)}")
    print(f"\n✅ Datos completos guardados en directorio 'data/'")

if __name__ == "__main__":
    main()
