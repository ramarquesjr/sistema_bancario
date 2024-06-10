import textwrap
import functools
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime
from pathlib import Path

ROOT_PATH = Path(__file__).parent

class ContaIterador:
    def __init__(self, contas):
        self.contas = contas
        self._index=0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            conta = self.contas[self._index]
            return f"""
                Agencia: \t{conta.agencia}
                Número: \t{conta.numero}
                Títular:\t{conta.cliente.nome}
                Saldo:\t{conta.saldo:.2f}"""
        except IndexError:
            raise StopIteration
        finally: self._index +=1

class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def adicionar_conta(self, conta):
        self.contas.append(conta)

    def realizar_transacao(self, conta, transacao):
        if len(conta.historico.transacoes_do_dia()) >= 10:
            print("\n@@@ Você excedeu o número de transações permitidas para o dia! @@@")
            return
        transacao.registrar(conta)
        
class PessoaFisica(Cliente):
    def __init__ (self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf

    def __repr__(self):
        return f"<{self.__class__.__name__}: ('{self.cpf}'>"

class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()
        
    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)
    
    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia
    
    @property
    def cliente(self):
        return self._cliente
    
    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        saldo = self._saldo
        if valor > 0 and valor <= saldo:
            self._saldo -= valor
            print("\n=== Saque realizado com sucesso! ===")
            return True
        elif valor > saldo:
            print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
        return False
            
    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print("\n=== Depósito realizado ===")
        else:

            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
            return False
        return True
    
    
    def __str__(self):
        return f'''
            Agência {self.agencia}
            Conta: {self.numero}
            Usuário: {self.cliente.nome}
        '''
    
class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self.limite = limite
        self.limite_saques = limite_saques

    def sacar(self, valor):
        numero_saques = len([transacao for transacao in self.historico.transacoes if transacao["tipo"] == Saque.__name__])
        excedeu_saldo = valor > self.saldo
        excedeu_limite = valor > self.limite
        excedeu_saques = numero_saques >= self.limite_saques

        if excedeu_saldo:
            print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
        elif excedeu_limite:
            print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")
        elif excedeu_saques:
            print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")
        elif valor > 0:
            self._saldo -= valor
            print(f"Saque:\t\t R$ {valor:.2f}\n")
            numero_saques += 1
            print("\n=== Saque realizado com sucesso! ===")
            return True
        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
        return False
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: ('{self.agencia}', '{self.numero}', '{self.client.nome})>"

class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )
        
    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower() == tipo_transacao.lower():
                yield transacao
                
    def transacoes_do_dia(self):
        data_atual = datetime.now().date()
        transacoes = []
        for transacao in self._transacoes:
            data_transacao = datetime.strptime(transacao['data'], "%d-%m-%Y %H:%M:%S").date()
            if data_atual == data_transacao:
                transacoes.append(transacao)
        return transacoes

class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass
    
class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor
        
    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        if conta.sacar(self.valor):
            conta.historico.adicionar_transacao(self)

class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor
        
    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.depositar(self.valor):
            conta.historico.adicionar_transacao(self)

### Decoradores
def log_transacao(func):
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M%S")
        with open(ROOT_PATH /"log.txt", "a") as arquivo:
            arquivo.write(
                f"[{data_hora}] Função: '{func.__name__}' executada com os argumentos {args} e {kwargs} ."
                f"Retornou {resultado}\n")
        return resultado
    return envelope

def op(funcao):
    @functools.wraps(funcao)
    def envelope(*args, **kwargs):
        cpf = input("Informe o CPF do cliente: ")
        cliente = filtrar_cliente(cpf,*args, **kwargs)
        if not cliente:
            print("\n@@@ Cliente não encontrado @@@")
            return
        transacao = funcao(*args, **kwargs)
        conta = recuperar_conta_cliente(cliente)
        if not conta:
            return
        cliente.realizar_transacao(conta, transacao)
    return envelope
####

def menu():
    menu = """

    [d] Depositar
    [s] Sacar
    [e] Extrato
    [nu] Criar usuários
    [nc] Cria conta
    [lc] Listar contas
    [q] Sair

    => """
    return input(textwrap.dedent(menu))

def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [ cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None

def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ O cliente não possui contas @@@")
    return cliente.contas[0]

@log_transacao
@op
def sacar(clientes):
    valor = float(input("Informe o valor do saque: "))
    transacao = Saque(valor)
    return transacao

@log_transacao
@op
def depositar(clientes):
    valor = float(input("Informe o valor do depósito: "))
    transacao = Deposito(valor)
    return transacao

@log_transacao
def exibir_extrato(clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)
    
    if not cliente:
        print("\n@@@ Cliente não encontrado @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        print("\n@@@ Não existe conta para esse cliente@@@")
        return

    print("\n================ EXTRATO ================")
    transacoes = conta.historico.transacoes
    tem_transacao = False
    extrato = ""
    for transacao in conta.historico.gerar_relatorio():
        tem_transacao=True
        extrato += f"\n{transacao['data']}\n {transacao['tipo']}:\t R$ {transacao['valor']:.2f}"
    if not tem_transacao:
        extrato = "@@@ Não foram realizadas movimentações @@@"
    print(extrato)
    print(f"\nSaldo:\t\t R$ {conta.saldo:.2f}")
    print("==========================================")
    
@log_transacao
def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente números): ")
    cliente = filtrar_cliente(cpf, clientes)
    if cliente:
        print(f"\n@@@ Já existe cliente com este CPF @@@")
        return
    nome = input("Informe o nome completo: ")
    data_nascimento = input ("Informe a data de nascimento no formato dd-mm-aaa: ")
    endereco = input("Informe o endereço (logradouro, número, bairro, cidade / sigla estado): ")
    cliente = PessoaFisica(nome, data_nascimento, cpf, endereco)
    clientes.append(cliente)
    print("=== Cliente criado com sucesso! ===")

def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do usuário: ")
    cliente = filtrar_cliente(cpf, clientes)
    if not cliente:
        print("\n@@@ Cliente não encontrado. @@@")
        return
    avancado = input("Deseja definir outros parâmetros da conta? (y/N)")
    if avancado == "y":
        limite = float(input("Defina o valor limite de saque diário: ") or 500)
        limite_saques = int(input("Defina o limite de saques: ") or 3)
        conta = ContaCorrente(cliente=cliente, numero=numero_conta, limite=limite, limite_saques=limite_saques)
        contas.append(conta)
        cliente.contas.append(conta)
    else:
        conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
        contas.append(conta)
        cliente.contas.append(conta)
    print("\n=== Conta criada com sucesso! ===")

def listar_contas(contas):
    for conta in ContaIterador(contas):
        print("="*100)
        print(textwrap.dedent(str(conta)))

def main():

    clientes =[]
    contas = []

    while True:
        opcao = menu()
        if opcao == "d":
            depositar(clientes)    
        elif opcao == "s":
            sacar(clientes)    
        elif opcao == "e":
            exibir_extrato(clientes, contas)
        elif opcao == "nu":
            criar_cliente(clientes)
        elif opcao == "nc":
            numero_conta = len(contas) +1
            criar_conta(numero_conta, clientes, contas)
        elif opcao == "lc":
            listar_contas(contas)
        elif opcao == "q":
            break
        else:
            print("Operação inválida, por favor selecione novamente a operação desejada.")
            
main()