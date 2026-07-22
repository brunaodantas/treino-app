import streamlit as st
from datetime import date

META = {"kcal": 2100, "prot": 188, "carb": 180, "gord": 60}

ALIMENTOS = {
    # Proteínas
    "Whey Protein (40g)":         (160, 36, 4,  2,  40),
    "Whey Protein (60g)":         (240, 54, 6,  3,  60),
    "Frango peito (100g)":        (165, 31, 0,  4,  100),
    "Ovo inteiro (unid ~50g)":    (70,  6,  0,  5,  50),
    "Iogurte Grego (100g)":       (65,  9,  4,  3,  100),
    "Iogurte Grego (200g)":       (130, 18, 8,  6,  200),
    # Carboidratos
    "Arroz branco cozido (100g)": (130, 3,  28, 0,  100),
    "Feijão cozido (100g)":       (130, 8,  23, 1,  100),
    "Aveia (30g)":                (111, 4,  19, 2,  30),
    "Banana média (~100g)":       (89,  1,  23, 0,  100),
    "Mamão (150g)":               (65,  1,  17, 0,  150),
    "Abacate (100g)":             (160, 2,  9,  15, 100),
    "Pão de forma (fatia ~25g)":  (66,  2,  12, 1,  25),
    "Batata-doce cozida (100g)":  (86,  2,  20, 0,  100),
    # Laticínios
    "Leite integral (200ml)":     (122, 6,  10, 7,  200),
    "Leite integral (300ml)":     (183, 9,  14, 10, 300),
    "Chocolate em pó (15g)":      (60,  2,  12, 1,  15),
    # Gorduras
    "Azeite (1 colher 10ml)":     (88,  0,  0,  10, 10),
    "Amendoim (30g)":             (170, 8,  5,  14, 30),
    # Legumes / verduras
    "Verduras mistas (100g)":     (30,  2,  5,  0,  100),
    "Brócolis (100g)":            (34,  3,  7,  0,  100),
    # Sem macro relevante
    "Café preto":                 (5,   0,  1,  0,  200),
    "Creatina (5g)":              (0,   0,  0,  0,  5),
}

PERIODOS = [
    {"id": "manha",  "label": "☀️ Manhã (7–9h)"},
    {"id": "almoco", "label": "🍽️ Almoço (12h)"},
    {"id": "tarde",  "label": "🥛 Tarde (15–16h)"},
    {"id": "jantar", "label": "🌙 Jantar (20h)"},
]
PERIODO_IDS   = [p["id"]    for p in PERIODOS]
PERIODO_LABEL = {p["id"]: p["label"] for p in PERIODOS}


def _bar(valor, meta, cor):
    pct = min(valor / meta, 1.0) if meta else 0
    return (
        f"<div style='background:#1E2130;border-radius:6px;height:10px;margin:2px 0 6px'>"
        f"<div style='background:{cor};width:{int(pct*100)}%;height:10px;border-radius:6px'></div></div>"
    )


def _macros_item(nome, qtd_g):
    if nome not in ALIMENTOS:
        return 0, 0, 0, 0
    kcal_base, prot_base, carb_base, gord_base, ref_g = ALIMENTOS[nome]
    fator = qtd_g / ref_g
    return (
        round(kcal_base * fator),
        round(prot_base * fator, 1),
        round(carb_base * fator, 1),
        round(gord_base * fator, 1),
    )


def render_nutricao(state: dict, save_fn):
    col_title, col_refresh = st.columns([6, 1])
    col_title.markdown("### 🥗 Nutrição")
    if col_refresh.button("🔄", key="nut_refresh", help="Atualizar"):
        st.rerun()

    today = str(date.today())
    nut = state.setdefault("nutricao", {})
    if nut.get("data") != today:
        nut["data"] = today
        nut["periodos"] = {p["id"]: [] for p in PERIODOS}
        save_fn(state)

    periodos_state = nut.setdefault("periodos", {p["id"]: [] for p in PERIODOS})

    # ── Totais ────────────────────────────────────────────────────────────────
    tot = {"kcal": 0, "prot": 0.0, "carb": 0.0, "gord": 0.0}
    for pid_data in periodos_state.values():
        for item in pid_data:
            k, p, c, g = _macros_item(item["nome"], item["qtd"])
            tot["kcal"] += k; tot["prot"] += p
            tot["carb"] += c; tot["gord"] += g

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Kcal", f"{tot['kcal']}", f"/ {META['kcal']}")
    col2.metric("Proteína", f"{tot['prot']:.0f}g", f"/ {META['prot']}g")
    col3.metric("Carb", f"{tot['carb']:.0f}g", f"/ {META['carb']}g")
    col4.metric("Gordura", f"{tot['gord']:.0f}g", f"/ {META['gord']}g")

    st.markdown(
        _bar(tot["kcal"], META["kcal"], "#FF6B35")
        + _bar(tot["prot"], META["prot"], "#4A90D9")
        + _bar(tot["carb"], META["carb"], "#4CAF50")
        + _bar(tot["gord"], META["gord"], "#FFC107"),
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Adicionar alimento (fora dos expanders para não fechar/saltar) ────────
    st.markdown("**Adicionar alimento**")
    col_per, col_ali = st.columns([2, 3])
    with col_per:
        periodo_escolhido = st.selectbox(
            "Refeição", PERIODO_IDS,
            format_func=lambda x: PERIODO_LABEL[x],
            key="nut_per",
            label_visibility="collapsed",
        )
    with col_ali:
        alimento_escolhido = st.selectbox(
            "Alimento", ["— selecione —"] + sorted(ALIMENTOS.keys()),
            key="nut_ali",
            label_visibility="collapsed",
        )

    ref_g = ALIMENTOS[alimento_escolhido][4] if alimento_escolhido != "— selecione —" else 100
    col_qtd, col_btn = st.columns([3, 1])
    with col_qtd:
        qtd = st.number_input(
            "Qtd (g/ml)", min_value=1, max_value=2000,
            value=ref_g, step=5, key="nut_qtd",
            label_visibility="collapsed",
        )
    with col_btn:
        if st.button("➕ Add", key="nut_add", use_container_width=True):
            if alimento_escolhido != "— selecione —":
                periodos_state.setdefault(periodo_escolhido, []).append(
                    {"nome": alimento_escolhido, "qtd": qtd}
                )
                nut["periodos"] = periodos_state
                state["nutricao"] = nut
                save_fn(state)
                st.rerun()

    st.markdown("---")

    # ── Resumo por período ────────────────────────────────────────────────────
    for p in PERIODOS:
        pid = p["id"]
        itens = periodos_state.get(pid, [])

        p_tot = {"kcal": 0, "prot": 0.0, "carb": 0.0, "gord": 0.0}
        for item in itens:
            k, pr, c, g = _macros_item(item["nome"], item["qtd"])
            p_tot["kcal"] += k; p_tot["prot"] += pr
            p_tot["carb"] += c; p_tot["gord"] += g

        resumo = f"{p_tot['kcal']} kcal · {p_tot['prot']:.0f}g prot" if itens else "vazio"

        with st.expander(f"{p['label']} — {resumo}"):
            if itens:
                changed = False
                to_remove = []
                for idx, item in enumerate(itens):
                    k, pr, c, g = _macros_item(item["nome"], item["qtd"])
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.caption(
                            f"**{item['nome']}** · {item['qtd']}g — "
                            f"{k} kcal · {pr:.0f}g prot · {c:.0f}g carb · {g:.0f}g gord"
                        )
                    with c2:
                        if st.button("✕", key=f"rm_{pid}_{idx}", use_container_width=True):
                            to_remove.append(idx)
                            changed = True
                if to_remove:
                    for idx in reversed(to_remove):
                        itens.pop(idx)
                    periodos_state[pid] = itens
                    nut["periodos"] = periodos_state
                    state["nutricao"] = nut
                    save_fn(state)
                    st.rerun()
            else:
                st.caption("Nenhum alimento adicionado.")
