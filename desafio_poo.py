from abc import ABC, abstractclassmethod, abstractproperty
import textwrap
from datetime import datetime

class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def adicionar_conta(self, conta):
        self.contas.append(conta)

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)
        

class PessoaFisica(Cliente):
    def __init__ (self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf

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
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%s"),
            }
        )
        
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

def operar(clientes, tipo):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado @@@")
        return
    if (tipo=="Saque"):
        valor = float(input("Informe o valor do saque: "))
        transacao = Saque(valor)
    elif(tipo=="Depósito"):
        valor = float(input("Informe o valor do depósito: "))
        transacao = Deposito(valor)
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    cliente.realizar_transacao(conta, transacao)

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
    extrato = ""
    if not transacoes:
            extrato = "Não foram realizadas transações."
    else:
        for trans in transacoes:
            extrato += f"\n{trans['tipo']}: \t\t R$ {trans['valor']:.2f}"
    print(extrato)
    print(f"\nSaldo:\t\t R$ {conta.saldo:.2f}")
    print("==========================================")
    
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
    for conta in contas:
        print('='*100)
        print(textwrap.dedent(str(conta)))

def main():

    clientes =[]
    contas = []

    while True:
        opcao = menu()
        if opcao == "d":
            operar(clientes, "Depósito")
        elif opcao == "s":
            operar(clientes, "Saque")
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