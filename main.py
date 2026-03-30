import requests
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from db import init_db, SessionLocal
from models import Cartorio

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configurações de API
BASE_URL = "https://justicaabertaapi.cnj.jus.br/v1/api"
UFS = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 
       'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

HEADERS = {
    'accept': '*/*',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'origin': 'https://justicaaberta.cnj.jus.br',
    'referer': 'https://justicaaberta.cnj.jus.br/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

COOKIES = {
    'INGRESSCOOKIE': '7cde68657093af981ec12de59095ef62|48a4a4d878df70e52381fc7bd6331f18',
    'adonis-session': 's%3AeyJtZXNzYWdlIjoiY21uOHRkdjF2MmYyNTBpbzcwbjVtYWk3ciIsInB1cnBvc2UiOiJhZG9uaXMtc2Vzc2lvbiJ9.7f2rH-tPgG8bp7fThHZBR91M1Ourdk96ZGTjBM3wztM'
}

def safe_date(date_str):
    if not date_str: return None
    try:
        if "T" in date_str: date_str = date_str.split("T")[0]
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def fetch_cidades(uf):
    url = f"{BASE_URL}/cidades/listar/{uf}"
    try:
        resp = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erro ao buscar cidades para UF {uf}: {e}")
        return []

def fetch_serventias(cidade_id, uf, nome_cidade):
    serventias_ativas = []
    page = 1
    last_page = 1
    while page <= last_page:
        url = f"{BASE_URL}/serventias?assignments=&page={page}&perPage=50&search="
        payload = {"cidade_id": cidade_id, "uf": uf, "cns": None}
        try:
            resp = requests.post(url, headers=HEADERS, cookies=COOKIES, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if page == 1 and 'meta' in data:
                last_page = data['meta'].get('last_page', 1)
            
            for item in data.get('data', []):
                if item.get('status') == 'Ativo':
                    item['nome_cidade'] = nome_cidade
                    item['cidade_id'] = cidade_id
                    item['uf'] = uf
                    # Garantir que carregamos infos que vêm da lista também:

                    serventias_ativas.append(item)
            page += 1
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Erro em serventias (Cidade: {cidade_id}, pag {page}): {e}")
            break
    return serventias_ativas

def processa_cartorio(cartorio_info):
    cns = cartorio_info.get("cns")
    if not cns: return None
    
    sess = requests.Session()
    sess.headers.update(HEADERS)
    sess.cookies.update(COOKIES)
    
    try:
        r_basico = sess.get(f"{BASE_URL}/serventias/{cns}", timeout=15)
        d_basico = r_basico.json() if r_basico.status_code == 200 else {}
        
        r_loc = sess.get(f"{BASE_URL}/serventias/{cns}/localizacao", timeout=15)
        d_loc = r_loc.json() if r_loc.status_code == 200 else {}
        
        r_resp = sess.get(f"{BASE_URL}/serventias/{cns}/responsaveis", timeout=15)
        d_resp = r_resp.json() if r_resp.status_code == 200 else []
        
        r_hor = sess.get(f"{BASE_URL}/serventias/{cns}/horarios-funcionamento", timeout=15)
        d_hor = r_hor.json() if r_hor.status_code == 200 else []

        return build_cartorio_model(cartorio_info, d_basico, d_loc, d_resp, d_hor)

    except Exception as e:
        logger.error(f"Erro ao enriquecer dados CNS {cns}: {e}")
        return None

def build_cartorio_model(info, basico, loc, resp_list, hor_list):
    # Formatação de campos compostos
    end_parts = [
        loc.get("endereco") or basico.get("endereco") or info.get("endereco"),
        loc.get("numero") or basico.get("numero") or info.get("numero"),
        loc.get("bairro") or basico.get("bairro") or info.get("bairro")
    ]
    # Remove Nones e espaços vazios antes de juntar
    endereco_completo = ", ".join([str(p).strip() for p in end_parts if p and str(p).strip()])
    
    # Busca responsavel titular vs substituto
    responsavel_titular = None
    responsavel_substituto = None
    
    # A base do CNJ traz varios, normalmente o titular ("-") ou ativo e depois os substitutos.
    # Como não temos um field especifico de "substituto=true/false" tão claro pro cargo, vamos classificar o primeiro como titular
    for r in resp_list:
        if isinstance(r, dict):
            nome_val = r.get("nome")
            if nome_val:
                nome = str(nome_val).strip()
                # As vezes a situacao juridica traz a palavra substituto, mas de qualquer forma listaremos:
                if responsavel_titular is None:
                    responsavel_titular = nome
                elif responsavel_substituto is None and nome != responsavel_titular:
                    responsavel_substituto = nome
    
    # Formatação de Horários (Formato: "segunda-feira: 09:00 às 17:00 | terça-feira: Fechado")
    lista_horarios = []
    for h in hor_list:
        dia = h.get("dia", "")
        if h.get("fechado"):
            lista_horarios.append(f"{dia}: Fechado")
        else:
            expedientes = h.get("horarios_funcionamento", [])
            if expedientes:
                ini = expedientes[0].get("inicio", "")
                fim = expedientes[0].get("fim", "")
                lista_horarios.append(f"{dia}: {ini} às {fim}")
    str_horarios = " | ".join(lista_horarios) if lista_horarios else None

    # Mapeando todos para a classe Cartorio que equivale a estrutura da CARV_CNJ
    c = Cartorio(
        CARVCns=info.get("cns"),
        CARVUf=info.get("uf"),
        CARVCidadeId=info.get("cidade_id"),
        CARVCidade=info.get("nome_cidade"),
        
        CARVNome=basico.get("denominacao_fantasia") or info.get("denominacao_fantasia"),
        CARVPadrao=basico.get("denominacao_padrao") or info.get("denominacao_padrao"),
        
        CARVCep=loc.get("cep") or basico.get("cep") or info.get("cep"),
        CARVEnd=endereco_completo,
        
        CARVStatus=basico.get("status") or info.get("status"),
        CARVTipo=basico.get("tipo_cartorio"),
        CARVSituacao=basico.get("situacao_juridica_cartorio") or info.get("situacao_juridica_cartorio"),
        CARVInstalacao=safe_date(basico.get("instalacao")),
        CARVAtribuicoes=basico.get("atribuicoes") or info.get("natureza"),
        
        CARVTelefone=loc.get("telefone") or basico.get("telefone") or info.get("telefone"),
        CARVEmail=loc.get("email") or basico.get("email") or info.get("email"),
        CARVWebsite=loc.get("website") or basico.get("website") or info.get("website"),
        
        CARVResponsavel=responsavel_titular,
        CARVSubstituto=responsavel_substituto,
        
        CARVHorarioFuncionamento=str_horarios
    )
    return c

def save_cartorio(cartorio_obj):
    db = SessionLocal()
    try:
        # db.merge executa a logica de UPDATE OR INSERT automaticamente:
        # Ele tenta buscar o registro com chave primária (CARVCns).
        # Se a chave existir no BD -> Faz UPDATE
        # Se a chave não existir -> Faz INSERT
        db.merge(cartorio_obj)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao salvar CNS {cartorio_obj.CARVCns}: {e}")
    finally:
        db.close()


def main():
    logger.info("Inicializando BD...")
    init_db()
    
    # Sistema de checkpoint baseado em BD (Sênior View):
    logger.info("Verificando checkpoint de CNS já processados no banco de dados...")
    db_session = SessionLocal()
    try:
        # Puxa o CNS e também a cidade para fazermos um "pulo" supersônico
        # Assim criamos um mapa: Cidade_ID -> Quantos cartorios dela já baixamos
        cns_bd = db_session.query(Cartorio.CARVCns, Cartorio.CARVCidadeId).all()
        cns_ja_processados = {c[0] for c in cns_bd}
        
        # Histograma de cartórios por cidade salvos no banco
        cidades_histograma = {}
        for cns, cid_id in cns_bd:
            cidades_histograma[cid_id] = cidades_histograma.get(cid_id, 0) + 1
            
        logger.info(f"Retomando extração: {len(cns_ja_processados)} cartórios já finalizados e salvos no banco.")
    except Exception as e:
        logger.error(f"Não foi possível checar checkpoint no BD. Iniciando verificação padrão. Erro: {e}")
        cns_ja_processados = set()
        cidades_histograma = {}
    finally:
        db_session.close()

    for uf in UFS:
        logger.info(f"Processando UF: {uf}")
        # A lista de cidades desse UF
        cidades = fetch_cidades(uf)
        logger.info(f"Encontradas {len(cidades)} cidades em {uf}")
        
        for cidade in cidades:
            cid_id = cidade.get("id")
            cid_nome = cidade.get("nome")
            qtd_esperada = cidade.get("quantidade_serventias", 0)
            
            # PULO SUPERSÔNICO DE CIDADE INTEIRA EM O(1):
            # Se a API de cidades diz que a cidade tem X serventias, e nós já temos X ou mais 
            # serventias salvas no nosso banco para esse cid_id, nós PULAMOS A CIDADE INTEIRA
            # sem nem mesmo chamar a API paralela de fetch_serventias!
            qtd_no_banco = cidades_histograma.get(cid_id, 0)
            if qtd_esperada > 0 and qtd_no_banco >= qtd_esperada:
                logger.info(f"[PULO RÁPIDO] {cid_nome} ({uf}) ignorada. Todos os {qtd_esperada} cartórios esperados já estão no BD.")
                continue

            logger.info(f"Buscando cartórios ativos em {cid_nome} ({uf}) - Esperado: {qtd_esperada} | No Banco: {qtd_no_banco}")
            
            ativas = fetch_serventias(cid_id, uf, cid_nome)
            if not ativas:
                continue
            
            # Filtro de Checkpoint - Granularidade Nível CNS
            # Só mandamos pra fila de enriquecimento HTTP (e gasto de conexões) os CNS que AINDA NÃO estão no banco.
            ativas_para_processar = [item for item in ativas if item.get("cns") not in cns_ja_processados]
            
            if not ativas_para_processar:
                logger.info(f"[PULADO] Todos os cartórios ativos de {cid_nome} já foram extraídos anteriormente.")
                continue

            logger.info(f"Processando {len(ativas_para_processar)} cartórios RESTANTES de {cid_nome} com ThreadPool...")
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(processa_cartorio, item): item for item in ativas_para_processar}
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        save_cartorio(res)
                        # Atualiza a memória cache do script pro caso da cidade ter cartorios iterados mas internet cair no meio
                        cns_ja_processados.add(res.CARVCns)
                        logger.info(f"Sucesso (Upsert) - CNS: {res.CARVCns} - Nome: {res.CARVNome}")
            
            time.sleep(1)


if __name__ == "__main__":
    main()
