import os
import pandas as pd
from io import StringIO
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI

# Configure OpenAI API key
openai_api_key = "sk-proj-nGphcyAtAeWW0RIXF3VFT3BlbkFJo7uOiTu5GT57lch8Lt2E"

# Função para carregar o arquivo CSV
@st.cache_data
def load_csv(file_path):
    return pd.read_csv(file_path)

# Carrega o arquivo CSV
file_path = 'C:/Users/alexc/multmodal_agent/relacionamentos_jn/relacionamentos.csv'
df = load_csv(file_path)

# Define o modelo de linguagem e o template de prompt para verificar o conteúdo
check_content_prompt = PromptTemplate(
    input_variables=["content_data", "question"],
    template="""
Você é um especialista educacional que conhece a BNCC brasileira. Você receberá uma lista de conteúdos das disciplinas, separados por ano escolar, juntamente com os conteúdos prévios necessários para cada título. Sua tarefa é verificar se os conteúdos listados estão corretos, se há mais conteúdos a serem considerados que não estão listados, sugerir melhorias e reorganizações na lista, tudo baseado na BNCC brasileira.

Aqui está a lista de conteúdos:

{content_data}

{question}

Instruções:
1. Verifique se os conteúdos listados estão corretos e em conformidade com a BNCC.
2. Adicione conteúdos adicionais importantes para o ano escolar que deveriam estar presentes, mas estão faltando.
3. Recomende reorganizações na lista, quando necessárias.
4. A coluna 'titulo_anterior' se refere a aprendizagens anteriores consideradas essenciais para o domínio dos conteúdos da coluna 'título'. 
   Verifique se ela está correta e adequada, ou seja, faltam conteúdos prévios importantes e que não estão no documento.
5. Se há conteúdos faltantes importantes na coluna 'titulo_anterior', busque conteúdos presentes na lista e que são importantes para o domínio do conhecimento referido na coluna 'titulo' da respectiva habilidade e adicione no novo documento.
6. Como resultado das análises dos itens 5 e 6, produza um novo documento contendo todas as sugestões de conhecimentos prévios a serem inseridos na coluna 'titulo_anterior', referentes aos conteúdos presente na coluna 'título' e que não estão contemplados no documento.
7. Os conteúdos da coluna 'titulo_anterior' são essenciais para manter o fluxo de aprendizagem dos alunos. Eles representam os conhecimentos prévios exigidos para cada conhecimento representado em 'título'. Analise com base na BNCC brasileira e faça todas as sugestões de adição de novos conteúdos para a coluna 'titulo_anterior'.
8. Você deve se ater apenas aos conteúdos presentes no documento para realizar as sugestões de alteração.
9. Ao analisar um conteúdo de matemática, busque todos os conteúdos de matemática do documento, de todos os anos, e analise se há conteúdos que deveriam estar na coluna 'titulo_anterior' mas não estão. O critério é o seguinte: há conhecimentos prévios para os alunos que são importantes, estão presentes na lista, mas não fazem parte deste conhecimento.
10. A sua resposta deve ser um documento tal qual {content_data}, contendo apenas a sua resposta para a {question} com as mesmas colunas, sendo que a coluna 'titulo_anterior' deve ser editada, com os acréscimos de conteúdo que você sugere.
11. Esta análise deve ser feita passo a passo, em todo o documento.
12. Se a resposta for sim, acrescente este conteúdo na coluna 'titulo_anterior' e adicione uma linha no documento de saída,
contendo 'titulo', 'disciplina, 'ano', 'titulo_anterior'
13. A sua resposta deve ser um documento tal qual {content_data}, contendo apenas a sua resposta para a {question} com as mesmas colunas, sendo que a coluna'titulo_anterior' deve
ser editada, com os acréscimos de conteúdo que você sugere, conforme instrução 12.
14. Responda apenas o que for perguntado. 

"""
)

# Inicializa o modelo de linguagem com a chave API e define a cadeia de prompts
llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4-1106-preview", temperature=0.3)
check_content_chain = LLMChain(llm=llm, prompt=check_content_prompt)

# Função para verificar se a resposta é um CSV válido
def is_valid_csv(data: str) -> bool:
    try:
        pd.read_csv(StringIO(data))
        return True
    except pd.errors.ParserError:
        return False
    except Exception as e:
        st.error(f"Erro ao verificar CSV: {e}")
        return False

# Função para depurar a resposta do modelo
def debug_response(response: str, debug_dir: str):
    debug_file_path = os.path.join(debug_dir, 'response_debug.txt')
    with open(debug_file_path, 'w', encoding='utf-8') as f:
        f.write(response)
    st.info(f"Resposta do modelo salva para inspeção em {debug_file_path}.")

# Configura a interface Streamlit
st.title("Análise de Conteúdos Educacionais")
disciplina = st.selectbox("Selecione a disciplina:", df['disciplina'].unique())
ano = st.selectbox("Selecione o ano escolar:", df['ano'].unique())
output_dir = st.text_input("Diretório de saída:", "C:/Users/alexc/multmodal_agent/relacionamentos_jn/")

if st.button("Analisar e Salvar"):
    # Filtra os dados com base na disciplina e ano
    df_filtered = df[(df['disciplina'] == disciplina) & (df['ano'] == ano)]

    # Converte os dados filtrados para uma string CSV
    content_data = df_filtered[['titulo', 'disciplina', 'ano', 'titulo_anterior']].to_csv(index=False)

    # Define a pergunta para o modelo
    question = f"Quais conteúdos adicionais de {disciplina} do {ano} deveriam ser incluídos? Os conhecimentos da coluna titulo_anterior estão adequados?"

    # Prepara a entrada do prompt
    prompt_input = {"content_data": content_data, "question": question}

    # Executa a cadeia de prompts para análise
    response = check_content_chain.run(prompt_input)

    if is_valid_csv(response):
        # Converte a resposta em um DataFrame
        response_data = pd.read_csv(StringIO(response))

        # Salva o DataFrame como um novo arquivo CSV
        output_file_path_csv = os.path.join(output_dir, f'{disciplina}_{ano}.csv')
        response_data.to_csv(output_file_path_csv, index=False)

        # Salva o DataFrame como um novo arquivo Excel
        output_file_path_excel = os.path.join(output_dir, f'{disciplina}_{ano}.xlsx')
        response_data.to_excel(output_file_path_excel, index=False)

        st.success(f"Arquivos atualizados salvos com sucesso em {output_file_path_csv} e {output_file_path_excel}.")
    else:
        st.error("A resposta do modelo não é um CSV válido.")
        debug_response(response, output_dir)
