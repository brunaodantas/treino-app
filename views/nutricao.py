import streamlit as st
from datetime import date

META = {"kcal": 2100, "prot": 188, "carb": 180, "gord": 60}

# Banco de alimentos — valores por porção indicada (fonte: TACO / rótulos típicos)
# Formato: (kcal, prot_g, carb_g, gord_g, ref_g)
ALIMENTOS = {
    # ── Proteínas animais ─────────────────────────────────────────────────────
    "🍗 Frango peito grelhado (100g)":  (163, 32, 0,  4,  100),
    "🍗 Frango peito cozido (150g)":    (245, 48, 0,  5,  150),
    "🥚 Ovo inteiro cozido":            (73,  6,  1,  5,  50),
    "🥚 Clara de ovo":                  (15,  3,  0,  0,  30),
    "🐟 Atum em água (lata 170g)":      (218, 46, 0,  3,  170),
    "🐟 Tilápia grelhada (100g)":       (128, 26, 0,  2,  100),
    "🥩 Patinho moído (100g)":          (219, 22, 0,  14, 100),
    "🥩 Carne bovina magra (100g)":     (210, 28, 0,  10, 100),
    # ── Laticínios e suplementos ──────────────────────────────────────────────
    "🥛 Leite integral (200ml)":        (122, 6,  10, 7,  200),
    "🥛 Leite integral (300ml)":        (183, 9,  14, 10, 300),
    "🫙 Iogurte grego integral (100g)": (97,  9,  4,  5,  100),
    "🫙 Iogurte grego integral (170g)": (165, 15, 7,  9,  170),
    "🧀 Queijo cottage (100g)":         (89,  11, 3,  4,  100),
    "🧀 Requeijão cremoso (30g)":       (68,  2,  2,  6,  30),
    "💪 Whey Protein (40g)":           (160, 36, 4,  2,  40),
    "💪 Whey Protein (60g)":           (240, 54, 6,  3,  60),
    # ── Cereais e carboidratos ────────────────────────────────────────────────
    "🍚 Arroz branco cozido (100g)":   (128, 3,  28, 0,  100),
    "🍚 Arroz branco cozido (150g)":   (192, 4,  42, 0,  150),
    "🫘 Feijão cozido (100g)":         (130, 9,  24, 1,  100),
    "🫘 Feijão cozido (150g)":         (195, 13, 35, 1,  150),
    "🌾 Aveia em flocos (30g)":        (111, 4,  19, 2,  30),
    "🌾 Aveia em flocos (50g)":        (185, 7,  32, 4,  50),
    "🍠 Batata-doce cozida (100g)":    (86,  2,  20, 0,  100),
    "🥔 Batata inglesa cozida (100g)": (82,  2,  19, 0,  100),
    "🍝 Macarrão cozido (100g)":       (146, 5,  30, 1,  100),
    "🫓 Tapioca (50g)":                (150, 0,  37, 0,  50),
    "🍞 Pão de forma (fatia 25g)":     (66,  2,  12, 1,  25),
    "🥖 Pão francês (50g)":            (134, 4,  27, 1,  50),
    # ── Frutas ────────────────────────────────────────────────────────────────
    "🍌 Banana média (100g)":          (89,  1,  23, 0,  100),
    "🫐 Mamão formosa (150g)":         (58,  1,  15, 0,  150),
    "🍎 Maçã (150g)":                  (83,  0,  22, 0,  150),
    "🍊 Laranja (150g)":               (69,  1,  18, 0,  150),
    "🍓 Morango (100g)":               (27,  1,  6,  0,  100),
    "🥑 Abacate (100g)":               (160, 2,  9,  15, 100),
    # ── Gorduras e oleaginosas ────────────────────────────────────────────────
    "🫒 Azeite (1 colher 10ml)":       (88,  0,  0,  10, 10),
    "🥜 Amendoim torrado (30g)":        (170, 8,  5,  14, 30),
    "🥜 Pasta de amendoim (30g)":       (183, 8,  6,  16, 30),
    "🌰 Mix oleaginosas (25g)":         (160, 5,  5,  14, 25),
    # ── Legumes e verduras ────────────────────────────────────────────────────
    "🥦 Brócolis (100g)":              (34,  3,  7,  0,  100),
    "🥗 Verduras mistas (100g)":       (25,  2,  4,  0,  100),
    "🍅 Tomate (100g)":                (19,  1,  4,  0,  100),
    "🫛 Abobrinha cozida (100g)":      (20,  1,  4,  0,  100),
    # ── Bebidas e temperos ────────────────────────────────────────────────────
    "☕ Café preto (200ml)":           (5,   0,  1,  0,  200),
    "🍫 Chocolate em pó (15g)":        (60,  2,  12, 1,  15),
    # ── Suplementos ───────────────────────────────────────────────────────────
    "⚗️ Creatina (5g)":               (0,   0,  0,  0,  5),
    "⚗️ BCAA (10g)":                  (40,  10, 0,  0,  10),
}

PERIODOS = [
    {"id": "manha",  "label": "☀️ Manhã (7–9h)"},
    {"id": "almoco", "label": "🍽️ Almoço (12h)"},
    {"id": "tarde",  "label": "🥛 Tarde (15–16h)"},
    {"id": "jantar", "label": "🌙 Jantar (20h)"},
]


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

    # ── Períodos ──────────────────────────────────────────────────────────────
    changed = False
    for p in PERIODOS:
        pid = p["id"]
        itens = periodos_state.setdefault(pid, [])

        # Calcula total do período
        p_tot = {"kcal": 0, "prot": 0.0, "carb": 0.0, "gord": 0.0}
        for item in itens:
            k, pr, c, g = _macros_item(item["nome"], item["qtd"])
            p_tot["kcal"] += k; p_tot["prot"] += pr
            p_tot["carb"] += c; p_tot["gord"] += g

        resumo = f"{p_tot['kcal']} kcal · {p_tot['prot']:.0f}g prot" if itens else "vazio"

        with st.expander(f"{p['label']} — {resumo}", expanded=False):
            # Adicionar alimento
            col_sel, col_qtd, col_btn = st.columns([4, 2, 1])
            with col_sel:
                escolha = st.selectbox(
                    "Alimento", ["— selecione —"] + sorted(ALIMENTOS.keys()),
                    key=f"sel_{pid}",
                )
            with col_qtd:
                ref_g = ALIMENTOS[escolha][4] if escolha != "— selecione —" else 100
                qtd = st.number_input("Qtd (g/ml)", min_value=1, max_value=1000,
                                      value=ref_g, step=5, key=f"qtd_{pid}")
            with col_btn:
                st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
                if st.button("➕", key=f"add_{pid}", use_container_width=True):
                    if escolha != "— selecione —":
                        itens.append({"nome": escolha, "qtd": qtd})
                        changed = True
                st.markdown("</div>", unsafe_allow_html=True)

            # Preview do item selecionado
            if escolha != "— selecione —":
                pk, pp, pc, pg = _macros_item(escolha, qtd)
                st.caption(
                    f"📊 **{pk} kcal** · {pp:.0f}g prot · {pc:.0f}g carb · {pg:.0f}g gord"
                )

            # Lista do período
            if itens:
                st.markdown("**Adicionados:**")
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
                for idx in reversed(to_remove):
                    itens.pop(idx)
            else:
                st.caption("Nenhum alimento adicionado ainda.")

    if changed:
        nut["periodos"] = periodos_state
        state["nutricao"] = nut
        save_fn(state)
