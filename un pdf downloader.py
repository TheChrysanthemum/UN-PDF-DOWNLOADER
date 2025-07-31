import os
import json
import requests
import pyfiglet
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

CURSOS_CONFIG = {
    "LF": {"nome": "Física", "base_dir": "Lições de Física", "json_local": "LF.json"},
    "LM": {"nome": "Matemática", "base_dir": "Lições de Matemática", "json_local": "LM.json"},
    "DMAT": {"nome": "Desvendando a Matemática", "base_dir": "Desvendando a Matemática", "json_local": "DMAT.json"}
}

JSON_URLS = {
    "LF": "https://raw.githubusercontent.com/TheChrysanthemum/UN-PDF-DOWNLOADER/main/LF.json",
    "LM": "https://raw.githubusercontent.com/TheChrysanthemum/UN-PDF-DOWNLOADER/main/LM.json",
    "DMAT": "https://raw.githubusercontent.com/TheChrysanthemum/UN-PDF-DOWNLOADER/main/DMAT.json"
}

MAX_WORKERS = 5 # Quantidade de threads

# --- Funções ---

def exibir_banner():
    banner = pyfiglet.figlet_format("PDFs UN", font="slant")
    print(banner)
    print("by: The C.")

def limpar_nome_arquivo(nome):
    return re.sub(r'[\\/*?:"<>|]', "", nome)

def baixar_json_online(alias_curso):
    """Baixa um único arquivo JSON da internet."""
    url = JSON_URLS.get(alias_curso)
    nome_arquivo_local = CURSOS_CONFIG[alias_curso]["json_local"]
    
    print(f"Baixando {nome_arquivo_local}...")
    try:
        resposta = requests.get(url, timeout=20)
        resposta.raise_for_status()
        with open(nome_arquivo_local, 'wb') as f:
            f.write(resposta.content)
        print(f"✅ '{nome_arquivo_local}' baixado com sucesso.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO: Falha ao baixar '{nome_arquivo_local}'. Motivo: {e}")
        return False

def obter_jsons_online():
    """Gerencia o menu de seleção e o download dos arquivos JSON."""
    print("\nSelecione os cursos para baixar os arquivos de materiais:")
    print("[1] Lições de Física")
    print("[2] Lições de Matemática")
    print("[3] Desvendando a Matemática")
    print("[4] Todos os cursos")
    
    escolha = input("Digite os números separados por vírgula (ex: 1,3) ou 4 para todos: ").strip()
    
    cursos_selecionados = []
    if '4' in escolha:
        cursos_selecionados = ["LF", "LM", "DMAT"]
    else:
        if '1' in escolha: cursos_selecionados.append("LF")
        if '2' in escolha: cursos_selecionados.append("LM")
        if '3' in escolha: cursos_selecionados.append("DMAT")

    if not cursos_selecionados:
        print("Nenhuma seleção válida. Encerrando.")
        return []

    arquivos_json_baixados = []
    for alias in cursos_selecionados:
        if baixar_json_online(alias):
            arquivos_json_baixados.append(CURSOS_CONFIG[alias]["json_local"])
            
    return arquivos_json_baixados

def processar_json(arquivo_json):
    lista_arquivos = []
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"AVISO: Arquivo '{arquivo_json}' não encontrado. Pulando...")
        return []
    except json.JSONDecodeError:
        print(f"ERRO: Arquivo '{arquivo_json}' não é um JSON válido. Pulando...")
        return []

    alias_curso = dados.get("alias")
    if alias_curso not in CURSOS_CONFIG:
        print(f"AVISO: Alias '{alias_curso}' do arquivo '{arquivo_json}' não configurado. Pulando...")
        return []

    config_curso = CURSOS_CONFIG[alias_curso]
    curso_base_dir = config_curso["base_dir"]

    for grande_area, modulos_container in dados.get("materials", {}).items():
        if grande_area in modulos_container:
            modulos = modulos_container[grande_area]
        else:
            modulos = modulos_container

        for cod_modulo, conteudos in modulos.items():
            if not conteudos:
                continue
            
            nome_modulo = conteudos[0].get("moduleName", f"Módulo {cod_modulo}")
            grande_area_limpa = limpar_nome_arquivo(grande_area)
            nome_modulo_limpo = limpar_nome_arquivo(nome_modulo)
            
            if alias_curso == "DMAT":
                pasta_modulo = os.path.join(curso_base_dir, f"{nome_modulo_limpo} [{cod_modulo}]")
            else:
                pasta_modulo = os.path.join(curso_base_dir, grande_area_limpa, f"{nome_modulo_limpo} [{cod_modulo}]")

            for item in conteudos:
                link = item.get("link")
                flag = item.get("flag")

                if not link or (flag and "NÃO POSSUI" in flag):
                    continue

                url_corrigida = link.replace('\\/', '/')
                tipo_conteudo = item.get("type")
                
                if tipo_conteudo == "material":
                    nome_arquivo_final = f"{nome_modulo_limpo}.pdf"
                else:
                    nome_conteudo_limpo = limpar_nome_arquivo(item.get("contentName", "arquivo"))
                    nome_arquivo_final = f"{nome_conteudo_limpo}.pdf"
                
                caminho_completo = os.path.join(pasta_modulo, nome_arquivo_final)

                lista_arquivos.append({
                    "url": url_corrigida,
                    "caminho_destino": caminho_completo
                })
                
    return lista_arquivos

def baixar_arquivo(url, caminho_destino):
    try:
        os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
        resposta = requests.get(url, stream=True, timeout=30)
        resposta.raise_for_status()
        tamanho_total = int(resposta.headers.get('content-length', 0))
        nome_desc = os.path.basename(caminho_destino)

        with open(caminho_destino, 'wb') as f, tqdm(
            desc=nome_desc,
            total=tamanho_total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
            leave=False
        ) as pbar:
            for chunk in resposta.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
        
        return True, caminho_destino
    except requests.exceptions.RequestException as e:
        return False, f"Erro ao baixar {url}: {e}"
    except Exception as e:
        return False, f"Erro inesperado ao processar {url}: {e}"

def verificar_arquivos(lista_planejada):
    print("\n--- Verificação Final ---")
    print("Verificando se todos os arquivos foram baixados e organizados corretamente...")
    
    arquivos_faltantes = []
    for arquivo in lista_planejada:
        if not os.path.exists(arquivo["caminho_destino"]):
            arquivos_faltantes.append(arquivo["caminho_destino"])
            
    total_planejado = len(lista_planejada)
    total_faltante = len(arquivos_faltantes)
    total_encontrado = total_planejado - total_faltante
    
    print(f"Arquivos planejados: {total_planejado}")
    print(f"Arquivos encontrados: {total_encontrado}")
    print(f"Arquivos faltantes: {total_faltante}")
    
    if total_faltante > 0:
        print("\nOs seguintes arquivos não foram encontrados:")
        for caminho in arquivos_faltantes:
            print(f"  - {caminho}")
    else:
        print("\n✅ Sucesso! Todos os arquivos foram baixados e organizados corretamente.")

def main():
    """Função principal que orquestra o processo."""
    exibir_banner()
    
    print("Como você deseja obter os arquivos de materiais (JSON)?")
    print("[1] Usar arquivos locais (LM.json, LF.json, DMAT.json na mesma pasta)")
    print("[2] Baixar online (Se você não tem arquivos locais)")
    
    fonte_escolha = input("Digite sua escolha (1 ou 2): ").strip()
    
    arquivos_json_a_processar = []
    
    if fonte_escolha == '1':
        arquivos_json_a_processar = [config["json_local"] for config in CURSOS_CONFIG.values()]
    elif fonte_escolha == '2':
        arquivos_json_a_processar = obter_jsons_online()
    else:
        print("Escolha inválida. Encerrando.")
        return

    if not arquivos_json_a_processar:
        print("\nNenhum arquivo JSON para processar. Encerrando.")
        return

    print("\nProcessando arquivos JSON selecionados...")
    todos_os_arquivos = []
    for nome_json in arquivos_json_a_processar:
        arquivos_do_curso = processar_json(nome_json)
        if arquivos_do_curso:
            print(f"  - Encontrados {len(arquivos_do_curso)} arquivos em '{nome_json}'.")
            todos_os_arquivos.extend(arquivos_do_curso)
    
    if not todos_os_arquivos:
        print("\nNenhum arquivo para baixar foi encontrado nos JSONs. Encerrando.")
        return

    print(f"\nTotal de arquivos a serem baixados: {len(todos_os_arquivos)}")
    
    confirmacao = input("Deseja iniciar o download? (s/n): ").strip().lower()
    if confirmacao != 's':
        print("Download cancelado pelo usuário.")
        return

    print("\nIniciando downloads...")
    sucessos = 0
    falhas = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {executor.submit(baixar_arquivo, f["url"], f["caminho_destino"]): f for f in todos_os_arquivos}

        for futuro in as_completed(futuros):
            sucesso, mensagem = futuro.result()
            if sucesso:
                sucessos += 1
            else:
                falhas += 1
                print(f"\n[FALHA] {mensagem}")

    print("\n--- Processo de Download Concluído ---")
    print(f"Downloads bem-sucedidos: {sucessos}")
    print(f"Downloads com falha: {falhas}")
    
    verificar_arquivos(todos_os_arquivos)
    
    print("\nOrganização finalizada!")

if __name__ == "__main__":
    main()
