#LE AQUI OREIA SECA
#PRA USAR O CODIGO VOCE DEVE EXTRAIR OS LINKS DOS ARQUIVOS DA REQUEST DO UN, EVIDENTEMENTE COM A FORMATAÇÃO CORRIGIDA, DEPOIS SO COLAR A LISTA DE LINKS NO CONSOLE. DEPENDENDO DE ONDE VC TA RODANDO SEU CONSOLE VAI TER LIMITE DE LINHAS E VC NAO VAI CONSEGUI BOTAR TUDO DE UMA VEZ (la ele). SE QUISER ACELERAR O CODIGO, NA LINHA 108 É DEFINIDO A QUANTIDADE DE THREADS A SER USADA, SE VC NAO SABE USAR NEM MEXE, SE SOUBER PODE AUMENTAR.
import os
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pyfiglet
import webbrowser

def mostrar_banner():
    """Exibe o banner do UN PDF DOWNLOADER."""
    banner = pyfiglet.figlet_format("UN PDF DOWNLOADER", font="slant")
    print(banner)
    print("by: The C.\n")

def verificar_url(url):
    """Verifica se o URL está acessível e retorna o tamanho do arquivo."""
    try:
        resposta = requests.head(url, allow_redirects=True)
        resposta.raise_for_status()
        tamanho = int(resposta.headers.get('content-length', 0))
        return url, tamanho, None
    except requests.exceptions.RequestException as e:
        return url, 0, str(e)

def baixar_arquivo(url, pasta_destino='downloads'):
    """Baixa um arquivo e exibe uma barra de progresso."""
    url = url.strip()
    nome_arquivo = os.path.join(pasta_destino, url.split('/')[-1])

    try:
        resposta = requests.get(url, stream=True)
        resposta.raise_for_status()

        tamanho_total = int(resposta.headers.get('content-length', 0))
        with open(nome_arquivo, 'wb') as arquivo, tqdm(
            desc=nome_arquivo,
            total=tamanho_total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as barra_progresso:
            for chunk in resposta.iter_content(chunk_size=8192):
                arquivo.write(chunk)
                barra_progresso.update(len(chunk))

        return nome_arquivo

    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo {url}: {e}")
        return None

def main():
    # Mostra o banner
    mostrar_banner()

    # Solicita ao usuário a lista de URLs
    print("Cole a lista de URLs (uma por linha) e pressione Enter duas vezes para finalizar:")
    urls = []
    while True:
        linha = input()
        if linha:
            urls.append(linha.strip())
        else:
            break

    if not urls:
        print("Nenhum URL fornecido. Encerrando o script.")
        return

    pasta_destino = 'downloads'
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    print("\nVerificando URLs...")
    urls_validos = []
    urls_invalidos = []
    tamanhos = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(verificar_url, url): url for url in urls}
        for futuro in as_completed(futuros):
            url, tamanho, erro = futuro.result()
            if erro:
                urls_invalidos.append(url)
            else:
                urls_validos.append(url)
                tamanhos.append(tamanho)

    print(f"\nTotal de URLs inválidos ou inacessíveis: {len(urls_invalidos)}")
    if urls_invalidos:
        print("Links inválidos ou inacessíveis:")
        for url in urls_invalidos:
            print(f"- {url}")

    tamanho_total = sum(tamanhos)
    print(f"\nTamanho total da lista de arquivos válidos: {tamanho_total} bytes ({tamanho_total / 1024 / 1024:.2f} MB)")

    if not urls_validos:
        print("Nenhum URL válido para baixar. Encerrando o script.")
        return

    confirmacao = input("\nDeseja baixar os arquivos válidos? (s/n): ").strip().lower()
    if confirmacao != 's':
        print("Download cancelado pelo usuário.")
        return

    print("\nIniciando downloads...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(baixar_arquivo, url, pasta_destino): url for url in urls_validos}
        for futuro in as_completed(futuros):
            url = futuros[futuro]
            try:
                resultado = futuro.result()
                if resultado:
                    print(f"Download concluído: {resultado}")
                else:
                    print(f"Falha no download: {url}")
            except Exception as e:
                print(f"Erro ao processar o URL {url}: {e}")

    print("\nTodos os downloads foram processados.")
    url_imagem = "https://i.postimg.cc/dV72X2bh/IMG-20250329-133535-727.jpg"
    webbrowser.open(url_imagem)

if __name__ == "__main__":
    main()