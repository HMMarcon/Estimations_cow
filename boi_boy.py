import streamlit as st
import pandas as pd

st.set_page_config(page_title="Food & Seasons", layout="wide")


# ---------- INITIAL DATA & STATE ----------

def init_tables():
    if "table1" not in st.session_state:
        st.session_state["table1"] = pd.DataFrame(
            {
                "Comida": ["Suplemento Mineral", "Suplemento Mineral Adensado",
                           "Proteinado 0,1%", "Proteico energetico 0,3%",
                           "Proteico energetico 0,5%", "Ração 1,5%", "Dieta total 2,2%"
                           ],
                "Preco (R$/kg)": [1, 1, 1, 1, 1, 1, 1],
                "Consumo (/dia)":[0.03, 0.03, 0.001, 0.003, 0.005, 1.50/100, 2.20/100],
                "Engorda na agua (kg/dia)": [0.4, 0.5, 0.65, 0.8, 0.9, 1.2, 1.5],
                "Engorda na seca (kg/dia)": [0, 0.1, 0.15, 0.3, 0.4, 0.9, 1.5],
            }
        )

    if "n_entries" not in st.session_state:
        st.session_state["n_entries"] = 1

    # defaults para parâmetros gerais
    st.session_state.setdefault("peso_inicial", 210.0)
    st.session_state.setdefault("custo_boi", 3200.0)
    st.session_state.setdefault("custo_terra", 30*1.8)
    st.session_state.setdefault("n_cabecas", 20)
    st.session_state.setdefault("preco_kg_venda", 320/15)


init_tables()


# ---------- PAGE SELECTION ----------
title_1 = "Alimentos e Resultados"
title_2 = "Configurações"
page = st.sidebar.selectbox(
    "Selecione a página",
    [title_1, title_2],
)


# ---------- HELPER: LOOKUP FOOD ROW ----------

def get_food_row(food_name: str):
    df1 = st.session_state["table1"]

    row1 = df1[df1["Comida"] == food_name]
    if not row1.empty:
        return row1.iloc[0], "Tabela 1"

    return None, "Não encontrado"


# ---------- PAGE 1: INPUTS & RESULTS ----------

if page.startswith(title_1):
    st.title(title_1)

    col1, col2 = st.columns(2)

    # ---- LEFT: multiple food blocks ----
    with col1:
        st.subheader("Parâmetros")

        all_foods = (
            pd.concat(
                [st.session_state["table1"]["Comida"]]
            )
            .dropna()
            .unique()
        )

        if len(all_foods) == 0:
            st.warning("Adicione alimentos nas tabelas da página 2.")
        else:
            if st.button("Adicionar alimento"):
                st.session_state["n_entries"] += 1

            entries = []

            for i in range(st.session_state["n_entries"]):
                with st.container():
                    st.markdown(f"---")
                    st.markdown(f"**Alimento {i + 1}**")

                    food = st.selectbox(
                        "Alimento",
                        all_foods,
                        key=f"Comida_{i}",
                    )

                    phase = st.radio(
                        "Fase",
                        ["seca", "água"],
                        key=f"phase_{i}",
                        horizontal=True,
                    )

                    max_months = 6 if phase == "seca" else 11
                    prev_val = st.session_state.get(f"months_{i}", 0)
                    default_val = min(prev_val, max_months) if prev_val is not None else 0

                    months = st.slider(
                        "Meses",
                        min_value=0,
                        max_value=max_months,
                        value=default_val,
                        key=f"months_{i}",
                    )

                    entries.append(
                        {
                            "Comida": food,
                            "Phase": phase,
                            "Months": months,
                        }
                    )

    # ---- RIGHT: results ----
    with col2:
        st.subheader("Resultados")

        if len(all_foods) == 0:
            st.info("Sem alimentos definidos ainda.")
        else:
            # ler parâmetros gerais da sessão
            peso_inicial = float(st.session_state.get("peso_inicial", 0.0))
            custo_boi = float(st.session_state.get("custo_boi", 0.0))
            custo_terra = float(st.session_state.get("custo_terra", 0.0))
            n_cabecas = int(st.session_state.get("n_cabecas", 20))
            preco_kg_venda = float(st.session_state.get("preco_kg_venda", 1))

            results_rows = []
            total_seca = 0
            total_agua = 0

            total_food_cost = 0.0      # ∑ Preco * meses
            total_delta_peso = 0.0     # ∑ engorda_fase * meses

            for e in entries:
                food = e["Comida"]
                phase = e["Phase"]
                months = e["Months"]

                row, source = get_food_row(food)

                if row is not None:
                    preco = float(row["Preco (R$/kg)"])
                    n_comida = 30*row["Consumo (/dia)"]
                    if phase == "seca":
                        engorda = float(row["Engorda na seca (kg/dia)"])
                    else:
                        engorda = float(row["Engorda na agua (kg/dia)"])

                    food_cost = n_comida * preco * months
                    delta_peso = months * engorda * 30

                    total_food_cost += food_cost
                    total_delta_peso += delta_peso
                else:
                    food_cost = None
                    delta_peso = None

                if phase == "seca":
                    total_seca += months
                else:
                    total_agua += months

                results_rows.append(
                    {
                        "Comida": food,
                        "Fase": phase,
                        "Meses": months,
                        "Custo alimento (Preço x meses)": food_cost,
                        "Δ Peso (kg)": delta_peso,
                    }
                )

            # métricas agregadas
            total_meses = total_seca + total_agua
            custo_terra_total = total_meses * custo_terra
            custo_total = custo_terra_total + (total_food_cost + custo_boi) * n_cabecas
            peso_final = peso_inicial + total_delta_peso
            preco_venda = n_cabecas * peso_final * preco_kg_venda
            lucro = preco_venda - custo_total

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Numero de Cabeças", n_cabecas)

                st.metric(
                    "Peso final do boi (kg)",
                    round(peso_final, 2),
                    delta=round(total_delta_peso, 2),
                    help="Peso inicial + ∑(engorda_na_fase × meses)",
                )

            with c2:

                st.metric(
                    "Custo total",
                    round(custo_total, 2),
                )
            with c3:
                st.metric("Total meses (seca + água)", total_meses)

                st.metric(
                    "Lucro total por cabeça",
                    lucro/n_cabecas,
                    delta=round((lucro - custo_total)/n_cabecas, 2),
                    #help="Peso inicial + ∑(engorda_na_fase × meses)",
                )

            st.markdown("### Detalhamento por alimento")
            results_df = pd.DataFrame(results_rows)
            st.dataframe(results_df, use_container_width=True)


# ---------- PAGE 2: TABLES (EDITABLE) ----------

elif page.startswith(title_2):
    st.markdown("### Parâmetros gerais")
    col1, col2 = st.columns([3, 10])

    with col1:
        peso_inicial = st.number_input(
            "Peso inicial do boi (kg)",
            min_value=0.0,
            value=float(st.session_state.get("peso_inicial", 300.0)),
            step=1.0,
        )
        st.session_state["peso_inicial"] = peso_inicial

        custo_boi = st.number_input(
            "Custo do boi (R$/cabeça)",
            min_value=0.0,
            value=float(st.session_state.get("custo_boi", 0.0)),
            step=10.0,
        )
        st.session_state["custo_boi"] = custo_boi

        custo_terra = st.number_input(
            "Custo da terra (R$/mês)",
            min_value=0.0,
            value=float(st.session_state.get("custo_terra", 0.0)),
            step=1.0,
        )
        st.session_state["custo_terra"] = custo_terra

        n_cabecas = st.number_input(
            "Numero de cabeças",
            min_value=1,
            value=int(st.session_state.get("n_cabecas", 20)),
            step=1,
        )
        st.session_state["n_cabecas"] = n_cabecas

        preco_kg_venda = st.number_input(
            "Preço de venda (R$/kg)",
            min_value=1.0,
            value=float(st.session_state.get("preco_kg_venda", 1.0)),
            step=1.0,
        )
        st.session_state["preco_kg_venda"] = preco_kg_venda

    with col2:
        st.subheader("Custo e engorda por alimento")
        edited_table1 = st.data_editor(
            st.session_state["table1"],
            num_rows="dynamic",
            use_container_width=True,
            key="editor1",
        )
        st.session_state["table1"] = edited_table1


