from sqlalchemy import Column, String, Integer, Date, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Cartorio(Base):
    __tablename__ = 'CARV_CNJ'

    CARVCns = Column(String(20), primary_key=True)
    CARVUf = Column(String(2))
    CARVCidadeId = Column(Integer)
    CARVCidade = Column(String(255))
    
    CARVNome = Column(String(500))  # Denominacao Fantasia
    CARVPadrao = Column(String(500)) # Denominacao Padrao
    
    CARVCep = Column(String(20))
    CARVEnd = Column(String(1000))   # Endereco + Numero + Bairro formatado
    
    CARVStatus = Column(String(50))
    CARVTipo = Column(String(255))   # Tipo Cartório (Ex: PRIVATIZADO)
    CARVSituacao = Column(String(255))
    CARVInstalacao = Column(Date, nullable=True)
    CARVAtribuicoes = Column(String(None)) # Mapeia para VARCHAR(MAX)
    
    # Contatos
    CARVTelefone = Column(String(255))
    CARVEmail = Column(String(255))
    CARVWebsite = Column(String(255))

    # Dados Responsaveis
    CARVResponsavel = Column(String(500))    # Ex: Titular
    CARVSubstituto = Column(String(500))     # Ex: Substituto
    
    CARVHorarioFuncionamento = Column(String(None))
    
    CARVDataAtualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
