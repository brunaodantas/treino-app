import time
import streamlit as st
import streamlit.components.v1 as _components
from datetime import datetime
from logic.schedule import (
    EXERCISES, WORKOUT_LABELS, MUSCLE_GROUPS, check_72h_conflict,
    get_scheduled_workout, get_next_workout, mark_workout_done, WORKOUT_SEQUENCE,
)
from logic.adaptation import (
    get_current_phase, is_adaptation_phase, get_workouts_in_current_week,
    ADAPTATION_MESSAGE, WORKOUTS_PER_WEEK,
)
from logic.running import get_day_label
from utils import now_br

MUSCLE_EMOJI = {
    "peito": "🫁", "ombro_lat": "💪", "triceps": "💪",
    "costas": "🔙", "ombro_post": "💪", "biceps": "💪",
    "pernas": "🦵", "ombro_full": "💪", "trapezio": "🏔️",
}

WORKOUT_DESC = {
    "A": "Peito · Ombro Lateral · Tríceps",
    "B": "Costas · Ombro Post. · Bíceps",
    "C": "Pernas",
    "D": "Peito · Costas · Braços",
    "E": "Ombros · Trapézio · Braços",
}

# ── Timer templates (plain strings — JS braces unescaped) ──────────────────────

_GLOBAL_TIMER_TPL = """
<style>
  body{background:transparent;margin:0;padding:0;font-family:-apple-system,sans-serif;}
  .gt{text-align:center;color:#888;font-size:13px;padding:4px 0;}
  .gt b{color:#FAFAFA;font-size:1.15rem;font-variant-numeric:tabular-nums;letter-spacing:1px;}
</style>
<div class="gt">⏱ Treino em andamento &nbsp;—&nbsp; <b id="t">LABEL_DEFAULT</b></div>
<script>
const SA = "STARTED_AT";
if (SA) {
  const S = new Date(SA).getTime();
  function tick(){
    const e=Math.max(0,Math.floor((Date.now()-S)/1000)),m=Math.floor(e/60),s=e%60;
    document.getElementById('t').textContent=m.toString().padStart(2,'0')+':'+s.toString().padStart(2,'0');
  }
  tick(); setInterval(tick,1000);
}
</script>
"""

_REST_TIMER_TPL = """
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:transparent;font-family:-apple-system,sans-serif;padding:2px 0}
  .lbl{color:#aaa;font-size:12px;font-weight:500;margin-bottom:6px;letter-spacing:.5px}
  .presets{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
  .pb{background:#1E3A5F;border:1.5px solid #4A90D9;color:#DDD;padding:7px 10px;
      border-radius:8px;cursor:pointer;font-size:13px;transition:background .15s}
  .pb.sel{background:#4A90D9;color:#fff;border-color:#4A90D9}
  .disp{font-size:2.6rem;font-weight:700;text-align:center;letter-spacing:3px;padding:8px 0;color:#FAFAFA}
  .disp.run{color:#4CAF50}
  .disp.done{color:#FF6B35}
  .ctrls{display:flex;gap:8px;margin-top:6px}
  .cb{flex:1;padding:11px;border-radius:10px;border:none;cursor:pointer;font-size:14px;font-weight:600}
  .go{background:#4CAF50;color:#fff}
  .go:disabled{background:#444;color:#888;cursor:default}
  .rst{background:#333;color:#bbb}
</style>
<div class="lbl">⏱ DESCANSO ENTRE SÉRIES</div>
<div class="presets" id="pre"></div>
<div class="disp" id="disp">--:--</div>
<div class="ctrls">
  <button class="cb go" id="goBtn" onclick="tog()" disabled>▶ Iniciar</button>
  <button class="cb rst" onclick="rst()">↺</button>
</div>
<script>
const OPTS=[{l:'30s',s:30},{l:'45s',s:45},{l:'1 min',s:60},{l:'1:30',s:90},{l:'1:45',s:105},{l:'2 min',s:120}];
let tot=0,rem=0,tid=null,run=false,selB=null,_ac=null;

if(Notification&&Notification.permission==='default')Notification.requestPermission();

// Desbloqueia AudioContext no primeiro toque (exigido pelo iOS)
document.addEventListener('touchstart',function unlock(){
  if(!_ac){try{_ac=new AudioContext();}catch(e){}}
  if(_ac&&_ac.state==='suspended')_ac.resume();
},{once:true});

const pEl=document.getElementById('pre');
OPTS.forEach(o=>{
  const b=document.createElement('button');
  b.className='pb';b.textContent=o.l;b.onclick=()=>pick(o.s,b);pEl.appendChild(b);
});

function pick(s,btn){
  clearInterval(tid);run=false;tot=rem=s;
  if(selB)selB.classList.remove('sel');
  selB=btn;if(btn)btn.classList.add('sel');
  render();document.getElementById('goBtn').disabled=false;
  document.getElementById('goBtn').textContent='▶ Iniciar';
}

function fmt(s){return Math.floor(s/60)+':'+(s%60).toString().padStart(2,'0');}

function render(){
  const d=document.getElementById('disp');
  if(rem>0){d.textContent=fmt(rem);d.className='disp'+(run?' run':'');}
  else{d.textContent='✓ Vai!';d.className='disp done';}
}

function tog(){
  if(!tot)return;
  if(run){clearInterval(tid);run=false;document.getElementById('goBtn').textContent='▶ Continuar';}
  else{
    if(rem<=0)rem=tot;
    run=true;document.getElementById('goBtn').textContent='⏸ Pausar';
    tid=setInterval(()=>{rem--;render();if(rem<=0){clearInterval(tid);run=false;document.getElementById('goBtn').textContent='▶ Iniciar';beep();flashDone();vibrate();notif();}},1000);
  }
  render();
}

function rst(){clearInterval(tid);run=false;rem=tot;render();document.getElementById('goBtn').textContent='▶ Iniciar';document.getElementById('goBtn').disabled=!tot;}

function beep(){
  try{
    if(!_ac)_ac=new AudioContext();
    function play(){
      const o=_ac.createOscillator(),g=_ac.createGain();
      o.connect(g);g.connect(_ac.destination);
      o.frequency.value=880;g.gain.value=0.4;
      o.start();g.gain.exponentialRampToValueAtTime(0.001,_ac.currentTime+0.8);
      o.stop(_ac.currentTime+0.8);
    }
    if(_ac.state==='suspended')_ac.resume().then(play);else play();
  }catch(e){}
}
function flashDone(){
  const d=document.getElementById('disp');let n=0;
  const iv=setInterval(()=>{d.style.color=n%2===0?'#FF6B35':'#FAFAFA';n++;if(n>=8){clearInterval(iv);d.style.color='';}},250);
}
function vibrate(){try{navigator.vibrate&&navigator.vibrate([200,100,200]);}catch(e){}}
function notif(){if(Notification&&Notification.permission==='granted'){try{new Notification('Treino Hub 🏋️',{body:'Descanso terminado! Próxima série.'});}catch(e){}}}

// Auto-start injected by Python
AUTOSTART_BLOCK
</script>
"""

_WAKELOCK_ON = """<script>
(function(){const p=(()=>{try{return window.parent;}catch(e){return window;}})();
const nav=(p||window).navigator;if(nav&&'wakeLock'in nav){
nav.wakeLock.request('screen').then(l=>{(p||window)._twl=l;l.addEventListener('release',()=>{(p||window)._twl=null;});}).catch(()=>{});}})();
</script>"""

_WAKELOCK_OFF = """<script>
(function(){const p=(()=>{try{return window.parent;}catch(e){return window;}})();
const w=p||window;if(w._twl){w._twl.release();w._twl=null;}})();
</script>"""


def _make_global_timer(started_at: str) -> str:
    label = "00:00" if not started_at else "00:00"
    waiting = "aguardando 1ª série..." if not started_at else "00:00"
    return (
        _GLOBAL_TIMER_TPL
        .replace("STARTED_AT", started_at or "")
        .replace("LABEL_DEFAULT", "aguardando 1ª série..." if not started_at else "00:00")
    )


def _make_rest_timer(remaining: int = 0, is_running: bool = False) -> str:
    if is_running and remaining > 0:
        autostart = (
            f"rem={remaining};tot={remaining};run=true;"
            "document.getElementById('goBtn').disabled=false;"
            "document.getElementById('goBtn').textContent='⏸ Pausar';"
            "render();"
            "tid=setInterval(()=>{rem--;render();if(rem<=0){"
            "clearInterval(tid);run=false;"
            "document.getElementById('goBtn').textContent='▶ Iniciar';"
            "beep();flashDone();vibrate();notif();}},1000);"
        )
    else:
        autostart = ""
    return _REST_TIMER_TPL.replace("AUTOSTART_BLOCK", autostart)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_last_sets(exercise_name: str, state: dict) -> list:
    for session in state.get("workout_history", []):
        sets = session.get("sets", {}).get(exercise_name, [])
        if sets:
            return sets
    return []


def _save_active_workout(state: dict, save_fn):
    if st.session_state.get("active_workout"):
        state["_active_workout"] = st.session_state.active_workout
    else:
        state.pop("_active_workout", None)
    save_fn(state)


def _init_session(workout: str, state: dict, save_fn):
    sets = {}
    for ex in EXERCISES[workout]:
        name = ex["nome"]
        last = _get_last_sets(name, state)
        default_w = float(ex.get("peso_atual", 0))
        default_r = int(ex.get("reps", "10").split("-")[0])
        ex_sets = []
        for i in range(ex["series"]):
            if last and i < len(last):
                w = float(last[i].get("weight", default_w))
                r = int(last[i].get("reps", default_r))
            else:
                w, r = default_w, default_r
            ex_sets.append({"weight": w, "reps": r, "done": False})
            st.session_state[f"w_{name}_{i}"] = w
            st.session_state[f"r_{name}_{i}"] = r
        sets[name] = ex_sets

    st.session_state.active_workout = {
        "workout": workout,
        "started_at": now_br().isoformat(),
        "first_set_ts": None,
        "sets": sets,
    }
    st.session_state._rest_ts = 0.0
    st.session_state._ex_rest_ts = {}
    _save_active_workout(state, save_fn)


def _finish_workout(state: dict, save_fn):
    from parsers.strava_api import is_connected, get_valid_token, create_activity

    session = st.session_state.active_workout
    workout = session["workout"]
    now = now_br()
    started_at = session.get("started_at", now.isoformat())

    volume = sum(
        s["weight"] * s["reps"]
        for sets in session["sets"].values()
        for s in sets
        if s["done"]
    )

    try:
        elapsed = int((now - datetime.fromisoformat(started_at)).total_seconds())
    except Exception:
        elapsed = 3600

    entry = {
        "date": str(now.date()),
        "workout": workout,
        "completed_at": now.isoformat(),
        "sets": session["sets"],
        "volume_total": round(volume, 1),
    }
    history = state.get("workout_history", [])
    history.insert(0, entry)
    state["workout_history"] = history[:60]

    log_entry = {
        "date": entry["date"],
        "workout": workout,
        "completed_at": entry["completed_at"],
    }
    state["workout_log"] = [log_entry] + state.get("workout_log", [])

    if workout != "E":
        state["current_index"] = (state["current_index"] + 1) % 4

    st.session_state.active_workout = None
    st.session_state._rest_ts = 0.0
    state.pop("_active_workout", None)
    st.session_state._wakelock_active = False
    save_fn(state)

    st.success(f"✅ Treino {workout} finalizado! Volume: {volume:,.0f} kg")
    _components.html(_WAKELOCK_OFF, height=0)

    if is_connected(state):
        token = get_valid_token(state, save_fn)
        if token:
            elapsed_min = elapsed // 60
            lines = [
                f"Treino {workout} — {WORKOUT_DESC[workout]}",
                f"Duração: {elapsed_min}min | Volume: {volume:,.0f} kg",
                "",
            ]
            for ex_name, ex_sets in session["sets"].items():
                done_sets = [s for s in ex_sets if s["done"]]
                if not done_sets:
                    continue
                lines.append(ex_name)
                for i, s in enumerate(done_sets, 1):
                    w = s["weight"]
                    r = s["reps"]
                    w_str = f"{w:g}" if w else "—"
                    lines.append(f"  Série {i}: {w_str} kg × {r}")
                lines.append("")
            desc = "\n".join(lines).rstrip()
            result = create_activity(
                token=token,
                name=f"Treino {workout} — Treino Hub",
                sport_type="WeightTraining",
                start_date_local=started_at[:19],
                elapsed_time=max(elapsed, 60),
                description=desc,
            )
            if result.get("id"):
                st.toast("🟠 Salvo no Strava!", icon="✅")
            else:
                st.toast(f"Strava: erro {result.get('message','desconhecido')}", icon="⚠️")


def render_musculacao(state: dict, hevy_df, save_fn):
    if "active_workout" not in st.session_state:
        st.session_state.active_workout = state.get("_active_workout", None)
    if "_rest_ts" not in st.session_state:
        st.session_state._rest_ts = 0.0
    if "_last_ex" not in st.session_state:
        st.session_state._last_ex = ""
    if "_ex_rest_ts" not in st.session_state:
        st.session_state._ex_rest_ts = {}

    if st.session_state.active_workout is None:
        _render_picker(state, save_fn)
    else:
        _render_session(state, save_fn)


# ── Tela de escolha de treino ──────────────────────────────────────────────────

def _render_picker(state: dict, save_fn):
    if st.session_state.get("_wakelock_active"):
        _components.html(_WAKELOCK_OFF, height=0)
        st.session_state._wakelock_active = False

    from datetime import date
    today = date.today()

    # ── Cabeçalho: data + treino programado ─────────────────────────────────────
    col_t, col_r = st.columns([5, 1])
    with col_t:
        st.markdown(f"### 🏋️ Musculação — {today.strftime('%d/%m')} ({get_day_label(today)})")
    with col_r:
        if st.button("🔄", help="Recarregar", key="refresh_musc"):
            _components.html("<script>window.parent.location.reload();</script>", height=0)

    today_workout = get_scheduled_workout(state)
    if today_workout:
        st.info(f"📌 Programado para hoje: **{WORKOUT_LABELS.get(today_workout, today_workout)}**")

    # ── Periodização ────────────────────────────────────────────────────────────
    phase = get_current_phase(state)
    week = phase["semana_global"]
    phase_week = phase["semana_na_fase"]
    phase_start, phase_end = phase["semanas"]
    phase_duration = phase_end - phase_start + 1

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{phase['nome']} — Semana {phase_week} de {phase_duration}** (semana {week} no total)")
        st.progress(min(phase_week / phase_duration, 1.0))
        st.caption(phase["descricao"])
        if is_adaptation_phase(state):
            done_in_week = get_workouts_in_current_week(state)
            st.caption(f"{done_in_week}/{WORKOUTS_PER_WEEK} treinos desta semana")
    with col2:
        week_override = st.number_input(
            "Ajustar semana", min_value=1, max_value=20,
            value=week, step=1, key="week_override",
            help="Ajuste manual da semana de periodização",
        )
        if week_override != week:
            state["adaptation_week_override"] = week_override
            save_fn(state)
            st.rerun()
    if is_adaptation_phase(state):
        st.warning(ADAPTATION_MESSAGE)

    st.markdown("---")
    st.markdown("### Qual treino hoje?")

    rows = [["A", "B"], ["C", "D"], ["E"]]
    for row in rows:
        cols = st.columns(len(row))
        for col, letter in zip(cols, row):
            with col:
                is_today = (letter == today_workout)
                btn = st.button(
                    f"**{letter}** — {WORKOUT_DESC[letter]}",
                    key=f"pick_{letter}",
                    use_container_width=True,
                    type="primary" if (is_today or not today_workout) else "secondary",
                )
                if btn:
                    _init_session(letter, state, save_fn)
                    st.rerun()

    # ── Registrar treino já feito (sem detalhar séries) ─────────────────────────
    with st.expander("✅ Registrar treino já feito (sem detalhar séries)"):
        quick = st.selectbox(
            "Treino", list(WORKOUT_LABELS.keys()),
            format_func=lambda w: WORKOUT_LABELS.get(w, w),
            key="quick_mark_sel",
        )
        q_conflict, q_msg = check_72h_conflict(state, quick)
        if q_conflict:
            st.caption(q_msg)
        if st.button(f"Registrar Treino {quick}", use_container_width=True, key="quick_mark_btn"):
            mark_workout_done(state, workout=quick)
            save_fn(state)
            st.success(f"Treino {quick} registrado!")
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Últimos Treinos de Musculação")
    _render_weight_history(state)


def _render_weight_history(state: dict):
    import pandas as pd
    from datetime import datetime
    from parsers.strava import get_weight_training

    rows = []

    # Strava (fonte principal — histórico completo)
    strava_df = st.session_state.get("strava_df")
    wt = get_weight_training(strava_df)
    if not wt.empty:
        for _, r in wt.head(30).iterrows():
            data = r.get("data")
            data_fmt = data.strftime("%d/%m/%Y") if hasattr(data, "strftime") else str(data)[:10]
            nome = str(r.get("nome", "")).strip() or "Musculação"
            dur = r.get("duracao_min")
            fc = r.get("fc_media")
            rows.append({
                "Data": data_fmt,
                "Treino": nome,
                "Duração": f"{int(dur)} min" if pd.notna(dur) and dur > 0 else "—",
                "FC Média": f"{int(fc)} bpm" if pd.notna(fc) and fc > 0 else "—",
            })

    # Fallback: histórico interno do app
    if not rows:
        for s in state.get("workout_history", [])[:20]:
            try:
                dt = datetime.fromisoformat(s["completed_at"])
                data_fmt = dt.strftime("%d/%m/%Y")
                hora = dt.strftime("%H:%M")
            except Exception:
                data_fmt = s.get("date", "")
                hora = "—"
            w = s.get("workout", "")
            vol = s.get("volume_total", 0)
            rows.append({
                "Data": data_fmt,
                "Treino": f"{w} — {WORKOUT_DESC.get(w, '')}",
                "Duração": hora,
                "FC Média": f"{vol:,.0f} kg vol.".replace(",", "."),
            })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Faça upload do CSV do Strava na sidebar para ver seu histórico de musculação.")


# ── Sessão ativa ───────────────────────────────────────────────────────────────

def _render_session(state: dict, save_fn):
    session = st.session_state.active_workout
    workout = session["workout"]
    exercises = EXERCISES[workout]
    started_at = session.get("started_at", now_br().isoformat())

    # Wake lock
    if not st.session_state.get("_wakelock_active"):
        _components.html(_WAKELOCK_ON, height=0)
        st.session_state._wakelock_active = True

    # Header
    col_title, col_cancel = st.columns([4, 1])
    with col_title:
        st.markdown(f"### 🏋️ Treino {workout} — {WORKOUT_DESC[workout]}")
    with col_cancel:
        if st.button("✕ Sair", help="Cancela sem salvar"):
            st.session_state.active_workout = None
            st.session_state._rest_ts = 0.0
            state.pop("_active_workout", None)
            st.session_state._wakelock_active = False
            _components.html(_WAKELOCK_OFF, height=0)
            save_fn(state)
            st.rerun()

    # Timer global — começa na primeira série marcada
    first_set_ts = session.get("first_set_ts") or ""
    _components.html(_make_global_timer(first_set_ts), height=32)

    # Progresso
    all_sets = [s for ex in exercises for s in session["sets"].get(ex["nome"], [])]
    done_sets = [s for s in all_sets if s["done"]]
    progress = len(done_sets) / len(all_sets) if all_sets else 0
    st.progress(progress, text=f"{len(done_sets)} / {len(all_sets)} séries")

    st.markdown("---")

    _REST_90S = {
        "Puxada Alta Polia", "Remada Sentada c/ Pegada V", "Remada Chest Supported",
        "Puxada Fechada Polia", "Remada Unilateral Halter", "Leg Press 45°",
        "Supino Inclinado Halter", "Supino Reto Halter", "Supino Reto Máquina",
    }

    # Exercícios
    for ex in exercises:
        name = ex["nome"]
        reps_range = ex.get("reps", "10-12")
        peso_prog = ex.get("peso_prog")
        ex_sets = session["sets"].get(name, [])
        done_count = sum(1 for s in ex_sets if s["done"])
        all_done = done_count == len(ex_sets) and len(ex_sets) > 0

        icon = "✅" if all_done else "○"
        last = _get_last_sets(name, state)
        last_hint = ""
        if last:
            last_hint = "  ·  ".join(
                f"{s['weight']}kg×{s['reps']}" for s in last if s.get("done")
            )

        label = f"{icon} {name}  —  {ex['series']}×{reps_range}"
        with st.expander(label, expanded=not all_done):
            if last_hint:
                st.caption(f"Última vez: {last_hint}")

            # Sugestão de progressão
            if all_done and peso_prog:
                reps_max = int(reps_range.split("-")[-1])
                all_at_max = all(s.get("reps", 0) >= reps_max for s in ex_sets if s.get("done"))
                if all_at_max:
                    st.success(f"🚀 Progressão sugerida: **{peso_prog:g} kg** na próxima sessão")

            for i, s in enumerate(ex_sets):
                c_w, c_r, c_btn = st.columns([3, 3, 1.2])
                with c_w:
                    w = st.number_input(
                        f"S{i+1} — kg",
                        min_value=0.0, max_value=400.0, step=2.5,
                        value=float(s["weight"]),
                        key=f"w_{name}_{i}",
                    )
                    s["weight"] = w
                    if last and i < len(last):
                        last_w = float(last[i].get("weight", 0))
                        if last_w > 0:
                            diff = w - last_w
                            if diff > 0:
                                st.markdown(f"<span style='color:#4CAF50;font-size:0.78rem'>↑ +{diff:g}kg</span>", unsafe_allow_html=True)
                            elif diff < 0:
                                st.markdown(f"<span style='color:#F44336;font-size:0.78rem'>↓ {diff:g}kg</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='color:#888;font-size:0.78rem'>= igual</span>", unsafe_allow_html=True)
                with c_r:
                    r = st.number_input(
                        "Reps",
                        min_value=0, max_value=200, step=1,
                        value=int(s["reps"]),
                        key=f"r_{name}_{i}",
                    )
                    s["reps"] = r
                with c_btn:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if s["done"]:
                        if st.button("✅", key=f"chk_{name}_{i}"):
                            s["done"] = False
                            _save_active_workout(state, save_fn)
                            st.rerun()
                    else:
                        if st.button("○", key=f"chk_{name}_{i}"):
                            s["done"] = True
                            now_ts = time.time()
                            st.session_state._ex_rest_ts[name] = now_ts
                            st.session_state._rest_ts = now_ts
                            st.session_state._last_ex = name
                            # Marca timestamp da primeira série feita
                            if not session.get("first_set_ts"):
                                session["first_set_ts"] = now_br().isoformat()
                            _save_active_workout(state, save_fn)
                            st.rerun()

            # ── Timer de descanso por exercício ──────────────────────────────
            rest_dur = 90 if name in _REST_90S else 60
            ex_ts = st.session_state._ex_rest_ts.get(name, 0)
            if ex_ts and ex_ts > 0:
                elapsed_r = time.time() - ex_ts
                remaining = max(0, int(rest_dur - elapsed_r))
                is_running = remaining > 0
                if not is_running:
                    st.session_state._ex_rest_ts[name] = 0
            else:
                remaining = 0
                is_running = False
            _components.html(_make_rest_timer(remaining, is_running), height=210, scrolling=False)

    st.markdown("---")

    col_fin, col_vol = st.columns([2, 1])
    with col_vol:
        vol_atual = sum(
            s["weight"] * s["reps"]
            for ex in exercises
            for s in session["sets"].get(ex["nome"], [])
            if s["done"]
        )
        st.metric("Volume atual", f"{vol_atual:,.0f} kg")
    with col_fin:
        if st.button("🏁 Finalizar Treino", type="primary", use_container_width=True):
            _finish_workout(state, save_fn)
            import json as _json
            _payload = _json.dumps(state, ensure_ascii=False)
            _components.html(f"""<script>
try{{localStorage.setItem('treino_hub_state',{_json.dumps(_payload)});}}catch(e){{}}
window.parent.location.reload();
</script>""", height=0)
