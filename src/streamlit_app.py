# streamlit_app.py
import io
import os
import re
import nbformat
import pandas as pd
import streamlit as st

from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

from agent_arxiv import ArxivAgent
from agent_summarizer import summarize_pdf
from agent_congruence import check_congruence
from agent_filter import join_ideas
from agent_manager import AgentManager, download_pdf

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def highlight_text(text, query):
    words = query.split()
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub(lambda m: f"<mark style='background-color: yellow; color: black;'>{m.group(0)}</mark>", text)
    return text

def generate_html_from_notebook(nb_json):
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

    # ------------ Cabeceras ----------
    st.set_page_config(page_title="Alejandría",layout="centered", initial_sidebar_state="auto", menu_items=None)
    st.markdown("<h1 style='text-align: center; color: white;'>Alejandría</h1>", unsafe_allow_html=True)
    st.write("Extrae artículos de arXiv, obtiene resúmenes pedagógicos, compara congruencias y genera un notebook final de Autoaprendizaje.")

    # ---------- Fase 1: Búsqueda de artículos ----------
    st.header("1. Buscar Artículos Científicos")
    # Usar un formulario para que se pueda enviar con Enter
    with st.form(key="search_form"):
        # Campo de texto para la consulta; al presionar Enter se enviará el formulario
        query_topic = st.text_input("Tema de búsqueda en arXiv", "RAPTOR Information Retrieval")
        
        # Dividir el espacio en dos columnas: una para el slider y otra para el selectbox de ordenamiento
        col1, col2 = st.columns(2)
        with col1:
            max_results = st.slider("Número de resultados a consultar", min_value=1, max_value=20, value=10, step=1)
        with col2:
            sortby = st.selectbox("Ordenar por", options=["relevance", "lastUpdatedDate", "submittedDate"], index=0,format_func=lambda x: x)
        
        # Botón de envío del formulario
        submitted = st.form_submit_button("Buscar Artículos")
    
    # Si se envía el formulario (ya sea presionando el botón o con Enter)
    if submitted:
        with st.spinner("Buscando artículos..."):
            try:
                agent = ArxivAgent()
                # Se pasa el parámetro 'sortby' según la selección realizada
                articles = agent.fetch_articles(query=query_topic, max_results=max_results, sortby=sortby)
                for art in articles:
                    art["summary_highlight"] = highlight_text(art.get("summary", ""), query_topic)
                    if isinstance(art.get("link_article"), str):
                        art["link_article"] = art["link_article"].rstrip("/")
                st.session_state["articles"] = articles
                st.success(f"Se encontraron {len(articles)} artículos.")
            except Exception as e:
                st.error(f"Error al buscar artículos: {e}")

    # ---------- Fase 2: Seleccionar Artículos ----------
    if st.session_state.get("articles"):
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
            # Reconstruir la lista de artículos respetando el orden de selección:
            selected_ids = df_selected["ID"].tolist()
            selected_articles = []
            for sel_id in selected_ids:
                for art in st.session_state["articles"]:
                    if art.get("link_article") == sel_id:
                        selected_articles.append(art)
                        break
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

    # ---------- Fase 3: Extraer Ideas (Descarga y Extracción de ideas y conceptos de PDFs) ----------
    if st.session_state.get("selected_articles"):
        st.header("3. Extraer Ideas y Conceptos")
        if st.button("Extraer Ideas y conceptos"):
            if "pdf_results" not in st.session_state:
                pdf_results = {}
                for art in st.session_state["selected_articles"]:
                    pdf_url = art["pdf_link"]
                    if pdf_url:
                        try:
                            filename = art["link_article"].split("/")[-1] + ".pdf"
                            pdf_folder = "../input/papers"
                            pdf_path = download_pdf(pdf_url, pdf_folder, filename)
                            st.info(f"PDF descargado para **{art['title']}** en {pdf_path}")
                            with st.spinner("Pensando..."):
                                with st.expander(f"**{art['title']}**"):
                                    # Creamos un placeholder para el spinner
                                    spinner_placeholder = st.empty()
                                    # Llamada a summarize_pdf que se encarga del streaming actual
                                    full_output, result = summarize_pdf(pdf_path, stream_placeholder=spinner_placeholder)
                                    spinner_placeholder.markdown(full_output)
                                    pdf_results[art["link_article"]] = [full_output, result]
                                    st.session_state["pdf_results"] = pdf_results
                        except Exception as e:
                            st.error(f"Error procesando PDF para {art['title']}: {e}")
                    else:
                        st.warning(f"No se encontró PDF para {art['title']}")
            else:
                # Si ya se procesaron, mostramos el expander con el resultado final (único por artículo)
                for art in st.session_state["selected_articles"]:
                    link = art["link_article"]
                    if link in st.session_state["pdf_results"]:
                        with st.expander(f"**{art['title']}**"):
                            st.markdown(st.session_state["pdf_results"][link][0])
            st.success("Extracción de Ideas y Conceptos completada.")
        else:
            if "pdf_results" in st.session_state:
                for art in st.session_state["selected_articles"]:
                    link = art["link_article"]
                    if link in st.session_state["pdf_results"]:
                        with st.expander(f"**{art['title']}**"):
                            st.markdown(st.session_state["pdf_results"][link][0])
        

    # ---------- Fase 4: Medir congruencias entre Secciones (Comparación de ideas) ----------
    if st.session_state.get("pdf_results"):
        st.header("4. Evaluar Congruencia entre Artículos")
        if st.button("Comparar Ideas y Conceptos"):
            with st.spinner("Comparando ideas y conceptos..."):
                with st.expander("**Comparación**"):
                    cong_placeholder = st.empty()
                    full_c_output, congruence_result = check_congruence(st.session_state["pdf_results"], stream_placeholder=cong_placeholder)
                    cong_placeholder.markdown(full_c_output)
                    st.session_state["congruence_result"] = congruence_result
            st.success("Comparación completada.")
            
    # ---------- Fase 5: Construir JSON de Notebook con info Consolidada ----------
    if (st.session_state.get("selected_articles") and 
        st.session_state.get("pdf_results") and 
        st.session_state.get("congruence_result")):
        st.header("Consolidar Información y Generar Notebook Final")
        if st.button("Consolidar Información y Generar Notebook Final"):
            # Construir el texto unificado consolidado
            unified_text = "### Material Educativo Consolidado\n\n"
            cong = st.session_state["congruence_result"]
            unified_text += f"**Conclusión de Congruencia:** {cong.get('conclusion', 'No se encontró relación')}\n\n"
            unified_text += f"**Detalles:** {cong.get('details', '')}\n\n"
            for art in st.session_state["selected_articles"]:
                art_id = art["link_article"]
                summary = st.session_state["pdf_results"].get(art_id, {})[1]
                #print(summary)
                unified_text += f"## {art['title']}\n\n"
                # Recorrer cada clave del resumen extraído
                for key, values in summary.items():
                    if key.lower() != "chain_of_thought":  # en caso de existir
                        if isinstance(values, list):
                            unified_text += f"**{key.capitalize()}:** {', '.join(values)}\n\n"
                        else:
                            unified_text += f"**{key.capitalize()}:** {values}\n\n"
                # Agregar un ejemplo de código para ejemplificar la implementación
                unified_text += "\n```python\n# Ejemplo de implementación:\nprint('Ejemplo de código para material educativo')\n```\n\n"
            st.session_state["unified_text"] = unified_text
            st.success("Información consolidada.")
            with st.expander("Ver Texto Unificado"):
                st.text_area("Texto Unificado", unified_text, height=300)

            with st.spinner("Generando Notebook..."):
                cong_placeholder = st.empty()
                notebook_json = join_ideas(st.session_state["unified_text"], stream_placeholder=cong_placeholder)
                print(notebook_json)
                st.session_state["notebook_json"] = notebook_json
                

    # ---------- Fase 3: Generar Notebook Consolidado ----------
    if (st.session_state.get("selected_articles") and 
    st.session_state.get("pdf_results") and
    st.session_state.get("notebook_json")):
        st.header("3. Generar Notebook Consolidado")
        if st.button("Generar Notebook Consolidado"):
            # Mapeo de repositorios (opcional)
            github_mapping = {}
            for art in st.session_state["selected_articles"]:
                key = art["link_article"]
                if art.get("github_link") and art.get("github_status") == "OK":
                    github_mapping[key] = art["github_link"]
                else:
                    github_mapping[key] = None
    
            manager = AgentManager()
            print(st.session_state["notebook_json"])
            with st.spinner("Generando notebook consolidado..."):
                # Usar la variable nb_json que se retorna
                nb_json, logs = manager.run_pipeline_multi(
                    st.session_state["selected_articles"],
                    github_mapping,
                    notebook_json=st.session_state["notebook_json"]
                )
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
