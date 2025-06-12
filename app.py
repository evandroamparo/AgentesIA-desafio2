# Bibliotecas de trabalho

## Importação das NFs

#Importações de bibliotecas
#--------------------------

# Para carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()  # carrega variáveis do arquivo .env

# Para tratar o arquivo ZIP.
import zipfile
import os

# Para ler os arquivos e salvar em banco de dados
import csv
import pandas as pd
import sqlite3
# import psycopg2
# from psycopg2 import Error

# Acesso a área Secrets
# from google.colab import userdata

# Acesso ao LLM

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache

# ativa o cache para melhorar a performance
set_llm_cache(InMemoryCache())


# Para criar a interface web
import streamlit as st
from langchain_openai import OpenAI

# Definição do repositório e arquivo.

# TODO: Alterar a origem de dados quando em produção.
nome_diretorio = './'
nomeArqZip= nome_diretorio + '202401_NFs.zip'

arquivo_banco_dados = "notas.db"

nome_arq_csv_cabecalho = nome_diretorio + '202401_NFs_Cabecalho.csv'
nome_arq_csv_itens = nome_diretorio + '202401_NFs_Itens.csv'

# Verifica se o arquivo ZIP existe
if not os.path.exists(nomeArqZip):
    print(f"Erro: O arquivo ZIP '{nomeArqZip}' não foi encontrado.")

def extrair_zip(caminho_zip, diretorio_destino):
    """
    Extrai todos os arquivos de um arquivo ZIP para um diretório especificado.

    Args:
        caminho_zip (str): O caminho completo para o arquivo ZIP.
        diretorio_destino (str): O diretório onde os arquivos serão extraídos.
    """
    if not os.path.exists(caminho_zip):
        print(f"Erro: O arquivo ZIP '{caminho_zip}' não foi encontrado.")
        return

    if not os.path.exists(diretorio_destino):
        os.makedirs(diretorio_destino)
        print(f"Diretório de destino '{diretorio_destino}' criado.")

    try:
        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            zip_ref.extractall(diretorio_destino)
        print(f"Arquivos extraídos com sucesso. \n Destino: '{diretorio_destino}'\n Origem: '{caminho_zip}'.")
    except zipfile.BadZipFile:
        print(f"Erro: O arquivo '{caminho_zip}' não é um arquivo ZIP válido ou está corrompido.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Execução da extração do arquivo ZIP.
extrair_zip(nomeArqZip, nome_diretorio)

# Função para converter CSV em banco de dados SQLite
def csv_para_sqlite(nome_csv, conexao, tabela):
    """
    Converte um arquivo CSV em uma tabela SQLite.

    Args:
        nome_csv (str): O caminho do arquivo CSV.
        conexao (sqlite3.Connection): A conexão com o banco de dados SQLite.
        tabela (str): O nome da tabela onde os dados serão inseridos.
    """
    try:
        df = pd.read_csv(nome_csv)
        df.to_sql(tabela, conexao, if_exists='replace', index=False, )
        print(f"Dados do arquivo '{nome_csv}' inseridos na tabela '{tabela}' com sucesso.")
    except Exception as e:
        print(f"Erro ao inserir dados do arquivo '{nome_csv}' na tabela '{tabela}': {e}")

# Carrega os arquivos
cabecalho = pd.read_csv(nome_arq_csv_cabecalho)
itens = pd.read_csv(nome_arq_csv_itens)

# Cria banco SQLite
conexaoBd = sqlite3.connect(arquivo_banco_dados)

csv_para_sqlite(nome_arq_csv_cabecalho, conexaoBd, "notas_fiscais")
csv_para_sqlite(nome_arq_csv_itens, conexaoBd, "itens")

conexaoBd.commit()
conexaoBd.close()
print("Banco de dados criado com sucesso!")

# Configuração do agente SQL com LangChain

# For SQLite, the database URI is simply the path to the database file.
# We'll use the variable 'arquivo_banco_dados' which is already defined as "notas.db"
database_uri = f"sqlite:///{arquivo_banco_dados}"

api_key = os.environ.get('OPENAI_API_KEY')
# api_key = os.environ.get('OPENROUTER_API_KEY')
# api_key = os.environ.get('GROQ_API_KEY')
model_name = "gpt-4o-mini"
base_url = "https://api.openai.com/v1" # não necessário para OpenAI, mas pode ser útil para outros provedores.

if not api_key:
    raise ValueError("A chave de API do OpenAI não foi encontrada. Por favor, defina a variável de ambiente 'OPENAI_API_KEY'.")

# Conectar ao banco de dados usando a URI que criamos
# For SQLite, we don't need the psycopg2 driver part in the SQLDatabase.from_uri call.
db = SQLDatabase.from_uri(database_uri)

# Inicializar o LLM da OpenAI
llm = ChatOpenAI(
    api_key=api_key,
    model=model_name,
    temperature=0,
    verbose=True,
    base_url=base_url,
    cache=True  # o cache deve estar configurado com set_llm_cache
)

# Criar o agente SQL
agente = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

# pergunta1 = "Quais são as 3 empresas de maior faturamento?"

# # Executar as perguntas e obter as respostas
# resposta1 = agente.invoke(pergunta1)
# print(f"Pergunta: {pergunta1}")
# print(f"Resposta: {resposta1['output']}")

# pergunta1 = "Quais são os 3 produtos mais vendidos?"

# # Executar as perguntas e obter as respostas
# resposta1 = agente.invoke(pergunta1)
# print(f"Pergunta: {pergunta1}")
# print(f"Resposta: {resposta1['output']}")

# pergunta1 = "Quais são os 3 produtos mais vendidos e quais foram as empresas que os venderam?"

# # Executar as perguntas e obter as respostas
# resposta1 = agente.invoke(pergunta1)
# print(f"Pergunta: {pergunta1}")
# print(f"Resposta: {resposta1['output']}")

# # Resposta errada.

# pergunta1 = "Com base nos 3 produtos de maior quantidade vendidas, quais foram as empresas que os venderam?"

# # Executar as perguntas e obter as respostas
# resposta1 = agente.invoke(pergunta1)
# print(f"Pergunta: {pergunta1}")
# print(f"Resposta: {resposta1['output']}")

# Configuração do Streamlit para criar uma interface web simples
st.set_page_config(page_title="Agente de Consulta de Notas Fiscais")
st.title("Agente de Consulta de Notas Fiscais")
st.write("### Pergunte algo sobre os dados das notas fiscais e o agente responderá.")

'''
💡 Exemplos de perguntas:

Qual o valor total das notas fiscais emitidas em janeiro de 2024?

Quais foram os 5 fornecedores que mais emitiram notas fiscais em valor total?

Qual a média de itens por nota fiscal?

Quais produtos tiveram maior volume vendido (em quantidade)?

Qual é o ticket médio (valor médio por nota fiscal)?

Qual o total de notas fiscais emitidas por cada CNPJ fornecedor?

Quantas notas fiscais foram emitidas por dia ao longo de janeiro?

Quais foram os 10 produtos mais vendidos em valor total (preço × quantidade)?

Qual o valor total de notas fiscais emitidas por tipo de operação (ex: entrada, saída)?

Quais notas fiscais tiveram mais de 3 itens diferentes?
'''

pergunta = st.text_input("Faça sua pergunta:")

if pergunta:
    st.write("Processando sua pergunta...")
    try:
        response = agente.invoke(f"Responda em portugues: {pergunta}")
        st.write("Resposta:")
        st.write(response['output'])
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar sua pergunta: {e}")
