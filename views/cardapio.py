import streamlit as st
from datetime import date

META_PROTEINA = 188

REFEICOES = [
    {"horario": "7h",    "nome": "Café da manhã",     "descricao": "Café preto",                                   "proteina": 0,  "emoji": "☕"},
    {"horario": "9h",    "nome": "Vitamina manhã",     "descricao": "Whey 40g + leite + banana/abacate/mamão + aveia + chocolate", "proteina": 45, "emoji": "🥤"},
    {"horario": "12h",   "nome": "Almoço",             "descricao": "Frango 170g + verduras + arroz + feijão",      "proteina": 48, "emoji": "🍽️"},
    {"horario": "15-16h","nome": "Snack da tarde",     "descricao": "Iogurte grego 200g + whey",                    "proteina": 50, "emoji": "🥛"},
    {"horario": "20h",   "nome": "Jantar",             "descricao": "Vitamina whey + leite + fruta + aveia + chocolate", "proteina": 45, "emoji": "🌙"},
]


def render_cardapio(state: dict, save_fn):
    st.markdown("### 🥗 Cardápio do Dia")

    today = str(date.today())

    # Inicializa registro de refeições no estado
    cardapio_state = state.setdefault("cardapio", {})
    if cardapio_state.get("data") != today:
        cardapio_state["data"] = today
        cardapio_state["marcadas"] = [False] * len(REFEICOES)
        cardapio_state["hidratacao"] = 0
        save_fn(state)

    marcadas = cardapio_state.get("marcadas", [False] * len(REFEICOES))
    while len(marcadas) < len(REFEICOES):
        marcadas.append(False)

    # Proteína acumulada
    proteina_total = sum(
        r["proteina"] for i, r in enumerate(REFEICOES) if marcadas[i]
    )
    proteina_pct = min(proteina_total / META_PROTEINA, 1.0)

    # Barra de progresso de proteína
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Proteína: {proteina_total}g / {META_PROTEINA}g**")
        st.progress(proteina_pct)
    with col2:
        if proteina_total >= META_PROTEINA:
            st.success("✅ Meta!")
        else:
            faltam = META_PROTEINA - proteina_total
            st.info(f"Faltam {faltam}g")

    st.markdown("---")

    # Lista de refeições
    changed = False
    for i, ref in enumerate(REFEICOES):
        col_check, col_info = st.columns([1, 6])
        with col_check:
            novo = st.checkbox(
                "",
                value=marcadas[i],
                key=f"refeicao_{i}_{today}",
            )
            if novo != marcadas[i]:
                marcadas[i] = novo
                changed = True
        with col_info:
            status = "~~" if marcadas[i] else ""
            st.markdown(
                f"{ref['emoji']} **{ref['horario']} — {ref['nome']}** · {ref['proteina']}g  \n"
                f"{status}{ref['descricao']}{status}"
            )

    if changed:
        cardapio_state["marcadas"] = marcadas
        save_fn(state)

    st.markdown("---")

    # Hidratação
    st.markdown("### 💧 Hidratação (meta: 4L = 8 garrafas de 500ml)")
    hidratacao = cardapio_state.get("hidratacao", 0)
    hid_pct = min(hidratacao / 8, 1.0)

    col_hid, col_btn = st.columns([3, 1])
    with col_hid:
        st.markdown(f"**{hidratacao} / 8 garrafas** ({hidratacao * 500}ml / 4000ml)")
        st.progress(hid_pct)
    with col_btn:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕", use_container_width=True, key="hid_add") and hidratacao < 8:
                cardapio_state["hidratacao"] = hidratacao + 1
                save_fn(state)
                st.rerun()
        with c2:
            if st.button("➖", use_container_width=True, key="hid_rem") and hidratacao > 0:
                cardapio_state["hidratacao"] = hidratacao - 1
                save_fn(state)
                st.rerun()

    # Ícones de garrafas
    icons = "🫙" * hidratacao + "⬜" * (8 - hidratacao)
    st.markdown(f"<div style='font-size:1.5rem;letter-spacing:4px'>{icons}</div>", unsafe_allow_html=True)
