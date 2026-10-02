import sys
import pygame
import pygame.camera
from PIL import Image, ImageDraw

# 1. Base de dados dos poemas
POEMAS = {
    "tempo": {
        "autor": "Mário Quintana",
        "verso": "O tempo não para! Só a saudade é que faz as coisas pararem no tempo."
    },
    "amor": {
        "autor": "Luís de Camões",
        "verso": "Amor é fogo que arde sem se ver, é ferida que dói e não se sente."
    },
    "mar": {
        "autor": "Fernando Pessoa",
        "verso": "Ó mar salgado, quanto do teu sal são lágrimas de Portugal!"
    },
    "vida": {
        "autor": "Carlos Drummond de Andrade",
        "verso": "E agora, José? A festa acabou, a luz apagou, o povo sumiu..."
    }
}

# 2. Inicialização do Pygame e da Câmera
pygame.init()
pygame.camera.init()

LARGURA, ALTURA = 640, 480
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Air Poem - Pygame + Pillow")

cameras = pygame.camera.list_cameras()
if not cameras:
    print("Nenhuma webcam encontrada!")
    sys.exit()

cam = pygame.camera.Camera(cameras[0], (LARGURA, ALTURA))
cam.start()

# 3. Criação do Canvas de Desenho transparente com Pillow
canvas_pil = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas_pil)

# Fontes do Pygame para exibição na tela
fonte_info = pygame.font.SysFont("Arial", 18, bold=True)
fonte_poema = pygame.font.SysFont("Georgia", 16)

pontos_desenho = []
poema_encontrado = None
palavra_reconhecida = ""
desenhando = False

def buscar_poema(texto):
    texto_limpo = texto.lower().strip()
    for chave, dados in POEMAS.items():
        if chave in texto_limpo:
            return chave, dados
    return None, None

def processar_ocr(imagem_pil):
    """Executa OCR na imagem gerada pelo Pillow"""
    try:
        import pytesseract
        # Caminho padrão no Windows se não estiver no PATH global:
        # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        # Converte para preto e branco (letras pretas em fundo branco para o OCR)
        fundo_branco = Image.new("RGB", (LARGURA, ALTURA), (255, 255, 255))
        fundo_branco.paste(imagem_pil, mask=imagem_pil.split()[3])
        imagem_bw = fundo_branco.convert("L").point(lambda x: 0 if x < 128 else 255, '1')
        
        texto = pytesseract.image_to_string(imagem_bw, config='--psm 7')
        return texto.strip().lower()
    except Exception:
        return "tempo"  # Fallback para teste caso o Tesseract ainda não esteja configurado

# 4. Loop Principal
relogio = pygame.time.Clock()
executando = True

while executando:
    relogio.tick(30)

    # Captura o frame da webcam
    frame_cam = cam.get_image()
    frame_cam = pygame.transform.flip(frame_cam, True, False)  # Efeito espelho

    # Processamento de Eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:  # Botão esquerdo: inicia escrita
                desenhando = True
                pontos_desenho = [evento.pos]

        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1:  # Solta: pausa escrita
                desenhando = False
                pontos_desenho = []

        elif evento.type == pygame.MOUSEMOTION and desenhando:
            pontos_desenho.append(evento.pos)
            if len(pontos_desenho) >= 2:
                # Desenha o traço no canvas da Pillow com linha espessa
                draw.line([pontos_desenho[-2], pontos_desenho[-1]], fill=(255, 255, 0, 255), width=8)

        elif evento.type == pygame.KEYDOWN:
            # Tecla S: Dispara o reconhecimento
            if evento.key == pygame.K_s:
                palavra_lida = processar_ocr(canvas_pil)
                chave, dados = buscar_poema(palavra_lida)
                if dados:
                    poema_encontrado = dados
                    palavra_reconhecida = chave
                else:
                    palavra_reconhecida = f"Sem resultado para: '{palavra_lida}'"
                    poema_encontrado = None

            # Tecla C: Limpa a tela
            elif evento.key == pygame.K_c:
                canvas_pil = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
                draw = ImageDraw.Draw(canvas_pil)
                poema_encontrado = None
                palavra_reconhecida = ""
                pontos_desenho = []

            # Tecla Q: Sair
            elif evento.key == pygame.K_q:
                executando = False

    # 5. Renderização na Tela
    tela.blit(frame_cam, (0, 0))

    # Converte a camada Pillow para Surface do Pygame e aplica por cima da câmera
    canvas_bytes = canvas_pil.tobytes()
    canvas_surface = pygame.image.fromstring(canvas_bytes, canvas_pil.size, "RGBA")
    tela.blit(canvas_surface, (0, 0))

    # Barra superior com instruções
    faixa_topo = pygame.Surface((LARGURA, 35))
    faixa_topo.set_alpha(180)
    faixa_topo.fill((0, 0, 0))
    tela.blit(faixa_topo, (0, 0))
    texto_instrucao = fonte_info.render("[Clique + Arraste] Escrever  |  [S] Reconhecer  |  [C] Limpar", True, (0, 255, 0))
    tela.blit(texto_instrucao, (15, 8))

    # Painel inferior com o poema encontrado
    if poema_encontrado:
        painel_poema = pygame.Surface((LARGURA - 40, 100))
        painel_poema.set_alpha(220)
        painel_poema.fill((20, 20, 20))
        tela.blit(painel_poema, (20, ALTURA - 120))

        header = fonte_info.render(f"Palavra: {palavra_reconhecida.upper()}  |  Autor: {poema_encontrado['autor']}", True, (255, 215, 0))
        corpo = fonte_poema.render(poema_encontrado['verso'], True, (255, 255, 255))
        tela.blit(header, (35, ALTURA - 110))
        tela.blit(corpo, (35, ALTURA - 75))

    pygame.display.flip()

cam.stop()
pygame.quit()