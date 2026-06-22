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
- `views/musculacao.py` — sessão de treino com timer, wake lock, auto-save
- `views/corrida.py` — histórico de corridas + progressão
- `views/dashboard.py` — status do dia + fila A→B→C→D
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

### Timer de descanso entre séries (views/musculacao.py)
- Componente HTML puro (`_TIMER_HTML`) embutido na sessão de treino
- Opções: 30s · 45s · 1min · 1:30 · 1:45 · 2min
- Beep via Web Audio API ao zerar
- Notificação push via Notifications API (pede permissão ao abrir)

### Auto-save contra crash (views/musculacao.py)
- `_save_active_workout()` persiste `active_workout` em `app_state["_active_workout"]`
- Chamado em: início de sessão, toggle de série feita, finalização
- `render_musculacao()` restaura o treino do backup se `active_workout` não estiver em session_state

### Tela sempre ligada — Wake Lock (views/musculacao.py)
- `_WAKELOCK_ON` / `_WAKELOCK_OFF`: snippets HTML que acessam `window.parent.navigator.wakeLock`
- Ativado ao entrar na sessão de treino, desativado ao sair ou finalizar
- Best-effort: falha silenciosamente em browsers sem suporte (iOS < 16.4 fora de PWA)

### Salvamento no Strava ao finalizar treino
- Posta atividade `WeightTraining` via `POST /api/v3/activities`
- Inclui nome do treino, grupos musculares e volume total na descrição

## Regras de alcance/segurança
- Sem sidebar: conteúdo de configuração na aba ⚙️
- CSS esconde header/footer do Streamlit (hambúrguer também some — por isso sidebar removida)
- Secrets Strava ficam no Streamlit Cloud Settings (não no código)
