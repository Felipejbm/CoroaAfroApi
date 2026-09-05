
from pydantic import BaseModel
from datetime import date

class LoginReq(BaseModel):
    email: str
    senha: str

class EmpreendedorCreate(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str
    data_cadastro: date

class EmpresaCreate(BaseModel):
    nome: str
    data_fundacao: date
    cnpj: str
    segmento: str
    endereco: str
    porte: str
    num_funcionarios: int
      
class TrilhaCreate(BaseModel):
    titulo: str
    tipo_trilha: str

class AtividadeCreate(BaseModel):
    titulo_tarefa: str
    conteudo: str

class MentorCreate(BaseModel):
    nome: str
    especialidade: str
    biografia: str

class MensagemChatCreate(BaseModel):
    texto_mensagem: str
    data_envio: date
    lida: bool
    remetente: str

class PostagemChatCreate(BaseModel):
    conteudo_texto: str
    midia_url: str
    data_publicacao: date

class TransacoesCreate(BaseModel):
    tipo_transacao: str
    valor: float
    data: date
    status: str

class SaldoCreate(BaseModel):
    saldo: float
    meta_faturamento: float
    data: date
    total_entradas: int
    total_saidas: int
    valor_inicial: float
    saldo_final: float

class MetricasMarketingCreate(BaseModel):
    data_coleta: date
    seguidores_total: int
    alcance_postagem: int
    engajamento_taxa: int
    cliques_bio: int

