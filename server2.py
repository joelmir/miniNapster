#Servidor 2
import socket,time
from threading import Thread
from datetime import datetime

class Cliente:
    def __init__(self,nome,ip,porta):
        self.ip = ip
        self.porta = porta
        self.nome = nome
        self.arquivos = None
        self.time = datetime.today()
        
    
class Servidor:
    def __init__(self,porta,ip):
        self.debug = False
        self.porta      = porta
        self.ip         = ip
        self.clientes   = [] #clientes ativos
        self.porta_default_cliente = 50001
        
        #Abre um thread para controle de time out
        th=Thread( target=self.time_out, args = () )
        th.start() 
        
        self.escuta()
        
    def time_out(self):
        while 1:
            time.sleep(2)
            for cliente in self.clientes:
                #Se o cliente estiver inativo por mais de 10 segundos
                if (datetime.today() - cliente.time).seconds > 10:
                    prot = {'nome': 'server','opcao' : 'conexao','dado' : 'timeout'}
                    self.envia_pacote(str(prot),cliente)
                    self.remove_cliente(cliente)
                #Se o cliente estiver inativo em um periodo de 5 a 10 segundos
                elif (datetime.today() - cliente.time).seconds > 5 :
                    prot = {'nome': 'server','opcao' : 'ping','dado'  : ''}
                    self.envia_pacote(str(prot),cliente)
    
    def remove_cliente(self,cliente):
        self.clientes.remove(cliente)
        print 'Cliente '+cliente.nome+' - '+cliente.ip+':'+str(cliente.porta)+' removido'
    
    '''
    Fica aceitando conexoes e criando uma nova thread para cada uma
    '''
    def escuta(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, self.porta))
        print 'Servidor Napster no AR e pronto para a guerra!!!!\n'
        while 1:
            #Aguarda conexoes
            s.listen(1)
            #Recebeu uma nova conexao
            conn, addr = s.accept()
            #Abre uma nova thead para tratar a conexao e libera a escuta do servidor
            th=Thread( target=self.nova_conexao, args = (conn,addr,) )
            th.start() 
    '''
    Recebe a conexao e realiza o tratamento necessario para atender sua necessidade
    '''    
    def nova_conexao(self,conn,addr):
        #recebe o dado
        dados = conn.recv(1024)
        #fecha a conexao para nao ficar ociosa
        conn.close()
        #converte os dados recebido
        try:
            dados = eval(dados)
            #verifica a integridade do pacote, se ele segue o protocolo
            if type(dados) == dict and dados.has_key('nome') and dados.has_key('opcao') and dados.has_key('dado'):
                #realiza o tratamento do pacote integro
                if type(dados['dado']) == dict and dados['dado'].has_key('porta'):
                    porta = dados['dado']['porta']
                else:
                    porta = self.porta_default_cliente
                    
                self.trata_dados_cliente(addr,dados,porta)
            else:
                raise SyntaxError
            
        except SyntaxError:
            erro = 'O pacote nao esta dentro dos padroes estabelecido '
            if self.debug:
                erro += '\n### - Pacote - ###\n'+str(dados)+'\n### - Final do Pacote - ###'
                
            cliente = Cliente('None',addr[0],self.porta_default_cliente)
            self.trata_erro(erro,cliente)
            return
            
    '''
    recebe o pacote dentro dos padroes estabelecidos e realiza o tratamento dos dados
    '''
    def trata_dados_cliente(self,addr,dados,porta):
        cliente = [cliente for cliente in self.clientes if cliente.ip == addr[0] and cliente.porta == porta]
        
        #Se o cliente nao estiver cadastrado, tenta cadastrar
        if not cliente:
            #trata o cadastro do novo cliente
            cliente = self.cadastra_cliente(addr[0], dados, porta)
            
        #Se retornar mais de um cliente, verifica se tem porta informada no pacote, ou se e um pacote errado
        elif len(cliente) > 1:
            erro = "O pacote enviado nao e valido, encotrado mais de um cliente para o mesmo ip "
            if self.debug:
                erro += "\n### - Pacote - ### \n "+str(dados)+"\n ### - Final do Pacote - ###"
            for c in cliente:
                trata_erro(erro,c)
            return
                
        #Caso ocorreu alguma inconformidade, o erro ja foi lancado, entao para de processar o pacote
        else:
            cliente = cliente[0]

        #Se for um dicionario, e porque o cliente esta rodando em um porta diferente
        if type(dados['dado']) == dict:
            #Trata o pacote conforme o padrao
            dados['dado'] = dados['dado']['dado']
            
        #Se o cliente esta nulo, deu erro
        if not cliente: return
        
        #atualiza a hora de contato
        cliente.time = datetime.today() 
        
        #dicionario que chama a opcao conforme a opcao
        opcao = {'conexao':self.conexao,'arquivos':self.arquivos,'pesquisa':self.pesquisa,'pong':self.pong}
        #chama a funcao referente a opcao do pacote passando por parametro o cliente em questao e o pacote recebido
        opcao[dados['opcao']](cliente,dados['dado'])
        
    '''
    Cadastro o novo cliente
    '''    
    def cadastra_cliente(self,ip,dados,porta):
        #cadastra o novo cliente com as informacoes recebidas
        cliente = Cliente(dados['nome'],ip,porta)
        
        if dados['opcao'] != 'conexao':
            erro = 'O pacote esta fora de ordem, solicite a conexao para iniciar a comunicacao com o servidor'
            if self.debug:
                erro +='\n### - Pacote - ###\n'+str(dados)+'\n### - Final do Pacote - ###'
            self.trata_erro(erro,cliente)
            return
            
        #adiciona na lista de clientes o cliente cadastrado
        self.clientes.append(cliente)
        #retorna o cliente para prosseguir no tratamento
        return cliente
    
    '''
    Tratamento dos pacotes
    '''
    
    def conexao(self,cliente,dados):
        if dados == 'Nova':
            prot = {'nome': 'server','opcao' : 'conexao','dado'  : 'aceitou'}
            self.envia_pacote(str(prot),cliente)
        if dados == 'encerrada':
            self.remove_cliente(cliente)
    
    def arquivos(self,cliente,dados):
        if type(dados) == list:
            cliente.arquivos = dados
            prot = {'nome': 'server','opcao' : 'arquivos','dado'  : 'concluiu'}
            self.envia_pacote(str(prot),cliente)
        else:
            erro = 'O pacote de arquivos nao esta no formato correto, ex: ["arq1.txt","arq2.txt"]'
            if self.debug:
                erro+='\n### - Pacote - ###\n'+str(dados)+'\n### - Final do Pacote - ###'
                
            erro = {'dado':'erro','erro':erro}
            self.trata_erro(erro,cliente)
            
    def pesquisa(self, cliente,dados):
        pesquisa = []
        for cli in [clientes for clientes in self.clientes if clientes.arquivos and clientes != cliente]:
            for arq in cli.arquivos:
                if dados.upper() in arq.upper():
                    pesquisa.append((cli.ip,cli.porta,cli.nome,arq))#Adiciona uma tupla de cliente e arquivo
        prot = {'nome': 'server','opcao' : 'pesquisa','dado'  : pesquisa}
        self.envia_pacote(str(prot),cliente)
        
    def pong(self,cliente,dados):
        # O pacote pong nao precisa ser processado
        pass
       
    '''
    Realiza o envio dos pacotes
    '''    
    def envia_pacote(self,pacote,cliente):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((cliente.ip,cliente.porta))
            s.send(pacote)
            s.close()
        except socket.error, msg:
            erro = 'nao foi possivel envia o pacote ao cliente ('+cliente.nome+') '+cliente.ip+':'+str(cliente.porta)
            if self.debug:
                erro+='\nDevido ao erro\n - ERRO - \n'+str(msg)
            print erro
    '''
    Realiza o tratamento de erro
    '''
    def trata_erro(self,erro,cliente):
        if self.debug:
            print erro
        prot = {'nome': 'server','opcao' : 'erro','dado'  : erro}
        self.envia_pacote(str(prot),cliente)
    
    
#Inicializa o Servidor caso o aquivo for chamado direto   
if __name__ == '__main__':
    s = Servidor(50002,'')