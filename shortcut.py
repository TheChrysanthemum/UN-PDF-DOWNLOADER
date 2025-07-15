import sys
import subprocess
import importlib # Importa a biblioteca necessária para importação dinâmica

# Lista de bibliotecas necessárias
required_libs = ['requests', 'tqdm', 'pyfiglet']

# Verifica e instala as bibliotecas faltantes
missing_libs = []
for lib in required_libs:
    try:
        # CORREÇÃO: Usa importlib.import_module() para verificar se a biblioteca existe
        importlib.import_module(lib)
    except ImportError:
        missing_libs.append(lib)

if missing_libs:
    print(f"Instalando bibliotecas faltantes: {', '.join(missing_libs)}")
    # Garante que o pip seja chamado corretamente
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_libs])

# Agora continua com o código original
import requests
url = "https://raw.githubusercontent.com/TheChrysanthemum/UN-PDF-DOWNLOADER/9608bdbcbffe7ae1cfd38eb0092b54c43cc769ba/un%20pdf%20downloader.py"

try:
    # Baixa e executa o script
    print("\nBaixando e executando o script principal...")
    response = requests.get(url)
    response.raise_for_status()  # Verifica se o download foi bem-sucedido
    # Normaliza quebras de linha do Windows ('\r\n') para o padrão Unix ('\n')
    script_code = response.text.replace('\r\n', '\n')
    exec(script_code)
except Exception as e:
    print(f"Erro ao executar o script baixado: {e}\n")

