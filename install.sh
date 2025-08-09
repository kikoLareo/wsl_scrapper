#!/bin/bash

# WSL Spanish Surfers Scraper - Instalación
echo "🏄‍♂️ WSL Spanish Surfers Data Scraper - Instalación"
echo "=================================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 no está disponible"
    echo "Por favor instala pip3"
    exit 1
fi

echo "✅ pip3 encontrado"

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas correctamente"
else
    echo "❌ Error instalando dependencias"
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data
mkdir -p data/checkpoints  
mkdir -p data/exports
mkdir -p .claude/agents

echo "✅ Directorios creados"

# Verificar agentes Claude Code
if [ -f ".claude/agents/wsl-scraper-orchestrator.md" ]; then
    echo "✅ Subagentes Claude Code configurados"
else
    echo "⚠️  Los subagentes Claude Code necesitan ser configurados manualmente"
    echo "   Ejecuta: /agents en Claude Code para ver los agentes disponibles"
fi

# Hacer scripts ejecutables
chmod +x wsl_scraper_main.py
chmod +x wsl_statistics_analyzer.py

echo ""
echo "🎉 Instalación completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Modo test: python3 wsl_scraper_main.py --test"
echo "2. Scraping completo: python3 wsl_scraper_main.py"
echo "3. Ver README.md para instrucciones detalladas"
echo ""
echo "⚠️  Recuerda: Ejecutar manualmente de forma periódica"
echo "   Los datos de WSL se actualizan cada pocos meses"