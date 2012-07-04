#Cliente 2
import socket,os,time,sys
from threading import Thread
from datetime import datetime

class Cliente:
    def __init__(self, servidor, porta_server, porta_cliente):
    
        self.debug = True
    
        self.HOST = servidor
        self.PORT = porta_server
        self.PORT_ME = porta_cliente
        
        #Arquivos do cliente
        self.arq_cli = {}

        #controle das threads
        self.done = True
        self.thread_done = True
        
        self.nome = raw_input("Digite seu nome: ")
        
        #Inicia a escuta
        th = Thread(target=self.escuta, args=())
        th.start()
        
        #Inicia o cliente
        self.main_loop()

    def fechar(self):
        self.done = False
        self.thread_done = False 
        
    def envia(self,pacote,ip,porta):
        try:
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.connect((ip,porta))
            c.send(str(pacote))
            c.close()
        except socket.error, msg:
            erro =  'nao foi possivel envia o pacote ao cliente/servidor '+ip+':'+str(porta)
            if self.debug and False:
                erro+='\nDevido ao erro\n - ERRO - \n'+str(msg)
            print erro
            
    def nova_conexao(self, conn,addr):
        #recebe os dados
        data = conn.recv(2048)
        
        #verifica se os dados sao validos
        if data != None:
            try:
                dados = eval(data)
                if type(dados) == dict and dados.has_key('nome') and dados.has_key('opcao') and dados.has_key('dado'):
                    self.trata_requisicao(dados,addr, conn)
                else:
                    raise SyntaxError
            except SyntaxError:
                erro = 'O pacote nao esta dentro dos padroes estabelecido '
                if self.debug:
                    erro += '\n### - Pacote - ###\n'+str(dados)+'\n### - Final do Pacote - ###'
                # TODO //Trata erro   
        conn.close()    
    def trata_requisicao(self, dados, addr,conn):
        #outro cliente conversando
        if dados['opcao'] == 'arquivos' and dados['dado'] == 'pedido':
            self.envio_arquivo(conn)
        
        #conversa com o servidor
        elif dados['nome'] == 'server' and self.HOST == addr[0]:
            if dados['opcao']=='erro':
                print dados['dado']
                
            if dados['opcao']=='arquivos':
                if type(dados['dado']) != dict:
                    print '\nO servidor '+dados['dado']+' a lista de aquivos'
                else:
                    print dados['dado']['erro']
                    
            if dados['opcao']=='conexao':
                print '\nO servidor '+dados['dado']+' a conexao'
                if dados['dado'] == 'Encerrada':
                    self.fechar()
                    
            if dados['opcao']=='pesquisa':
                arq = dados['dado']
                if not arq:
                    print 'Sua pesquisa nao retornou nenhum arquivo'
                else:
                    for idx,a in enumerate(arq):
                        self.arq_cli[a] = idx
                    print '\nO servidor retornou '+str(len(arq))+' arquivos'
                    
            if dados['opcao']=='ping':
                prot = {'nome': self.nome,'opcao' : 'pong','dado':{'dado':'','porta':self.PORT_ME}}
                self.envia(str(prot), self.HOST,self.PORT)

        #print data
        

    def escuta(self):
        try:
            es = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            es.bind(('', self.PORT_ME))
        
            while self.thread_done:
                es.listen(1)
                conn, addr = es.accept()
                #abre uma nova thread para tratar a requisicao e fica ocioso para tratar novas requisicoes
                th2 = Thread(target=self.nova_conexao, args=(conn,addr,))
                th2.start()
        except socket.error, msg:
            erro =  'nao foi possivel proceguir com o recebimentos de pacotes\nDevido ao erro\n - ERRO - \n'+str(msg)
            print erro
            self.fechar()
            
    def envio_arquivo(self, conn):
        date = datetime.today() #pega a hora atual
        prot = {'nome': self.nome,'opcao' : 'arquivos','dado':'nome'}
        conn.send(str(prot))
        while 1:
            if (datetime.today() - date).seconds > 5: #se ficar mais que 5 segundos sem resposta encerra a conexao
                prot = {'nome': self.nome,'opcao' : 'arquivos','dado':'cancelado'}
                conn.send(str(prot))
                return
            date = datetime.today() #pega a hora atual    
            data = conn.recv(1024)
            if data != None:
                date = datetime.today() #atualiza o ultimo contato
                dados = eval(data)
                if type(dados) == dict and dados.has_key('nome')\
                   and dados.has_key('opcao') and dados.has_key('dado'):
                    #verifica se a opcao
                    if dados['opcao']=='arquivos':
                        d = dados['dado']
                        #se o pacote tem os dados correto
                        if type(d) == dict and d.has_key('nome'):
                            
                            
                            #tenta abrir o arquivo
                            try:
                                arquivo = open(os.path.join('.','shared', d['nome']),'rb')
                                try:
                                    #Envia a confirmacao para criar o arquivo no cliente
                                    prot = {'nome': self.nome,'opcao' : 'arquivos','dado':'pedido'}
                                    conn.send(str(prot))

                                    #tenta ler o arquivo em intervalos de 512
                                    while 1:
                                        palavra = arquivo.read(200)
                                        if palavra == '':
                                            break
                                        #tempo de espera para nao congestionar a rede e dar tempo de escrever, caso der erro, aumentar o tempo 
                                        time.sleep(0.1)
                                        #envia para o cliente o arquivo
                                        prot = {'nome': self.nome,'opcao' : 'arquivos','dado':{'nome':d['nome'],'stream':palavra,'estado':'enviando'}}
                                        conn.send(str(prot))
                                            
                                except:
                                    prot = {'nome': self.nome,'opcao' : 'arquivos','dado':{'nome':d['nome'],'estado':'abortado'}}
                                    conn.send(str(prot))
                                    return
                            except:
                                prot = {'nome': self.nome,'opcao' : 'arquivos','dado':{'nome':d['nome'],'estado':'nao_encontrado'}}
                                conn.send(str(prot))
                                return
                            #envia para o cliente a confirmacao do termino do arquivo
                            prot = {'nome': self.nome,'opcao' : 'arquivos','dado':{'nome':d['nome'],'estado':'conluido'}}
                            conn.send(str(prot))
                            return
    def main_loop(self):
        while self.done:
            time.sleep(1)
            opcao1 = raw_input('''
            
    Digite 1 para conectar ao servidor
    Digite 2 para realizar uma pesquisa
    Digite 3 para listar as pesquisas
    Digite 4 para Sair

''')

            if opcao1 == '1':
                prot = {'nome': self.nome,'opcao' : 'conexao','dado'  :{'dado':'Nova','porta':self.PORT_ME}}
                self.envia(str(prot), self.HOST,self.PORT)
                try:
                    arquivos = os.listdir('./shared')
                    prot = {'nome': self.nome,'opcao' : 'arquivos','dado'  : {'dado':arquivos,'porta':self.PORT_ME}}
                    self.envia(str(prot), self.HOST,self.PORT)
                except:
                    print 'Verifique se a pasta "shared" esta no diretorio de execucao'
                continue
            if opcao1 == '2':
                arquivos = raw_input("\nDigite o nome do arquivo: ")
                prot = {'nome': self.nome,'opcao' : 'pesquisa','dado'  : {'dado':arquivos,'porta':self.PORT_ME}}
                self.envia(str(prot), self.HOST,self.PORT)
                continue
            if opcao1 == '3':
                dict_arq = self.arq_cli.items()
                dict_arq.sort(key=lambda x: x[1])
                for key,value in dict_arq:
                    print 'Opcao '+str(value)+' - ('+ str(key[2])+') cliente: '+str(key[0])+' porta: '+ str(key[1])+' arquivo: '+ str(key[3])
                opcao2 = raw_input('Digite a opcao ou "S" para sair: ')
                
                cliente = [key for key,value in self.arq_cli.items() if str(value) == opcao2]
                if opcao2.upper() == 'S':
                    print '\nPesquisa cancelada\n'
                    continue
                if not cliente:
                    print '\nOpcao invalida\n'
                    continue
                prot = {'nome': self.nome,'opcao' : 'arquivos','dado':'pedido'}

                try:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((cliente[0][0],cliente[0][1]))
                except socket.error, msg:
                    erro =  'nao foi possivel envia o pacote ao cliente '+ip+':'+str(porta)
                    if self.debug and False:
                        erro+='\nDevido ao erro\n - ERRO - \n'+str(msg)
                    print erro    
                    continue

                arquivo = None
                conn.send(str(prot))
                while 1:
                    dados = conn.recv(2048)
                    try:
                        dados = eval(dados)
                    except SyntaxError:
                        erro = 'O pacote nao esta dentro dos padroes estabelecido '
                        if self.debug:
                            erro += '\n### - Pacote - ###\n'+str(dados)+'\n### - Final do Pacote - ###'
                        
                        print erro
                        continue
                    if type(dados) == dict and dados.has_key('nome')\
                       and dados.has_key('opcao') and dados.has_key('dado'):
                        if dados['opcao']=='arquivos':
                            if type(dados['dado']) == dict:
                                if  arquivo == None:
                                    print 'nao foi recebido o protocolo de abertura de arquivo'
                                    break
                               
                                d = dados['dado']
                                if d.has_key('estado') and d['estado'] == 'enviando':
                                    arquivo.write(d['stream'])
                                    sys.stdout.write('.')
                                    sys.stdout.flush()
                                if d.has_key('estado') and d['estado'] == 'abortado':
                                    print 'O recebimento do arquivo foi abortado'
                                    arquivo.close()
                                    break
                                if d.has_key('estado') and d['estado'] == 'nao_encontrado':
                                    print 'O arquivo nao foi encontrado'
                                    arquivo.close()
                                    break
                                if d.has_key('estado') and d['estado'] == 'conluido':
                                    print '\nO recebimento do arquivo foi conluido'
                                    arquivo.close()
                                    break

                            if  dados['dado']== 'nome':
                                prot = {'nome': self.nome,'opcao' : 'arquivos','dado':{'nome':cliente[0][3]}}
                                conn.send(str(prot))
                            if dados['dado']== 'pedido':
                                arquivo = open(os.path.join('.','shared', 'copy_'+cliente[0][3]),'wb')
                                print 'Recebendo'
                            if dados['dado'] == 'cancelado':
                                print 'Cancelado por que a conexao esta ociosa por mais de 2 segundos'
                                break
                conn.close()
            if opcao1 == '4':
                prot = {'nome': self.nome,'opcao' : 'conexao','dado'  : {'dado':'encerrada','porta':self.PORT_ME}}
                self.envia(str(prot), self.HOST,self.PORT)
                prot = {'nome': self.nome,'opcao' : 'conexao','dado'  :'encerrada'}
                self.envia(str(prot),'127.0.0.1',self.PORT_ME)
                self.fechar()

#Ordem dos parametros
                
#ip servidor
#porta servidor
#porta cliente                
c = Cliente('127.0.0.1',50002,50010)
