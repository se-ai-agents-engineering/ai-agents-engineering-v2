"""Arquitetura B — workflow determinístico.   (COMPLETE OS TODOs 1 e 2)

O fluxo está escrito no código. O modelo só faz duas tarefas pequenas:
classificar a pergunta e redigir a resposta.

    pergunta ──► classificar ──► tema?
                                   ├── "elegibilidade" ──► escalar (sem chamar o modelo)
                                   └── "rh" | "ti" | "beneficios"
                                          ──► buscar(tema, pergunta) ──► [ modelo + 3 documentos ] ──► resposta

Quem decide o próximo passo é o CÓDIGO, não o modelo.
"""
from comum import modelo
from comum.resultado import Resultado
from ferramentas import buscar, formatar
from politica_de_resposta import FORMATO_JSON, REGRAS

CATEGORIAS = ("rh", "ti", "beneficios", "elegibilidade")


# --------------------------------------------------------------------------
# TODO 1 — o classificador
#
# Escreva o prompt de sistema que faz o modelo responder com UMA das
# CATEGORIAS acima, e nada mais. Dicas:
#   - diga o que entra em cada categoria (ex.: "ti: notebook, senha, VPN...");
#   - "elegibilidade" é quando a pessoa pergunta se ELA tem direito a algo;
#   - peça a resposta em minúsculas, sem pontuação.
# --------------------------------------------------------------------------
PROMPT_CLASSIFICADOR = """Você é um classificador de perguntas de suporte interno da Aurora Tecnologia.
Classifique a pergunta em exatamente UMA das seguintes categorias:

- rh: trabalho remoto, home office, dias presenciais, jornada, banco de horas, férias, licenças (paternidade, maternidade), integração.
- ti: equipamentos (notebook, conserto, danos, tela quebrada), senhas, bloqueio de conta, login, VPN, acesso remoto a sistemas, instalação de software.
- beneficios: plano de saúde, dependentes, auxílio-creche, vale-refeição.
- elegibilidade: quando a pessoa pergunta se ELA PESSOALMENTE tem direito ou é elegível a algo (ex: "tenho direito a...?", "posso ter...?").

Regras:
- Responda APENAS com uma das quatro palavras: rh, ti, beneficios ou elegibilidade.
- Responda sempre em minúsculas, sem pontuação, sem nenhuma explicação."""



def classificar(pergunta: str) -> str:
    resposta = modelo.chamar([modelo.mensagem_do_usuario(pergunta)],
                             sistema=PROMPT_CLASSIFICADOR, max_tokens=10)
    categoria = resposta.texto.strip().lower()

    # TODO 1 (continuação): e se o modelo responder algo fora de CATEGORIAS?
    # Decida um comportamento padrão e devolva sempre uma categoria válida.
    return categoria if categoria in CATEGORIAS else "elegibilidade"


def resolver(pergunta: str) -> Resultado:
    categoria = classificar(pergunta)

    # a) Se a categoria for "elegibilidade", devolva direto sem chamar o modelo
    if categoria == "elegibilidade":
        return Resultado("escalar", [], "Dúvidas sobre elegibilidade a benefícios são analisadas diretamente pelo RH.")

    # b) Senão, busque os documentos do tema
    docs = buscar(categoria, pergunta)
    if not docs:
        return Resultado("nao_sei", [], "Não foram encontrados documentos sobre o tema solicitado.")

    # c) Monte o prompt de sistema com REGRAS, FORMATO_JSON e os documentos, chame o modelo e devolva Resultado.de_json
    documentos = "\n\n".join(formatar(doc) for doc in docs)
    sistema = f"{REGRAS}\n\n{FORMATO_JSON}\n\nDocumentos disponíveis:\n\n{documentos}"

    resposta = modelo.chamar([modelo.mensagem_do_usuario(pergunta)], sistema=sistema)
    return Resultado.de_json(resposta.texto)

