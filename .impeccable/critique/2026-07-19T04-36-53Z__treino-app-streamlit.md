---
target: treino_app (Streamlit) — geral
total_score: 28
p0_count: 0
p1_count: 3
timestamp: 2026-07-19T04-36-53Z
slug: treino-app-streamlit
---
# Crítica — Treino Hub (Streamlit)

Método: DEGRADED single-context (alvo Streamlit/Python; detector web-only N/A). Revisão com app rodando em viewport mobile + leitura de todo o código.

## Score: 28/40 (Bom)
Fraquezas em Estético/Minimalista (2) e Recuperação de erro (2).

## Anti-patterns (product-slop)
- st.metric delta usado como status: "↑ Normal", "↑ Boa" (seta = aumento, leitura errada).
- Status duplicado: badge de delta + 🟢 em linha separada.

## Priority Issues
- [P1] Métricas empilham no mobile (st.columns 4/3 -> 1 col), números gigantes sozinhos, muito vazio. Causa do "parece vazia". Fix: bloco compacto flex 2-up ou cartão de estado denso. -> /impeccable layout
- [P1] Contradição: banner "Bom para treinar hoje" vs caption "Ainda sem dados de hoje" (usa dado de ontem mas diz hoje). Fix: rotular "Com base em DD/MM". -> /impeccable clarify
- [P1] delta como status ("↑ Normal"/"↑ Boa") + 🟢 duplicado. Fix: um sinal só, inline. -> /impeccable distill
- [P2] Erro = traceback cru (st.code). Fix: mensagem amigável + expander. -> /impeccable harden
- [P2] Botão 🔄 repetido no topo de cada aba. -> /impeccable layout

## Persona red flags
- Casey (mobile): rola 3-4 telas na Saúde; Passos/Calorias "—" ocupam tela cheia.
- Alex (decisão): "treino hoje?" fragmentado em 3 abas depois de remover Dashboard.
- Sam (a11y): status por cor+emoji; emoji com significado não lido por leitor de tela.

## Minor
- Emoji conduz toda hierarquia; caption cinza no limite de contraste; ícone de âncora do Streamlit no título.

## What's working
- Sessão de treino ativa (timer descanso auto, wake lock, autosave anti-crash, dica última vez, progressão) = craft real.
- Prevenção de erro (conflito 72h, autosave). Modelagem de periodização A-E.
