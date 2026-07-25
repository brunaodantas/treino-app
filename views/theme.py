"""
Tema visual do Treino Hub — glassmorphism, dark deep, laranja.

Uma função só: inject_theme(), chamada uma vez no topo do app.py.

Notas de implementação:
- Glass precisa de algo atrás para desfocar. O fundo tem dois blobs radiais
  (laranja e azul) fixos, senão o backdrop-filter não tem o que borrar e o
  card fica só cinza translúcido.
- backdrop-filter nunca é animado — o browser recalcula o blur a cada frame
  e engasga. As transições mexem só em background-color, border e transform.
- Texto nunca fica direto sobre 4% de opacidade: os blocos de conteúdo têm
  um véu mais opaco por baixo para garantir contraste.
"""

_THEME_CSS = """
<style>
:root{
  --bg-deep:#0a0e27;
  --bg-mid:#131a3a;
  --orange:#FF8C00;
  --orange-soft:rgba(255,140,0,.16);
  --orange-line:rgba(255,140,0,.28);
  --orange-glow:rgba(255,140,0,.35);
  --green:#22C55E;
  --green-soft:rgba(34,197,94,.14);
  --red:#EF4444;
  --red-soft:rgba(239,68,68,.14);
  --txt:#F1F5F9;
  --txt-dim:#94A3B8;
  --glass:rgba(255,255,255,.045);
  --glass-strong:rgba(255,255,255,.075);
  --glass-line:rgba(255,255,255,.10);
  --blur:blur(18px) saturate(150%);
  --shadow:0 8px 32px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.07);
  --radius:16px;
}

/* ── Fundo: base escura + blobs para o blur ter o que borrar ─────────────── */
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(60rem 40rem at 12% -8%, rgba(255,140,0,.16), transparent 62%),
    radial-gradient(48rem 34rem at 92% 8%, rgba(59,130,246,.14), transparent 60%),
    radial-gradient(40rem 30rem at 78% 96%, rgba(255,140,0,.10), transparent 62%),
    linear-gradient(168deg, var(--bg-deep) 0%, var(--bg-mid) 58%, #0d1230 100%);
  background-attachment: fixed;
  color: var(--txt);
}
[data-testid="stHeader"]{display:none}
footer, #MainMenu{display:none}
[data-testid="stAppViewContainer"] > .main{background:transparent}
.block-container{padding-top:1.4rem;padding-bottom:3rem;max-width:46rem}

h1,h2,h3,h4{color:var(--txt);letter-spacing:-.015em}
h1{font-weight:700}
p,label,span,li{color:var(--txt)}
[data-testid="stCaptionContainer"], .stCaption, small{color:var(--txt-dim)!important}
hr{border-color:var(--glass-line);opacity:.7}

/* ── Card glass base ────────────────────────────────────────────────────── */
[data-testid="stExpander"]{
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--orange-line);
  border-radius:var(--radius);
  box-shadow:var(--shadow);
  margin-bottom:.85rem;
  overflow:hidden;
  transition:border-color .18s ease, background-color .18s ease;
}
[data-testid="stExpander"]:hover{
  border-color:var(--orange-glow);
  background:var(--glass-strong);
}
[data-testid="stExpander"] summary{
  padding:.9rem 1.1rem;
  font-weight:600;
  color:var(--txt);
}
[data-testid="stExpander"] summary:hover{color:var(--orange)}
[data-testid="stExpander"] summary svg{fill:var(--orange)}
/* véu mais opaco atrás do conteúdo — contraste de texto */
[data-testid="stExpander"] [data-testid="stExpanderDetails"]{
  background:rgba(10,14,39,.34);
  padding:.4rem 1.1rem 1rem;
}

/* ── Métricas ───────────────────────────────────────────────────────────── */
[data-testid="stMetric"]{
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--orange-line);
  border-radius:var(--radius);
  box-shadow:var(--shadow);
  padding:1rem 1.1rem;
}
[data-testid="stMetricLabel"]{color:var(--txt-dim)!important;font-size:.78rem;
  text-transform:uppercase;letter-spacing:.08em}
[data-testid="stMetricValue"]{color:var(--orange)!important;font-weight:700}

/* ── Botões ─────────────────────────────────────────────────────────────── */
.stButton > button{
  min-height:3rem;
  font-size:1rem;
  font-weight:600;
  color:var(--txt);
  background:var(--glass-strong);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--orange-line);
  border-radius:12px;
  box-shadow:0 4px 18px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.08);
  transition:background-color .16s ease, border-color .16s ease, transform .12s ease;
}
.stButton > button:hover{
  background:var(--orange-soft);
  border-color:var(--orange);
  color:#fff;
  transform:translateY(-1px);
}
.stButton > button:active{transform:translateY(0)}
/* botão primário — laranja cheio */
.stButton > button[kind="primary"]{
  background:linear-gradient(135deg, var(--orange) 0%, #FF6B35 100%);
  border-color:transparent;
  color:#0a0e27;
  font-weight:700;
  box-shadow:0 6px 24px rgba(255,140,0,.34), inset 0 1px 0 rgba(255,255,255,.25);
}
.stButton > button[kind="primary"]:hover{
  background:linear-gradient(135deg,#FFA733 0%, var(--orange) 100%);
  color:#0a0e27;
}

/* ── Inputs ─────────────────────────────────────────────────────────────── */
.stNumberInput input, .stTextInput input, .stTextArea textarea{
  font-size:1.1rem;
  color:var(--txt)!important;
  background:rgba(10,14,39,.5)!important;
  border:1px solid var(--glass-line)!important;
  border-radius:10px!important;
}
.stNumberInput input{height:2.8rem}
.stNumberInput input:focus, .stTextInput input:focus{
  border-color:var(--orange)!important;
  box-shadow:0 0 0 3px var(--orange-soft)!important;
}
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"]{
  background:var(--glass-strong);color:var(--orange);border:none}
[data-testid="stNumberInputStepUp"]:hover,
[data-testid="stNumberInputStepDown"]:hover{background:var(--orange-soft)}

/* selectbox / multiselect */
[data-baseweb="select"] > div{
  background:rgba(10,14,39,.5)!important;
  border-color:var(--glass-line)!important;
  border-radius:10px!important;
  color:var(--txt)!important;
}

/* ── Slider ─────────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"]{
  background:var(--orange)!important;
  box-shadow:0 0 0 5px var(--orange-soft), 0 2px 8px rgba(0,0,0,.4)!important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[style*="background"]{
  background:var(--orange)!important;
}
[data-testid="stTickBarMin"], [data-testid="stTickBarMax"]{color:var(--txt-dim)}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]{
  overflow-x:auto;
  flex-wrap:nowrap;
  gap:.3rem;
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--glass-line);
  border-radius:14px;
  padding:.35rem;
  box-shadow:var(--shadow);
  scrollbar-width:none;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{display:none}
.stTabs [data-baseweb="tab"]{
  background:transparent;
  border-radius:10px;
  padding:.5rem .85rem;
  color:var(--txt-dim);
  font-weight:600;
  white-space:nowrap;
  transition:background-color .16s ease, color .16s ease;
}
.stTabs [data-baseweb="tab"]:hover{color:var(--txt);background:var(--glass-strong)}
.stTabs [aria-selected="true"]{
  background:var(--orange-soft)!important;
  color:var(--orange)!important;
  box-shadow:inset 0 0 0 1px var(--orange-line);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{display:none}

/* ── Progresso ──────────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div{
  background:rgba(255,255,255,.07);
  border-radius:99px;
  height:.55rem;
}
[data-testid="stProgress"] > div > div > div{
  background:linear-gradient(90deg, var(--orange) 0%, #FFB05C 100%)!important;
  box-shadow:0 0 14px var(--orange-glow);
  border-radius:99px;
}

/* ── Alertas: verde = bom, vermelho = alerta, laranja = atenção ─────────── */
[data-testid="stAlert"]{
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border-radius:var(--radius);
  border-width:1px;
  border-style:solid;
  box-shadow:var(--shadow);
}
[data-testid="stAlert"] p, [data-testid="stAlert"] div{color:var(--txt)!important}
[data-testid="stAlertContentSuccess"], .stSuccess{
  background:var(--green-soft)!important;border-color:rgba(34,197,94,.4)!important}
[data-testid="stAlertContentError"], .stError{
  background:var(--red-soft)!important;border-color:rgba(239,68,68,.42)!important}
[data-testid="stAlertContentWarning"], .stWarning{
  background:var(--orange-soft)!important;border-color:var(--orange-line)!important}
[data-testid="stAlertContentInfo"], .stInfo{
  background:rgba(59,130,246,.13)!important;border-color:rgba(59,130,246,.35)!important}

/* ── Tabelas e dataframes ───────────────────────────────────────────────── */
[data-testid="stDataFrame"], [data-testid="stTable"]{
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--glass-line);
  border-radius:var(--radius);
  overflow:hidden;
  box-shadow:var(--shadow);
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"]{
  background:rgba(10,14,39,.72);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border-right:1px solid var(--orange-line);
}

/* ── Plotly em vidro ────────────────────────────────────────────────────── */
[data-testid="stPlotlyChart"]{
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--glass-line);
  border-radius:var(--radius);
  padding:.5rem;
  box-shadow:var(--shadow);
}

/* iframes de componente (timers) — fundo transparente */
[data-testid="stIFrame"]{background:transparent}

/* ── Mobile ─────────────────────────────────────────────────────────────── */
@media (max-width:768px){
  .block-container{padding:1rem .75rem 2.5rem}
  :root{--blur:blur(14px) saturate(140%)}
  [data-testid="stExpander"] summary{padding:.8rem .9rem}
  [data-testid="stExpander"] [data-testid="stExpanderDetails"]{padding:.4rem .9rem 1rem}
}

/* Respeita quem pediu menos movimento */
@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important}
}
</style>
"""


def inject_theme(st) -> None:
    """Injeta o tema. Chamar uma vez, logo depois do set_page_config."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)
