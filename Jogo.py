import cv2 as cv
import mediapipe as mp
import math 
import pygame as pg
from pygame import sprite 
from pygame.locals import * 
from sys import exit 
import os 
from random import randrange, choice

map_face_mesh = mp.solutions.face_mesh 


# Indices do olho esquerdo 
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

# Indices do olho direito
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]  


video = cv.VideoCapture(0) 

# Detectando marcações faciais
def achandoMarcacoes(video, results, desenhar=False):
    video_altura, video_largura = video.shape[:2] 
    mesh_coord = [(int(ponto.x * video_largura), int(ponto.y * video_altura)) for ponto in results.multi_face_landmarks[0].landmark] 
    if desenhar:
        [cv.circle(video, p, 2, (0, 255, 0), -1) for p in mesh_coord] 

    return mesh_coord 

# Distância euclidiana
def distanciaEuclidiana(ponto, ponto1):
    x, y = ponto 
    x1, y1 = ponto1 
    distancia = math.sqrt((x1 - x)**2 + (y1 - y)**2)  

    return distancia 

# Piscada direita
def piscada(img, marcacoes, indice_Direito, indice_Esquerdo):

    # Olho direito
    # linha horizontal
    olho_direitoD = marcacoes[indice_Direito[0]] 
    olho_esquerdoD = marcacoes[indice_Direito[8]] 

    # linha vertical
    olho_cimaD = marcacoes[indice_Direito[12]] 
    olho_baixoD = marcacoes[indice_Direito[4]] 

    cv.line(img, olho_direitoD, olho_esquerdoD, (255, 0, 0), 2)
    cv.line(img, olho_cimaD, olho_baixoD, (255, 0, 0), 2) 

    # Olho esquerdo
    # linha horizontal
    olho_direitoE = marcacoes[indice_Esquerdo[0]] 
    olho_esquerdoE = marcacoes[indice_Esquerdo[8]] 
    
    # linha vertical
    olho_cimaE = marcacoes[indice_Esquerdo[12]] 
    olho_baixoE = marcacoes[indice_Esquerdo[4]] 

    cv.line(img, olho_direitoE, olho_esquerdoE, (255, 0, 0), 2) 
    cv.line(img, olho_cimaE, olho_baixoE, (255, 0, 0), 2) 

    distanciaDir_D = distanciaEuclidiana(olho_direitoD, olho_esquerdoD) 
    distanciaEsq_D = distanciaEuclidiana(olho_cimaD, olho_baixoD) 

    distanciaDir_E = distanciaEuclidiana(olho_cimaE, olho_baixoE) 
    distanciaEsq_E = distanciaEuclidiana(olho_direitoE, olho_esquerdoE) 
    
    relacaoDir = distanciaDir_D / distanciaEsq_D 
    relacaoEsq = distanciaEsq_E / distanciaDir_E 

    relacao = (relacaoDir + relacaoEsq) / 2 
    return relacao 

pg.init() 
pg.mixer.init() 

diretorio_principal = os.path.dirname(__file__) 
diretorio_imagens = os.path.join(diretorio_principal, 'imagens') 
diretorio_elementos = os.path.join(diretorio_imagens, 'PNG', 'Default')
diretorio_obstaculos = os.path.join(diretorio_imagens, 'kenney_generic-items', 'PNG', 'Colored')
diretorio_sons = os.path.join(diretorio_principal, 'sons') 

largura = 640 
altura = 480 

COR_FUNDO = (14, 123, 205)  # Fundo oceano
BRANCO = COR_FUNDO 

tela = pg.display.set_mode((largura, altura)) 
pg.display.set_caption("Jogo do Peixe") 

som_colisao = pg.mixer.Sound(os.path.join(diretorio_sons, "death_sound.wav")) 
som_colisao.set_volume(1) 
colidiu = False 
pontos = 0 
velocidade_padrao = 10
velocidade_jogo = velocidade_padrao 

def exibe_mensagem(msg, tamanho, cor):
    fonte = pg.font.SysFont('comicsansms', tamanho, True, False) 
    mensagem = f'{msg}' 
    texto_formatado = fonte.render(mensagem, True, cor)
    return texto_formatado 

class Peixe(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self) 
        self.som_pulo = pg.mixer.Sound(os.path.join(diretorio_sons, "jump_sound.wav")) 
        self.som_pulo.set_volume(1) 

        img_base = pg.image.load(os.path.join(diretorio_elementos, "fish_green.png")).convert_alpha() 
        img_base = pg.transform.scale(img_base, (72, 72)) 

        # Animação simulando o nado com leve oscilação
        self.imagens_peixe = [
            pg.transform.rotate(img_base, 0),
            pg.transform.rotate(img_base, 4),
            pg.transform.rotate(img_base, 0),
            pg.transform.rotate(img_base, -4),
        ]
        # Esqueleto do peixe para quando colidir
        self.img_morte = pg.image.load(os.path.join(diretorio_elementos, "fish_green_skeleton.png")).convert_alpha()
        self.img_morte = pg.transform.scale(self.img_morte, (72, 72))

        self.index_lista = 0 
        self.image = self.imagens_peixe[0] 
        self.rect = self.image.get_rect() 
        self.mask = pg.mask.from_surface(self.image) 
        self.pos_y_inicial = altura - 64 - 64
        self.rect.topleft = (100, self.pos_y_inicial) 
        self.pulo = False 

    def pular(self):
        self.pulo = True 
        self.som_pulo.play() 
        
    def update(self):
        if self.pulo:
            if self.rect.y <= 180:
                self.pulo = False 
            self.rect.y -= 20 
        else:
            if self.rect.y < self.pos_y_inicial:
                self.rect.y += 20 
            else:
                self.rect.y = self.pos_y_inicial 

        self.index_lista += 0.25 
        if self.index_lista >= len(self.imagens_peixe):
            self.index_lista = 0 
        self.image = self.imagens_peixe[int(self.index_lista)] 
        self.mask = pg.mask.from_surface(self.image)

class Bolhas(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self) 
        nomes_bolhas = ["bubble_a.png", "bubble_c.png"]
        self.imagens = [
            pg.image.load(os.path.join(diretorio_elementos, nome)).convert_alpha()
            for nome in nomes_bolhas
        ]
        self.sortear_bolha()
        self.rect.x = largura - randrange(30, 300, 40) 

    def sortear_bolha(self):
        img = choice(self.imagens)
        tamanho = randrange(64, 84)
        self.image = pg.transform.scale(img, (tamanho, tamanho))
        self.rect = self.image.get_rect()
        self.rect.y = randrange(30, 260, 30)
        self.velocidade = randrange(4, 9)

    def update(self):
        if self.rect.topright[0] < 0: 
            self.sortear_bolha()
            self.rect.x = largura 
        self.rect.x -= self.velocidade

# Carrega a imagem do chão de areia
LARGURA_CHAO = 64
TOTAL_CHAO = (largura * 2) // LARGURA_CHAO
LARGURA_TOTAL_CHAO = TOTAL_CHAO * LARGURA_CHAO

img_chao = pg.image.load(os.path.join(diretorio_elementos, "terrain_sand_top_a.png")).convert_alpha()
img_chao = pg.transform.scale(img_chao, (LARGURA_CHAO, 64))

class Chao(pg.sprite.Sprite):
    def __init__(self, pos_x):
        pg.sprite.Sprite.__init__(self) 
        self.image = img_chao
        self.rect = self.image.get_rect() 
        self.rect.y = altura - 64 
        self.rect.x = pos_x * LARGURA_CHAO 

    def update(self):
        self.rect.x -= velocidade_jogo 
        if self.rect.right <= 0: 
            self.rect.x += LARGURA_TOTAL_CHAO 

def redimensionar_proporcional(imagem, max_largura=64, max_altura=74, fator=None):
    w, h = imagem.get_size()
    if fator is not None:
        escala = fator
    else:
        escala = min(max_largura / w, max_altura / h)
    novo_w = max(1, round(w * escala))
    novo_h = max(1, round(h * escala))
    return pg.transform.scale(imagem, (novo_w, novo_h))

class Obstaculo(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self) 
        nomes_obstaculos = [
            "genericItem_color_051.png",
            "genericItem_color_127.png"
        ]
        self.imagens = [
            redimensionar_proporcional(
                pg.image.load(os.path.join(diretorio_obstaculos, nome)).convert_alpha(),
                max_largura=64,
                max_altura=74
            )
            for nome in nomes_obstaculos
        ]
        self.image = self.imagens[0] 
        self.rect = self.image.get_rect() 
        self.mask = pg.mask.from_surface(self.image) 
        self.rect.bottom = altura - 64 
        self.rect.x = largura 
        self.passou = False 

    def sortear(self):
        self.image = choice(self.imagens)
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.bottom = altura - 64

    def update(self):
        if self.rect.topright[0] < 0:
            self.sortear()
            self.rect.x = largura 
            self.passou = False 
        self.rect.x -= velocidade_jogo 

# Aliases para manter compatibilidade com nomes antigos se necessário
Dino = Peixe
Nunvens = Bolhas
Cacto = Obstaculo

todas_as_sprites = pg.sprite.Group() 

# Camada 1 (fundo): bolhas
for i in range(4):
    bolha = Bolhas() 
    todas_as_sprites.add(bolha) 

# Camada 2: chão contínuo de areia
lista_chao = []
for i in range(TOTAL_CHAO):
    chao = Chao(i) 
    todas_as_sprites.add(chao) 
    lista_chao.append(chao)

# Camada 3: obstáculos (algas/pedras)
obstaculo = Obstaculo() 
cacto = obstaculo 
todas_as_sprites.add(obstaculo) 

# Camada 4 (frente): peixe jogador
peixe = Peixe() 
dino = peixe 
todas_as_sprites.add(peixe) 

grupo_obstaculos = pg.sprite.Group() 
grupo_obstaculos.add(obstaculo) 

def reiniciar_jogo():
    global colidiu, pontos, velocidade_jogo 
    colidiu = False 
    obstaculo.sortear()
    obstaculo.rect.x = largura 
    obstaculo.passou = False 
    peixe.rect.y = peixe.pos_y_inicial 
    peixe.pulo = False 
    peixe.image = peixe.imagens_peixe[0] 
    for i, c in enumerate(lista_chao):
        c.rect.x = i * LARGURA_CHAO
    pontos = 0 
    velocidade_jogo = velocidade_padrao 

relogio = pg.time.Clock() 
piscou = False 
with map_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:

    while True:

        ret, frame = video.read() 

        frame = cv.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv.INTER_CUBIC) 

        rgb_frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR) 
        resultado = face_mesh.process(rgb_frame) 
        if resultado.multi_face_landmarks:
            mesh_coords = achandoMarcacoes(frame, resultado, True) 
            
            relacao = piscada(frame, mesh_coords, RIGHT_EYE, LEFT_EYE) 
            cv.putText(frame, f"Piscada: {relacao}", (50, 100), cv.FONT_HERSHEY_COMPLEX, 1.0, (255, 0, 0), 2) 
   
            # Se o olho direito piscar, marcação no vídeo
            if relacao > 4.5:
                cv.putText(frame, "Piscou", (50, 400), cv.FONT_HERSHEY_COMPLEX, 1.3, (0, 0, 255), 2) 
                piscou = True 
             
        cv.imshow("Video", frame) 
        key = cv.waitKey(1) 
        if key == ord('q') or key == ord('Q'):
            break 
   
        relogio.tick(30) 
        tela.fill(COR_FUNDO) 
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit() 
                exit() 
        if piscou:
            if peixe.rect.y != peixe.pos_y_inicial:
                pass 
            else:
                peixe.pular() 
        
        if piscou and colidiu == True:
            reiniciar_jogo() 
        
        pontuacao = exibe_mensagem(f"Pontos: {pontos}", 50, (255, 255, 255)) 
        tela.blit(pontuacao, (300, 10))
        
        colisoes = pg.sprite.spritecollide(peixe, grupo_obstaculos, False, pg.sprite.collide_mask) 
        todas_as_sprites.draw(tela) 
        
        if colisoes and colidiu == False:
            som_colisao.play() 
            colidiu = True 
            peixe.image = peixe.img_morte

        if colidiu == True:
            game_over = exibe_mensagem("GAME OVER", 40, (255, 255, 255)) 
            tela.blit(game_over, (largura // 2 - 120, altura // 2 - 30)) 
            restart = exibe_mensagem("Pisque para reiniciar", 20, (255, 255, 255)) 
            tela.blit(restart, (largura // 2 - 100, altura // 2 + 30)) 
        else:
            todas_as_sprites.update() 
            if not obstaculo.passou and obstaculo.rect.right < peixe.rect.left:
                pontos += 1 
                obstaculo.passou = True 
                # Aumenta a velocidade progressivamente com a pontuação (limite máximo de 22)
                velocidade_jogo = min(30, velocidade_padrao + (pontos // 3)) 
        
        pg.display.flip() 
        piscou = False 
    cv.destroyAllWindows() 
    cv.waitKey() 
    video.release() 
