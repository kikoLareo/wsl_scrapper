#!/usr/bin/env python3
import threading
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from flask import Flask, render_template, request, redirect, url_for, send_file
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import DEFAULT_YEARS, DEFAULT_COUNTRIES
from wsl_surfer_focused import WSLSurferFocused, Surfer


app = Flask(__name__)

DATA_DIR = Path('data')
CHECKPOINTS = DATA_DIR / 'checkpoints'
JOBS_DIR = CHECKPOINTS / 'jobs'

jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()


def _ensure_dirs():
    CHECKPOINTS.mkdir(exist_ok=True, parents=True)
    JOBS_DIR.mkdir(exist_ok=True, parents=True)


def save_jobs_state():
    try:
        _ensure_dirs()
        latest_file = CHECKPOINTS / 'jobs_latest.json'
        with jobs_lock:
            with latest_file.open('w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            # Guardar también por job individual
            for jid, payload in jobs.items():
                with (JOBS_DIR / f'{jid}.json').open('w', encoding='utf-8') as jf:
                    json.dump(payload, jf, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_jobs_state():
    try:
        latest_file = CHECKPOINTS / 'jobs_latest.json'
        if not latest_file.exists():
            return
        data = json.loads(latest_file.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            with jobs_lock:
                jobs.clear()
                for jid, payload in data.items():
                    # Si quedó 'running' de una sesión anterior, marcar como 'interrupted'
                    if isinstance(payload, dict) and payload.get('status') == 'running':
                        payload['status'] = 'interrupted'
                        payload.setdefault('logs', []).append('Proceso anterior interrumpido por reinicio del servidor')
                    jobs[jid] = payload
    except Exception:
        pass


def load_options() -> Dict[str, Any]:
    options = {
        'years': DEFAULT_YEARS,
        'countries': DEFAULT_COUNTRIES,
        'tours': ['CT', 'CS', 'QS', 'LONGBOARD', 'JUNIOR', 'BIG-WAVE'],
        'surfers': [],  # [{'id': '10158', 'name': 'Adur Amatriain', 'country': 'Spain'}]
        'locations': [],
    }
    latest = CHECKPOINTS / 'options_latest.json'
    if latest.exists():
        try:
            data = json.loads(latest.read_text(encoding='utf-8'))
            if isinstance(data.get('years'), list) and data['years']:
                options['years'] = sorted({int(y) for y in data['years']})
            if isinstance(data.get('tours'), list) and data['tours']:
                options['tours'] = sorted({str(t).upper() for t in data['tours']})
            if isinstance(data.get('surfers'), list):
                options['surfers'] = data['surfers']
            if isinstance(data.get('locations'), list):
                options['locations'] = sorted({str(l) for l in data['locations']})
        except Exception:
            pass
    return options


def run_scrape_job(job_id: str, years: List[int], countries: List[str], tours: List[str], surfers: List[str], max_workers: int, request_delay: float, locations: List[str]):
    job = jobs[job_id]
    job['status'] = 'running'
    job['logs'].append('Iniciando scraping...')
    save_jobs_state()
    try:
        scraper = WSLSurferFocused(
            years=years or DEFAULT_YEARS,
            countries=countries or DEFAULT_COUNTRIES,
            surfer_filter=surfers or None,
            max_workers=max_workers,
            tours=tours or None,
            request_delay=request_delay,
            locations=locations or None,
        )
        job['logs'].append(f"Parámetros: years={years}, countries={countries}, tours={tours}, surfers={surfers}, locations={locations}, max_workers={max_workers}, delay={request_delay}")
        start = time.time()

        # Obtener listado de surfistas primero para conocer el total
        surfers_list = scraper.get_surfers()
        total = len(surfers_list)
        job['progress'] = {'total': total, 'done': 0, 'eta_s': None}
        job['logs'].append(f"Total de surfistas a procesar: {total}")
        save_jobs_state()

        if total == 0:
            job['status'] = 'finished'
            job['summary'] = {'total_surfers': 0, 'total_events': 0, 'total_heats': 0, 'elapsed_s': 0}
            return

        def worker(surfer_data: dict) -> Surfer:
            events = []
            for y in years or DEFAULT_YEARS:
                events.extend(scraper.get_surfer_events(surfer_data, y))
            surfer_obj = Surfer(
                surfer_id=surfer_data['id'],
                name=surfer_data['name'],
                country=surfer_data['country'],
                events=events,
            )
            scraper._save_surfer_data(surfer_obj)
            return surfer_obj

        all_surfers_data: List[Surfer] = []
        done = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, sd) for sd in surfers_list]
            for fut in as_completed(futures):
                try:
                    s = fut.result()
                    all_surfers_data.append(s)
                except Exception as e:
                    job['logs'].append(f"Error procesando surfista: {e}")
                finally:
                    done += 1
                    job['progress']['done'] = done
                    elapsed = max(0.001, time.time() - start)
                    rate = done / elapsed
                    rem = max(0, total - done)
                    eta = rem / rate if rate > 0 else None
                    job['progress']['eta_s'] = round(eta, 1) if eta is not None else None
                    if done % 5 == 0 or done == total:
                        job['logs'].append(f"Avance: {done}/{total} ({round(100*done/total,1)}%)")
                        save_jobs_state()

        # Guardado final y resumen
        scraper._save_final_data(all_surfers_data)
        elapsed = time.time() - start
        total_surfers = len(all_surfers_data)
        total_events = sum(len(s.events) for s in all_surfers_data if s.events)
        total_heats = sum(sum(len(e.heats) for e in s.events if e.heats) for s in all_surfers_data if s.events)
        job['summary'] = {
            'total_surfers': total_surfers,
            'total_events': int(total_events),
            'total_heats': int(total_heats),
            'elapsed_s': round(elapsed, 1),
        }
        job['logs'].append(f"Finalizado: surfers={total_surfers}, events={total_events}, heats={total_heats}, tiempo={elapsed:.1f}s")
        job['status'] = 'finished'
        save_jobs_state()
    except Exception as e:
        job['status'] = 'error'
        job['logs'].append(f"Error: {e}")
        save_jobs_state()


@app.get('/')
def index():
    options = load_options()
    return render_template('index.html', options=options)


@app.post('/run')
def run_job():
    form = request.form
    years = [int(y) for y in form.getlist('years')]
    countries = form.getlist('countries') or DEFAULT_COUNTRIES
    tours = [t.upper() for t in form.getlist('tours')]
    surfers_raw = form.get('surfers', '').strip()
    locations = [l for l in form.getlist('locations') if l]
    surfers = []
    if surfers_raw:
        for token in re_split_tokens(surfers_raw):
            if token:
                surfers.append(token)
    max_workers = int(form.get('max_workers', 5))
    request_delay = float(form.get('request_delay', 0.5))

    job_id = str(int(time.time()))
    jobs[job_id] = {
        'id': job_id,
        'status': 'queued',
        'logs': [],
        'summary': None,
        'params': {
            'years': years,
            'countries': countries,
            'tours': tours,
            'surfers': surfers,
            'max_workers': max_workers,
            'request_delay': request_delay,
            'locations': locations,
        }
    }
    save_jobs_state()

    t = threading.Thread(target=run_scrape_job, args=(job_id, years, countries, tours, surfers, max_workers, request_delay, locations), daemon=True)
    t.start()

    return redirect(url_for('status', job_id=job_id))


def re_split_tokens(text: str) -> List[str]:
    """Divide exclusivamente por comas, conservando espacios internos del nombre.
    Ej.: "10158, Adur Amatriain, Leticia Canales Bilbao" ->
    ["10158", "Adur Amatriain", "Leticia Canales Bilbao"]
    """
    return [t.strip() for t in text.split(',') if t.strip()]


@app.get('/status/<job_id>')
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return f"Job {job_id} no encontrado", 404
    return render_template('status.html', job=job)


@app.get('/jobs')
def jobs_list():
    with jobs_lock:
        ordered = sorted(jobs.values(), key=lambda j: j.get('id', ''), reverse=True)
    return render_template('jobs.html', jobs=ordered)


def find_latest_files() -> dict:
    # Busca primero data/checkpoints/run_latest.json y valida rutas
    try:
        meta = Path('data/checkpoints/run_latest.json')
        if meta.exists():
            info = json.loads(meta.read_text(encoding='utf-8'))
            r = Path(info.get('run_dir', ''))
            if r.exists():
                files = {
                    'surfers_raw': r / 'surfers_raw.json',
                    'heats_raw_jsonl': r / 'heats_raw.jsonl',
                    'heats_raw_csv': r / 'heats_raw.csv',
                    'surfers_summary_csv': r / 'surfers_summary.csv',
                    'surfers_full': r / 'surfers_full.json',
                    'surfers_2025': r / 'surfers_2025.json',
                }
                files['run_dir'] = str(r)
                return files
    except Exception:
        pass
    # Fallback: escanear data/runs
    base = Path('data/runs')
    if not base.exists():
        return {}
    runs = sorted([p for p in base.iterdir() if p.is_dir()], reverse=True)
    for r in runs:
        files = {
            'surfers_raw': r / 'surfers_raw.json',
            'heats_raw_jsonl': r / 'heats_raw.jsonl',
            'heats_raw_csv': r / 'heats_raw.csv',
            'surfers_summary_csv': r / 'surfers_summary.csv',
            'surfers_full': r / 'surfers_full.json',
            'surfers_2025': r / 'surfers_2025.json',
        }
        any_exists = any(p.exists() for p in files.values())
        if any_exists:
            files['run_dir'] = str(r)
            return files
    return {}


@app.get('/download/<kind>')
def download(kind: str):
    files = find_latest_files()
    mapping = {
        'surfers_raw': files.get('surfers_raw'),
        'heats_raw_jsonl': files.get('heats_raw_jsonl'),
        'heats_raw_csv': files.get('heats_raw_csv'),
        'surfers_summary_csv': files.get('surfers_summary_csv'),
        'surfers_full': files.get('surfers_full'),
        'surfers_2025': files.get('surfers_2025'),
    }
    path = mapping.get(kind)
    if not path or not path.exists():
        return f"Archivo {kind} no encontrado", 404
    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    load_jobs_state()
    # Evitar reinicios que borran memoria: no usar reloader y debug off por defecto
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


