import streamlit as st
import streamlit.components.v1 as _components
from datetime import datetime
from logic.schedule import EXERCISES, WORKOUT_LABELS, MUSCLE_GROUPS, check_72h_conflict

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

_TIMER_HTML = """
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:transparent;font-family:-apple-system,sans-serif;padding:2px 0}}
  .lbl{{color:#aaa;font-size:12px;font-weight:500;margin-bottom:6px;letter-spacing:.5px}}
  .presets{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}}
  .pb{{background:#1E3A5F;border:1.5px solid #4A90D9;color:#DDD;padding:7px 10px;
       border-radius:8px;cursor:pointer;font-size:13px;transition:background .15s}}
  .pb.sel{{background:#4A90D9;color:#fff;border-color:#4A90D9}}
  .disp{{font-size:2.6rem;font-weight:700;text-align:center;letter-spacing:3px;
         padding:8px 0;color:#FAFAFA}}
  .disp.run{{color:#4CAF50}}
  .disp.done{{color:#FF6B35}}
  .ctrls{{display:flex;gap:8px;margin-top:6px}}
  .cb{{flex:1;padding:11px;border-radius:10px;border:none;cursor:pointer;
       font-size:14px;font-weight:600}}
  .go{{background:#4CAF50;color:#fff}}
  .go:disabled{{background:#444;color:#888;cursor:default}}
  .rst{{background:#333;color:#bbb}}
</style>
<div class="lbl">⏱ DESCANSO ENTRE SÉRIES</div>
<div class="presets" id="pre"></div>
<div class="disp" id="disp">--:--</div>
<div class="ctrls">
  <button class="cb go" id="goBtn" onclick="tog()" disabled>▶ Iniciar</button>
  <button class="cb rst" onclick="rst()">↺</button>
</div>
<script>
const OPTS=[{{l:'30s',s:30}},{{l:'45s',s:45}},{{l:'1 min',s:60}},
            {{l:'1:30',s:90}},{{l:'1:45',s:105}},{{l:'2 min',s:120}}];
let tot=0,rem=0,tid=null,run=false,selB=null;

if(Notification&&Notification.permission==='default')Notification.requestPermission();

const pEl=document.getElementById('pre');
OPTS.forEach(o=>{{
  const b=document.createElement('button');
  b.className='pb';b.textContent=o.l;b.onclick=()=>pick(o.s,b);pEl.appendChild(b);
}});

function pick(s,btn){{
  clearInterval(tid);run=false;tot=rem=s;
  if(selB)selB.classList.remove('sel');selB=btn;btn.classList.add('sel');
  render();document.getElementById('goBtn').disabled=false;
  document.getElementById('goBtn').textContent='▶ Iniciar';
}}

function fmt(s){{return Math.floor(s/60)+':'+(s%60).toString().padStart(2,'0');}}

function render(){{
  const d=document.getElementById('disp');
  if(rem>0){{d.textContent=fmt(rem);d.className='disp'+(run?' run':'');}}
  else{{d.textContent='✓ Vai!';d.className='disp done';}}
}}

function tog(){{
  if(!tot)return;
  if(run){{
    clearInterval(tid);run=false;
    document.getElementById('goBtn').textContent='▶ Continuar';
  }}else{{
    if(rem<=0)rem=tot;
    run=true;document.getElementById('goBtn').textContent='⏸ Pausar';
    tid=setInterval(()=>{{
      rem--;render();
      if(rem<=0){{
        clearInterval(tid);run=false;
        document.getElementById('goBtn').textContent='▶ Iniciar';
        beep();notif();
      }}
    }},1000);
  }}
  render();
}}

function rst(){{
  clearInterval(tid);run=false;rem=tot;render();
  document.getElementById('goBtn').textContent='▶ Iniciar';
  document.getElementById('goBtn').disabled=!tot;
}}

function beep(){{
  try{{
    const a=new AudioContext(),o=a.createOscillator(),g=a.createGain();
    o.connect(g);g.connect(a.destination);o.frequency.value=880;g.gain.value=0.3;
    o.start();g.gain.exponentialRampToValueAtTime(0.001,a.currentTime+0.6);
    o.stop(a.currentTime+0.6);
  }}catch(e){{}}
}}

function notif(){{
  if(Notification&&Notification.permission==='granted'){{
    try{{new Notification('Treino Hub 🏋️',{{body:'Descanso terminado! Próxima série.'}});}}catch(e){{}}
  }}
}}
</script>
"""

_WAKELOCK_ON = """
<script>
(function(){
  const p=(() => { try { return window.parent; } catch(e) { return window; } })();
  const nav=(p||window).navigator;
  if(nav&&'wakeLock'in nav){
    nav.wakeLock.request('screen').then(lock=>{
      (p||window)._twl=lock;
      lock.addEventListener('release',()=>{ (p||window)._twl=null; });
    }).catch(()=>{});
  }
})();
</script>
"""

_WAKELOCK_OFF = """
<script>
(function(){
  const p=(() => { try { return window.parent; } catch(e) { return window; } })();
  const w=p||window;
  if(w._twl){ w._twl.release(); w._twl=null; }
})();
</script>
"""


def _get_last_sets(exercise_name: str, state: dict) -> list:
    for session in state.get("workout_history", []):
        sets = session.get("sets", {}).get(exercise_name, [])
        if sets:
            return sets
    return []


def _save_active_workout(state: dict, save_fn):
    """Persiste o treino em andamento no app_state para sobreviver a recargas."""
    if st.session_state.get("active_workout"):
        state["_active_workout"] = st.session_state.active_workout
    else:
        state.pop("_active_workout", None)
    save_fn(state)


def _init_session(workout: str, state: dict, save_fn):
    sets = {}
    for ex in EXERCISES[workout]:
        last = _get_last_sets(ex["nome"], state)
        ex_sets = []
        for i in range(ex["series"]):
            if last and i < len(last):
                ex_sets.append({
                    "weight": float(last[i].get("weight", 0)),
                    "reps": int(last[i].get("reps", 0)),
                    "done": False,
                })
            else:
                ex_sets.append({"weight": 0.0, "reps": 0, "done": False})
        sets[ex["nome"]] = ex_sets

    st.session_state.active_workout = {
        "workout": workout,
        "started_at": datetime.now().isoformat(),
        "sets": sets,
    }
    # Salva backup imediato para proteger contra crash
    _save_active_workout(state, save_fn)


def _finish_workout(state: dict, save_fn):
    from parsers.strava_api import is_connected, get_valid_token, create_activity

    session = st.session_state.active_workout
    workout = session["workout"]
    now = datetime.now()
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
    state.pop("_active_workout", None)  # limpa backup de crash
    st.session_state._wakelock_active = False
    save_fn(state)

    st.success(f"✅ Treino {workout} finalizado! Volume: {volume:,.0f} kg")
    _components.html(_WAKELOCK_OFF, height=0)

    # Salvar no Strava se conectado
    if is_connected(state):
        token = get_valid_token(state, save_fn)
        if token:
            desc = f"{WORKOUT_DESC[workout]}\nVolume total: {volume:,.0f} kg"
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
                st.toast("Strava: não foi possível salvar", icon="⚠️")


def render_musculacao(state: dict, hevy_df, save_fn):
    if "active_workout" not in st.session_state:
        # Tenta restaurar treino interrompido do backup de crash
        st.session_state.active_workout = state.get("_active_workout", None)

    if st.session_state.active_workout is None:
        _render_picker(state, save_fn)
    else:
        _render_session(state, save_fn)


# ── Tela de escolha de treino ──────────────────────────────────────────────────

def _render_picker(state: dict, save_fn):
    # Libera wake lock se houver algum residual
    if st.session_state.get("_wakelock_active"):
        _components.html(_WAKELOCK_OFF, height=0)
        st.session_state._wakelock_active = False

    st.markdown("### Qual treino hoje?")

    rows = [["A", "B"], ["C", "D"], ["E"]]
    for row in rows:
        cols = st.columns(len(row))
        for col, letter in zip(cols, row):
            with col:
                conflict, _ = check_72h_conflict(state, letter)
                warn = "  ⚠️" if conflict else ""
                btn = st.button(
                    f"**{letter}** — {WORKOUT_DESC[letter]}{warn}",
                    key=f"pick_{letter}",
                    use_container_width=True,
                    type="secondary" if conflict else "primary",
                )
                if btn:
                    _init_session(letter, state, save_fn)
                    st.rerun()

    history = state.get("workout_history", [])
    if history:
        st.markdown("---")
        st.markdown("#### Últimos treinos")
        for s in history[:6]:
            vol = s.get("volume_total", 0)
            st.markdown(
                f"**{s['workout']}** — {s['date']} — {vol:,.0f} kg volume"
            )


# ── Sessão ativa ───────────────────────────────────────────────────────────────

def _render_session(state: dict, save_fn):
    session = st.session_state.active_workout
    workout = session["workout"]
    exercises = EXERCISES[workout]

    # Wake lock: mantém tela acesa durante o treino
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
            state.pop("_active_workout", None)
            st.session_state._wakelock_active = False
            _components.html(_WAKELOCK_OFF, height=0)
            save_fn(state)
            st.rerun()

    # Progresso global
    all_sets = [s for ex in exercises for s in session["sets"].get(ex["nome"], [])]
    done_sets = [s for s in all_sets if s["done"]]
    progress = len(done_sets) / len(all_sets) if all_sets else 0
    st.progress(progress, text=f"{len(done_sets)} / {len(all_sets)} séries")

    st.markdown("---")

    # Timer de descanso
    _components.html(_TIMER_HTML, height=210, scrolling=False)

    st.markdown("---")

    # Exercícios
    for ex in exercises:
        name = ex["nome"]
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

        with st.expander(f"{icon} {name}", expanded=not all_done):
            if last_hint:
                st.caption(f"Última vez: {last_hint}")

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
                            _save_active_workout(state, save_fn)  # auto-save no toggle
                            st.rerun()
                    else:
                        if st.button("○", key=f"chk_{name}_{i}"):
                            s["done"] = True
                            _save_active_workout(state, save_fn)  # auto-save no toggle
                            st.rerun()

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
            st.rerun()
