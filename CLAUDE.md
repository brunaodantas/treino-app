# Treino Hub — Notas de Implementação

App Streamlit de treino pessoal. Deploy em https://treino-bruno.streamlit.app
Repositório: https://github.com/brunaodantas/treino-app

## Stack
- Python 3.11, Streamlit >= 1.35
- streamlit-javascript para leitura de localStorage
- Plotly para gráficos
- Strava API OAuth 2.0

## Estrutura
- `app.py` — entry point, state bootstrap, tabs, OAuth callback
- `views/musculacao.py` — sessão de treino com timer global, timer de descanso, wake lock, auto-save
- `views/corrida.py` — histórico de corridas + progressão
- `views/dashboard.py` — status do dia (informativo, sem bloqueio por dia)
- `views/analytics.py` — gráficos de volume e steps
- `logic/` — schedule, running, adaptation
- `views/theme.py` — tema glassmorphism (dark deep + laranja), injetado uma vez no app.py

## Programa de musculação (desde 25/07/2026)

Ciclo fixo de 3 treinos de **corpo inteiro** (`"1"`, `"2"`, `"3"`), Ter/Qua/Sáb.
Substituiu o split A/B/C/D/E, que a 3 sessões por semana treinava cada grupo
0,75x/semana. Agora cada músculo é treinado 3x/semana.

- Superséries de antagonistas: cada exercício tem `ss`, `ss_pos`, `par` e `rest`.
  Primeiro do par descansa 20s (só trocar de aparelho); segundo descansa o valor
  do par (`REST_PAIR_2`: SS1 90s · SS2 75s · SS3 60s · SS4 75s · CORE 45s).
- Ao marcar a **última série** de um exercício, o descanso é atribuído ao
  **próximo** exercício (`_ex_rest_ts` / `_ex_rest_dur`), senão o timer morria
  junto com o card que colapsa.
- `check_72h_conflict` não aplica a regra de 72h por grupo a treinos de corpo
  inteiro — a sobreposição é intencional. Alerta só se a mesma sessão repetir
  em menos de 20h.
- `LEGACY_LABELS` + `label_for()` existem só para o histórico: `workout_log` tem
  registros antigos com letras A–E. Nunca indexar `WORKOUT_LABELS[...]` ou
  `EXERCISES[...]` com valor vindo do histórico.
- `_reps_num()` / `_reps_max()` extraem números do campo `reps`, que aceita
  `"10-12"`, `"8"` e `"40s"` (Prancha). `int("40s")` derrubava a aba inteira.
- `parsers/strava_api.py` — OAuth + create_activity
- `data/` — strava_cache.json (781 atividades) e health_cache.json (Apple Health)

## Persistência de Estado
- `st.session_state.app_state` — estado em memória durante a sessão
- `state.json` — arquivo local (fallback)
- `localStorage` do navegador — escrito a cada `save_state()` via `components.html`;
  lido na inicialização via `st_javascript`. Sobrevive a restartes do servidor.

## Features implementadas

### Timer global de sessão (views/musculacao.py)
- Componente HTML `_make_global_timer(started_at)` exibido no header da sessão
- Mostra tempo decorrido desde o início do treino em formato MM:SS
- Atualiza a cada segundo via `setInterval` no JavaScript do iframe

### Timer de descanso com auto-disparo (views/musculacao.py)
- `_make_rest_timer(remaining, is_running)` gera HTML com estado inicial injetado
- Ao marcar uma série como feita (○ → ✅), salva `_rest_ts = time.time()` no session_state
- No próximo render, Python calcula `remaining = 60 - elapsed` e passa ao timer HTML
- Timer inicia automaticamente com 1 min; também permite escolha manual de 30s/45s/1min/1:30/1:45/2min
- Beep via Web Audio API + notificação push ao zerar
- Resets e rerenders preservam o tempo restante correto

### Auto-save contra crash (views/musculacao.py)
- `_save_active_workout()` persiste `active_workout` em `app_state["_active_workout"]`
- Chamado em: início de sessão, toggle de série feita, finalização
- `render_musculacao()` restaura o treino do backup se `active_workout` não estiver em session_state

### Tela sempre ligada — Wake Lock (views/musculacao.py)
- `_WAKELOCK_ON` / `_WAKELOCK_OFF`: snippets HTML que acessam `window.parent.navigator.wakeLock`
- Ativado ao entrar na sessão, desativado ao sair ou finalizar
- Best-effort: falha silenciosamente em browsers sem suporte

### Dashboard sem travamento por dia (views/dashboard.py)
- Removido o early return que bloqueava acesso em dias de descanso
- Dias de descanso e corrida aparecem como **informativos** (st.info), não como bloqueios
- Usuário pode selecionar qualquer treino do ciclo (1/2/3) a qualquer dia da semana
- "Próximo na fila" é sugestão, não obrigação

### Strava — correção do escopo OAuth (parsers/strava_api.py)
- **Bug identificado**: `SCOPE = "activity:read_all"` não incluía permissão de escrita
- **Correção**: `SCOPE = "activity:read_all,activity:write"` 
- **Ação necessária**: Usuário precisa desconectar e reconectar o Strava na aba ⚙️ para que o novo escopo seja autorizado
- Após reconexão, `POST /api/v3/activities` funciona e salva treinos no Strava ao finalizar

### Salvamento no Strava ao finalizar treino
- Posta atividade `WeightTraining` via `POST /api/v3/activities`
- Inclui nome do treino, grupos musculares e volume total na descrição
- Exibe erro específico da API no toast se falhar (em vez de mensagem genérica)
