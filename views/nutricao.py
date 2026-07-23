import streamlit as st
from datetime import date

META = {"kcal": 2100, "prot": 188, "carb": 180, "gord": 60}

ALIMENTOS = {
    "Vitamina base (leite+whey+achoc+creatina)": (403, 47, 30, 13, 1),
    "Whey Protein (40g)":         (160, 36, 4,  2,  40),
    "Whey Protein (60g)":         (240, 54, 6,  3,  60),
    "Frango peito (100g)":        (165, 31, 0,  4,  100),
    "Fígado de boi (100g)":       (135, 21, 4,  4,  100),
    "Ovo inteiro (~50g)":         (70,  6,  0,  5,  50),
    "Iogurte Grego (100g)":       (65,  9,  4,  3,  100),
    "Iogurte Grego (200g)":       (130, 18, 8,  6,  200),
    "Arroz branco cozido (100g)": (130, 3,  28, 0,  100),
    "Feijão cozido (100g)":       (130, 8,  23, 1,  100),
    "Aveia (30g)":                (111, 4,  19, 2,  30),
    "Banana média (~100g)":       (89,  1,  23, 0,  100),
    "Banana prata (~80g)":        (73,  1,  19, 0,  80),
    "Mamão (150g)":               (65,  1,  17, 0,  150),
    "Abacate (100g)":             (160, 2,  9,  15, 100),
    "Pão de forma (fatia ~25g)":  (66,  2,  12, 1,  25),
    "Batata-doce cozida (100g)":  (86,  2,  20, 0,  100),
    "Batata cozida (100g)":       (77,  2,  18, 0,  100),
    "Macarrão cozido (100g)":     (158, 5,  31, 1,  100),
    "Leite integral (200ml)":     (122, 6,  10, 7,  200),
    "Leite integral (300ml)":     (183, 9,  14, 10, 300),
    "Chocolate em pó (15g)":      (60,  2,  12, 1,  15),
    "Azeite (1 colher 10ml)":     (88,  0,  0,  10, 10),
    "Amendoim (30g)":             (170, 8,  5,  14, 30),
    "Verduras mistas (100g)":     (30,  2,  5,  0,  100),
    "Brócolis (100g)":            (34,  3,  7,  0,  100),
    "Abóbora cozida (100g)":      (26,  1,  6,  0,  100),
    "Cenoura cozida (100g)":      (35,  1,  8,  0,  100),
    "Café preto":                 (5,   0,  1,  0,  200),
    "Creatina (5g)":              (0,   0,  0,  0,  5),
}

CATEGORIAS = {
    "⚡ Combos":    ["Vitamina base (leite+whey+achoc+creatina)"],
    "🥩 Proteínas": ["Whey Protein (40g)", "Whey Protein (60g)", "Frango peito (100g)",
                     "Fígado de boi (100g)", "Ovo inteiro (~50g)",
                     "Iogurte Grego (100g)", "Iogurte Grego (200g)"],
    "🍚 Carbs":     ["Arroz branco cozido (100g)", "Feijão cozido (100g)", "Macarrão cozido (100g)",
                     "Aveia (30g)", "Banana média (~100g)", "Banana prata (~80g)", "Mamão (150g)",
                     "Abacate (100g)", "Pão de forma (fatia ~25g)",
                     "Batata-doce cozida (100g)", "Batata cozida (100g)"],
    "🥛 Laticínios":["Leite integral (200ml)", "Leite integral (300ml)", "Chocolate em pó (15g)"],
    "🫒 Outros":    ["Azeite (1 colher 10ml)", "Amendoim (30g)", "Verduras mistas (100g)",
                     "Brócolis (100g)", "Abóbora cozida (100g)", "Cenoura cozida (100g)",
                     "Café preto", "Creatina (5g)"],
}

PERIODOS = [
    {"id": "manha",  "label": "☀️ Manhã"},
    {"id": "almoco", "label": "🍽️ Almoço"},
    {"id": "tarde",  "label": "🥛 Tarde"},
    {"id": "jantar", "label": "🌙 Jantar"},
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
    if col_refresh.button("🔄", key="nut_refresh"):
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

    # ── Adicionar alimento — sem teclado automático ───────────────────────────
    st.markdown("**Adicionar alimento**")

    # 1. Período (radio horizontal — toque, sem teclado)
    periodo_escolhido = st.radio(
        "Refeição", PERIODO_IDS,
        format_func=lambda x: PERIODO_LABEL[x],
        horizontal=True, key="nut_per",
        label_visibility="collapsed",
    )

    # 2. Categoria (radio horizontal)
    cat_keys = list(CATEGORIAS.keys())
    categoria = st.radio(
        "Categoria", cat_keys,
        horizontal=True, key="nut_cat",
        label_visibility="collapsed",
    )

    # 3. Alimentos da categoria como botões — toque direto, sem teclado
    alimentos_cat = CATEGORIAS[categoria]
    sel = st.session_state.get("nut_sel")

    cols = st.columns(2)
    for i, nome in enumerate(alimentos_cat):
        ativo = nome == sel
        label = f"✅ {nome}" if ativo else nome
        if cols[i % 2].button(label, key=f"food_{nome}", use_container_width=True):
            st.session_state["nut_sel"] = nome
            st.rerun()

    # 4. Quantidade + Add (só aparece quando um alimento está selecionado)
    sel = st.session_state.get("nut_sel")
    if sel and sel in ALIMENTOS:
        ref_g = ALIMENTOS[sel][4]
        k0, p0, c0, g0 = _macros_item(sel, ref_g)
        st.caption(f"**{sel}** → {k0} kcal · {p0:.0f}g prot · {c0:.0f}g carb · {g0:.0f}g gord")

        col_qtd, col_add = st.columns([3, 2])
        with col_qtd:
            qtd = st.number_input(
                "Qtd (g/ml/porção)", min_value=1, max_value=2000,
                value=ref_g, step=5, key="nut_qtd",
            )
        with col_add:
            st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key="nut_add", use_container_width=True):
                periodos_state.setdefault(periodo_escolhido, []).append(
                    {"nome": sel, "qtd": qtd}
                )
                nut["periodos"] = periodos_state
                state["nutricao"] = nut
                save_fn(state)
                st.session_state.pop("nut_sel", None)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

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

        with st.expander(f"{p['label']} (7–9h) — {resumo}" if pid == "manha"
                         else f"{p['label']} — {resumo}"):
            if itens:
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
