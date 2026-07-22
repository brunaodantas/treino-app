import streamlit as st
from datetime import date

META = {"kcal": 2100, "prot": 188, "carb": 180, "gord": 60}

PERIODOS = [
    {
        "id": "manha",
        "label": "☀️ Manhã (7–9h)",
        "placeholder": "Ex: café preto + vitamina whey 60g + leite + banana + aveia",
        "preset": {"kcal": 560, "prot": 65, "carb": 55, "gord": 15},
    },
    {
        "id": "almoco",
        "label": "🍽️ Almoço (12h)",
        "placeholder": "Ex: frango 170g + arroz + feijão + verduras",
        "preset": {"kcal": 635, "prot": 56, "carb": 69, "gord": 7},
    },
    {
        "id": "tarde",
        "label": "🥛 Tarde (15–16h)",
        "placeholder": "Ex: iogurte grego 200g + whey",
        "preset": {"kcal": 290, "prot": 50, "carb": 8, "gord": 6},
    },
    {
        "id": "jantar",
        "label": "🌙 Jantar (20h)",
        "placeholder": "Ex: vitamina whey + leite + fruta + aveia",
        "preset": {"kcal": 560, "prot": 45, "carb": 53, "gord": 15},
    },
]


def _bar(valor, meta, cor):
    pct = min(valor / meta, 1.0) if meta else 0
    pct_txt = f"{int(pct * 100)}%"
    return (
        f"<div style='background:#1E2130;border-radius:6px;height:10px;margin:2px 0 6px'>"
        f"<div style='background:{cor};width:{pct_txt};height:10px;border-radius:6px'></div></div>"
    )


def render_nutricao(state: dict, save_fn):
    st.markdown("### 🥗 Nutrição")

    today = str(date.today())
    nut = state.setdefault("nutricao", {})
    if nut.get("data") != today:
        nut["data"] = today
        nut["periodos"] = {}
        save_fn(state)

    periodos_state = nut.setdefault("periodos", {})

    # ── Totais ────────────────────────────────────────────────────────────────
    totais = {"kcal": 0, "prot": 0, "carb": 0, "gord": 0}
    for p in PERIODOS:
        ps = periodos_state.get(p["id"], {})
        if ps.get("comeu"):
            for k in totais:
                totais[k] += ps.get(k, 0)

    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px'>"
        f"<div><b>{totais['kcal']}</b> / {META['kcal']} kcal</div>"
        f"<div><b>{totais['prot']}g</b> / {META['prot']}g prot</div>"
        f"<div><b>{totais['carb']}g</b> / {META['carb']}g carb</div>"
        f"<div><b>{totais['gord']}g</b> / {META['gord']}g gord</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        _bar(totais["kcal"], META["kcal"], "#FF6B35")
        + _bar(totais["prot"], META["prot"], "#4A90D9")
        + _bar(totais["carb"], META["carb"], "#4CAF50")
        + _bar(totais["gord"], META["gord"], "#FFC107"),
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Períodos ──────────────────────────────────────────────────────────────
    changed = False
    for p in PERIODOS:
        pid = p["id"]
        ps = periodos_state.setdefault(pid, {
            "comeu": False,
            "descricao": "",
            **p["preset"],
        })

        with st.expander(p["label"], expanded=not ps["comeu"]):
            comeu = st.checkbox("Comi esta refeição", value=ps["comeu"], key=f"comeu_{pid}")
            if comeu != ps["comeu"]:
                ps["comeu"] = comeu
                changed = True

            desc = st.text_area(
                "O que comi",
                value=ps.get("descricao", ""),
                placeholder=p["placeholder"],
                key=f"desc_{pid}",
                height=68,
            )
            if desc != ps.get("descricao", ""):
                ps["descricao"] = desc
                changed = True

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                v = st.number_input("Kcal", min_value=0, max_value=2000,
                                    value=int(ps.get("kcal", 0)), step=10, key=f"kcal_{pid}")
                if v != ps.get("kcal"):
                    ps["kcal"] = v; changed = True
            with c2:
                v = st.number_input("Prot (g)", min_value=0, max_value=200,
                                    value=int(ps.get("prot", 0)), step=1, key=f"prot_{pid}")
                if v != ps.get("prot"):
                    ps["prot"] = v; changed = True
            with c3:
                v = st.number_input("Carb (g)", min_value=0, max_value=300,
                                    value=int(ps.get("carb", 0)), step=1, key=f"carb_{pid}")
                if v != ps.get("carb"):
                    ps["carb"] = v; changed = True
            with c4:
                v = st.number_input("Gord (g)", min_value=0, max_value=200,
                                    value=int(ps.get("gord", 0)), step=1, key=f"gord_{pid}")
                if v != ps.get("gord"):
                    ps["gord"] = v; changed = True

    if changed:
        nut["periodos"] = periodos_state
        state["nutricao"] = nut
        save_fn(state)
