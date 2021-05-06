from player.parser import *
from r2a.ir2a import IR2A
import time
import statistics


class R2ANewAlgoritm1(IR2A):

    #metodo que inicia variaveis no programa
    def __init__(self, id):
        IR2A.__init__(self, id)
        #parsed_mpd serve para pegar as qualidades disponiveis
        self.parsed_mpd = ''
        #vazoes, lista que armagena td as vazoes calculadas
        self.vazoes = []
        #qi, lista que armazenas as qualidades(no caso de 0 a 19)
        self.qi = []
        #variavel para marcar o momento que algo foi enviado
        self.tempo = 0
        #lista que armazena todas as qualidades que o programa ja usou ate entao
        self.qualidades = []
        #variavel para ter acesso aos metodos whiteboard
        self.dados = self.whiteboard




    #metodo que faz a primeira chamada ao connection handler
    def handle_xml_request(self, msg):
        #momento que foi feito o pedido
        self.tempo = time.perf_counter()

        self.send_down(msg)



    #metodo que recebe que recebe a requisicao
    def handle_xml_response(self, msg):
        #recebe do host as informacoes em que o video esta codificado
        self.parsed_mpd = parse_mpd(msg.get_payload())
        #armazena as qualidades
        self.qi = self.parsed_mpd.get_qi()

        #usando o tempo em que foi enviado, o tamanho da mensagem e o tempo
        #que foi recebido, eh assim calculado a primeira vazao e armazenada na lista
        deltatempo = time.perf_counter() - self.tempo
        deltaespaco = msg.get_bit_length()
        vazao = deltaespaco/deltatempo
        self.vazoes.append(vazao)

        self.send_up(msg)




    #metodo que a partir da vazao calculada decidi a qualidade
    #que sera pedida para ser baixada
    def handle_segment_size_request(self, msg):
        #momento em que foi feito o pedido
        self.tempo = time.perf_counter()
        #armazena o tamanho da lista de vazoes
        valores = len(self.vazoes)

        #variavel iniciada aqui apenas para nao gerar erro de compilacao
        media = statistics.harmonic_mean(self.vazoes)
        #enquanto nao houverem 50 elementos na lista, a media sera calculada por
        #baixo para nao ter perigo de nao conseguir continuar baixando
        if (valores < 50):
            media = 3*statistics.harmonic_mean(self.vazoes)/5

        #se ja houver 50 elementos, eh feita a media dos ultimos 50 elementos
        #isso ocorre para que elementos mais antigos sejam descartados para
        #nao gerar um numero padrao para o resto todo da execucao
        else:
           lista = self.vazoes[(valores-50):]            
           media = statistics.harmonic_mean(lista)


        #inicia as duas variaveis para nao ter perigo de gerar erro de compilacao
        indice = 0
        qualidade = self.qi[0]
        #faz um loop para ver com base na media das vazoes, o proximo qi
        #a ser baixado, sendo q o qi tem q ser menor ou igual ao resultado
        #da media, qualidade pega o valor de qi e indice armazena o numero dessa qi(0 a 19)
        for idx, val in enumerate(self.qi):
            if media >= val:
                qualidade = val
                indice = idx
        
        #pega o numero de elementos na lista e buffer pega o tamanho do buffer o momento
        tamanho = len(self.qualidades)
        buffer = self.dados.get_playback_buffer_size()

        #se houver ja uma qualidade na lista entra nesse if
        #nele sera feito, se o resultado do for passado, ou seja a qualidade escolhida
        #eh menor ou maior que a ultima que foi escolhida antes

        #e analisa o tamanho do buffer, caso ele nao exista ainda, primeiros ifs,
        # a qualidade final sera o resultado do for anterior, se ele tiver pelo menos 5 elementos
        #ja que nao eh sera mudado drasticamente a qualidade, diminuindo ou aumentando
        # em apenas uma unidade, mas caso tenha menos
        #sera mudado imediatamente para o valor do loop for, e se forem iguais nada muda
        if(tamanho>0):
            index = self.qualidades[(tamanho-1)]
            if (self.qi[indice] > self.qi[index]):
                if  (len(buffer) == 0):
                    indice = indice
                elif (buffer[len(buffer)-1][1]>5):
                    indice = indice
                else:
                    indice = index + 1
              
            elif (self.qi[indice]<self.qi[index]):
                if  (len(buffer) == 0):
                    indice = indice                
                elif (buffer[len(buffer)-1][1]>5):
                    indice = index - 1
                else:
                    indice = indice
 
            else: 
                indice = index


        #depois entao eh armazenado aqui a qualidade escolhida no fim e entao eh pedido a ser baixada
        qualidade = self.qi[indice]
        #adiciona a lista essa ultima qualidade escolhida
        self.qualidades.append(indice)

        msg.add_quality_id(qualidade)
        self.send_down(msg)




    #metodo que recebe a mensagem de qual qualidade a ser baixada, e calcula
    #com o momento em que foi recebida a vazao e adiciona ela a lista
    def handle_segment_size_response(self, msg):

        deltatempo = time.perf_counter() - self.tempo
        deltaespaco = msg.get_bit_length()
        vazao = deltaespaco/deltatempo
        self.vazoes.append(vazao)
        
        self.send_up(msg)



    #metodos que executariam antes e depois de todos acima
    #porem nao houve necessidade de usa-los, e o professor mesmo nao
    #usou nas aulas  mesmo kkk
    def initialize(self):
        pass

    def finalization(self):
        pass