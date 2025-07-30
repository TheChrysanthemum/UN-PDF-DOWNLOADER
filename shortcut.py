import sys
import subprocess
import importlib
import os
from pathlib import Path

def is_running_on_android():
    """Verifica se o script está rodando em um ambiente Android."""
    if 'ANDROID_ROOT' in os.environ or os.path.exists('/storage/emulated/0'):
        return True
    return False

def get_download_path():
    """Retorna o caminho para a pasta de Downloads padrão do sistema."""
    if is_running_on_android():
        download_dir = Path('/storage/emulated/0/Download')
    else:
        download_dir = Path.home() / 'Downloads'
    
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir

def check_and_install_dependencies():
    """Verifica e instala dependências silenciosamente, a menos que haja um problema."""
    required_libs = ['requests', 'tqdm', 'pyfiglet']
    missing_libs = []

    for lib_name in required_libs:
        try:
            importlib.import_module(lib_name)
        except ImportError:
            missing_libs.append(lib_name)

    if missing_libs:
        print(f"ℹ️  Instalando dependências necessárias: {', '.join(missing_libs)}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_libs],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ Dependências instaladas.")
        except subprocess.CalledProcessError:
            print(f"\n❌ ERRO: Falha ao instalar as dependências.")
            print(f"   Por favor, tente instalar manualmente: pip install {' '.join(missing_libs)}")
            sys.exit(1)

def run_main_script(work_dir):
    """Baixa e executa o script principal."""
    main_script_url = "https://raw.githubusercontent.com/TheChrysanthemum/UN-PDF-DOWNLOADER/main/un%20pdf%20downloader.py"
    
    try:
        import requests
        response = requests.get(main_script_url)
        response.raise_for_status()
        script_code = response.text
        
        os.chdir(work_dir)
        
        print("="*40)
        exec(script_code, {'__name__': '__main__'})

    except Exception as e:
        print(f"\n❌ ERRO: Falha ao baixar ou executar o script principal.")
        print(f"   Motivo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    
    download_dir = get_download_path()
    
    print(f"ℹ️  Os arquivos serão salvos em: {download_dir}")
    print("    Se optar por usar JSONs locais, coloque-os nesta pasta.\n")
    
    check_and_install_dependencies()
    run_main_script(download_dir)
