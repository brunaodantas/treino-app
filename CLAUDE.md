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
- Usuário pode selecionar qualquer treino (A–E) a qualquer dia da semana
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
