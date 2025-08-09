#!/usr/bin/env python3
"""
Debug script para analizar la respuesta del API endpoint
"""

import requests
import time
from bs4 import BeautifulSoup

def debug_api_response():
    """Analizar qué contiene exactamente la respuesta del API"""
    
    base_url = "https://www.worldsurfleague.com"
    test_url = f"{base_url}/athletes?countryIds%5B%5D=208&rnd={int(time.time() * 1000)}"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    print(f"🔍 Analizando URL: {test_url}")
    print("=" * 80)
    
    try:
        response = session.get(test_url)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
        
        # Guardar respuesta completa para análisis
        with open('api_response_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("✅ Respuesta guardada en: api_response_debug.html")
        
        # Analizar estructura
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar cualquier elemento que contenga "spain", "basque", "canary"
        all_text = response.text.lower()
        
        spanish_indicators = ['spain', 'basque', 'canary', 'españa', 'vasco', 'canarias']
        
        print("\n🔍 Buscando indicadores españoles en el texto...")
        for indicator in spanish_indicators:
            count = all_text.count(indicator)
            if count > 0:
                print(f"  ✅ '{indicator}': {count} ocurrencias")
            else:
                print(f"  ❌ '{indicator}': 0 ocurrencias")
        
        # Buscar elementos comunes de atletas
        print("\n🔍 Buscando elementos de atletas...")
        
        selectors = [
            "[class*='athlete']",
            ".athlete-name",
            ".athlete-country-name", 
            "a[href*='/athletes/']",
            "tr",
            ".name"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            print(f"  Selector '{selector}': {len(elements)} elementos")
            
            # Mostrar primeros 3 como ejemplo
            for i, elem in enumerate(elements[:3]):
                text = elem.get_text(strip=True)[:100]
                print(f"    {i+1}. {text}...")
        
        # Buscar patrones de país en general
        print("\n🔍 Buscando países en general...")
        countries = ['australia', 'brazil', 'south africa', 'usa', 'france', 'portugal', 'hawaii']
        
        for country in countries:
            count = all_text.count(country)
            print(f"  '{country}': {count} ocurrencias")
        
        # Ver si la página contiene JavaScript que carga datos dinámicamente
        scripts = soup.find_all('script')
        print(f"\n📜 Scripts encontrados: {len(scripts)}")
        
        for i, script in enumerate(scripts[:5]):  # Primeros 5 scripts
            if script.string:
                script_text = script.string[:200].strip()
                if script_text:
                    print(f"  Script {i+1}: {script_text}...")
        
        print("\n💡 ANÁLISIS COMPLETADO")
        print("Revisa el archivo 'api_response_debug.html' para ver el contenido completo")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_api_response()
