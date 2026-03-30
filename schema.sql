-- Script de Criação para Tabela Única
CREATE TABLE CARV_CNJ (
    CARVCns VARCHAR(20) PRIMARY KEY,
    CARVUf VARCHAR(2),
    CARVCidadeId INT,
    CARVCidade VARCHAR(255),
    
    CARVNome VARCHAR(500),
    CARVPadrao VARCHAR(500),
    
    CARVCep VARCHAR(20),
    CARVEnd VARCHAR(1000),
    
    CARVStatus VARCHAR(50),
    CARVTipo VARCHAR(255),
    CARVSituacao VARCHAR(255),
    CARVInstalacao DATE,
    CARVAtribuicoes VARCHAR(MAX),
    
    CARVTelefone VARCHAR(255),
    CARVEmail VARCHAR(255),
    CARVWebsite VARCHAR(255),
    
    CARVResponsavel VARCHAR(500),
    CARVSubstituto VARCHAR(500),
    
    CARVHorarioFuncionamento VARCHAR(MAX),
    
    CARVDataAtualizacao DATETIME DEFAULT GETDATE()
);