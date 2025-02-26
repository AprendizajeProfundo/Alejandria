# streamlit_app.py
import streamlit as st
import pandas as pd
import nbformat
import io
import os

from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

from agent_arxiv import ArxivAgent
from agent_manager import AgentManager, download_pdf
from agent_filter import process_pdf

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def highlight_text(text, query):
    import re
    words = query.split()
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub(lambda m: f"<mark style='background-color: yellow; color: black;'>{m.group(0)}</mark>", text)
    return text

def generate_html_from_notebook(nb_json):
    from nbconvert import HTMLExporter
    html_exporter = HTMLExporter()
    html_exporter.template_name = 'classic'
    (body, _) = html_exporter.from_notebook_node(nb_json)
    return body

def execute_notebook(nb_json):
    from nbconvert.preprocessors import ExecutePreprocessor
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    try:
        ep.preprocess(nb_json, {'metadata': {'path': './'}})
    except Exception as e:
        st.error("Error ejecutando el notebook: " + str(e))
    return nb_json

def main():
    st.markdown("<h1 style='text-align: center; color: white;'>Alejandría</h1>", unsafe_allow_html=True)
    st.write("Extrae artículos de arXiv, obtiene resúmenes pedagógicos, compara congruencias y genera un notebook final de Autoaprendizaje.")

    # ---------- Fase 1: Búsqueda de artículos ----------
    st.header("1. Buscar Artículos")
    query_topic = st.text_input("Tema de búsqueda en arXiv", "RAG")
    max_results = st.slider("Número de resultados a consultar", min_value=1, max_value=20, value=10, step=1)
    if st.button("Buscar Artículos"):
        with st.spinner("Buscando artículos..."):
            try:
                agent = ArxivAgent()
                articles = agent.fetch_articles(query=query_topic, max_results=max_results)
                for art in articles:
                    art["summary_highlight"] = highlight_text(art.get("summary", ""), query_topic)
                    if isinstance(art.get("link_article"), str):
                        art["link_article"] = art["link_article"].rstrip("/")
                st.session_state["articles"] = articles
                st.success(f"Se encontraron {len(articles)} artículos.")
            except Exception as e:
                st.error(f"Error al buscar artículos: {e}")

    # ---------- Fase 2: Seleccionar Artículos ----------
    if "articles" in st.session_state:
        st.header("2. Seleccionar Artículos")
        df = pd.DataFrame(st.session_state["articles"])
        df["ID"] = df["link_article"]
        df["Título"] = df["title"]
        df["Publicado"] = df["published"]
        df["GitHub Link"] = df["github_link"].fillna("No link")
        df["GitHub Estado"] = df["github_status"].fillna("No link")
        df["Resumen"] = df["summary_highlight"]
        df_display = df[["ID", "Título", "Publicado", "GitHub Link", "GitHub Estado", "Resumen"]].copy()

        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_selection('multiple', use_checkbox=True, pre_selected_rows=[])
        gb.configure_default_column(sortable=True, filter=True)
        gb.configure_column("Resumen", cellRenderer='html')
        grid_options = gb.build()

        grid_response = AgGrid(
            df_display,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            allow_unsafe_jscode=True,
            height=400,
            fit_columns_on_grid_load=True,
        )
        selected = grid_response.get('selected_rows', [])
        if selected is not None and len(selected) > 0:
            st.write("**Artículos seleccionados:**")
            df_selected = pd.DataFrame(selected)
            st.dataframe(df_selected[["ID", "Título", "Publicado", "GitHub Link", "GitHub Estado", "Resumen"]])
            selected_ids = df_selected["ID"].tolist()
            selected_articles = [art for art in st.session_state["articles"] if art.get("link_article") in selected_ids]
            st.session_state["selected_articles"] = selected_articles
        else:
            st.session_state["selected_articles"] = []

        with st.expander("Ver detalles completos de los artículos seleccionados"):
            for art in st.session_state["selected_articles"]:
                st.markdown(f"### {art['title']}")
                st.markdown(f"**Publicado:** {art['published']}")
                st.markdown(f"**Resumen:** {art['summary_highlight']}", unsafe_allow_html=True)
                st.markdown(f"**GitHub Link:** {art['github_link'] if art.get('github_link') else 'No link'}")
                st.markdown(f"**GitHub Estado:** {art['github_status']}")
                st.markdown(f"**Autores:** {', '.join([a['name'] for a in art.get('authors', [])])}")
                st.markdown(f"**Link del artículo:** {art['link_article']}")
                st.markdown("---")

    # ---------- Fase 2.5: Extraer Secciones (Descarga y procesamiento de PDFs) ----------
    if st.session_state.get("selected_articles"):
        st.header("2.5. Extraer Secciones")
        if st.button("Extraer Secciones"):
            pdf_results = {}
            for art in st.session_state["selected_articles"]:
                pdf_url = art["pdf_link"]
                if pdf_url:
                    try:
                        filename = art["link_article"].split("/")[-1] + ".pdf"
                        pdf_folder = "../input/papers"
                        pdf_path = download_pdf(pdf_url, pdf_folder, filename)
                        st.info(f"PDF descargado para {art['title']}: {pdf_path}")
                        with st.expander("Streaming del Chain-of-Thought"):
                            llm_placeholder = st.empty()  # Placeholder para actualizar en streaming
                            result = process_pdf(pdf_path, stream_placeholder=llm_placeholder)
                            pdf_results[art["link_article"]] = result
                    except Exception as e:
                        st.error(f"Error procesando PDF para {art['title']}: {e}")
                else:
                        st.warning(f"No se encontró PDF para {art['title']}")
            st.session_state["pdf_results"] = pdf_results
            print(pdf_results)

    # ---------- Fase 3: Generar Notebook Consolidado ----------
    if st.session_state.get("selected_articles") and st.session_state.get("pdf_results"):
        st.header("3. Generar Notebook Consolidado")
        if st.button("Generar Notebook Consolidado"):
            github_mapping = {}
            for art in st.session_state["selected_articles"]:
                key = art["link_article"]
                if art.get("github_link") and art.get("github_status") == "OK":
                    github_mapping[key] = art["github_link"]
                else:
                    github_mapping[key] = None

            manager = AgentManager()
            with st.spinner("Generando notebook consolidado..."):
                nb_json, logs = manager.run_pipeline_multi(st.session_state["selected_articles"], github_mapping, pdf_results=st.session_state["pdf_results"])
                nb_json = execute_notebook(nb_json)
                notebook_filename = "Alejandria_Notebook_Consolidado.ipynb"
                with open(notebook_filename, "w", encoding="utf-8") as f:
                    nbformat.write(nb_json, f)
                st.success("Notebook generado y ejecutado exitosamente.")
                
                html_body = generate_html_from_notebook(nb_json)
                st.subheader("Notebook Renderizado")
                st.components.v1.html(html_body, height=800, scrolling=True)
                
                file_buffer = io.StringIO()
                nbformat.write(nb_json, file_buffer)
                notebook_str = file_buffer.getvalue()
                st.download_button("Descargar Notebook (.ipynb)", notebook_str,
                                   file_name=notebook_filename, mime="application/json")
                
                st.subheader("Eventos del Proceso")
                for log in logs:
                    st.text(log)

if __name__ == "__main__":
    main()
