# streamlit_app.py
import io
import re
import nbformat
import pandas as pd
import streamlit as st

from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

from scraping.agent_arxiv import ArxivAgent
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
            max_results = st.slider("Número de resultados a consultar", min_value=1, max_value=100, value=10, step=1)
        with col2:
            sortby = st.selectbox("Ordenar por", options=["relevance", "lastUpdatedDate", "submittedDate"], index=0,format_func=lambda x: x)
        
        # Botón de envío del formulario
        submitted = st.form_submit_button("Buscar Artículos")
    
    # Si se envía el formulario (ya sea presionando el botón o con Enter)
    if submitted:
        with st.spinner("Buscando artículos..."):
            try:
                arxiv_agent = ArxivAgent()
                # Se pasa el parámetro 'sortby' según la selección realizada
                articles = arxiv_agent.fetch_articles(query=query_topic, max_results=max_results, sortby=sortby)
                for art in articles:
                    # Asegurarse de que los campos necesarios estén presentes
                    if 'abstract' in art and 'summary' not in art:
                        art['summary'] = art['abstract']
                    if 'url' in art and 'link_article' not in art:
                        art['link_article'] = art['url']
                    
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
            # Recuperamos o inicializamos el diccionario de resultados
            pdf_results = st.session_state.get("pdf_results", {})
            # Obtenemos los IDs (link_article) de la selección actual
            current_ids = set(art["link_article"] for art in st.session_state["selected_articles"])
            # Si hay resultados previos, eliminamos aquellos que ya no estén en la selección
            for key in list(pdf_results.keys()):
                if key not in current_ids:
                    del pdf_results[key]
            # Procesamos únicamente los artículos que aún no se han procesado
            for art in st.session_state["selected_articles"]:
                link = art["link_article"]
                if link not in pdf_results:
                    # Usamos 'pdf_url' en lugar de 'pdf_link' para coincidir con el campo del agente de Arxiv
                    pdf_url = art.get("pdf_url")
                    if pdf_url:
                        try:
                            filename = link.split("/")[-1] + ".pdf"
                            pdf_folder = "../input/papers"
                            pdf_path = download_pdf(pdf_url, pdf_folder, filename)
                            st.info(f"PDF descargado para **{art['title']}** en {pdf_path}")
                            with st.spinner("Pensando..."):
                                # Mostramos el resultado en un expander para este artículo
                                with st.expander(f"**{art['title']}**"):
                                    spinner_placeholder = st.empty()
                                    full_output, result = summarize_pdf(pdf_path, stream_placeholder=spinner_placeholder)
                                    spinner_placeholder.markdown(full_output)
                                    pdf_results[link] = [full_output, result]
                        except Exception as e:
                            st.error(f"Error procesando PDF para {art['title']}: {e}")
                    else:
                        st.warning(f"No se encontró PDF para {art['title']}")
            st.session_state["pdf_results"] = pdf_results
            st.success("Extracción de Ideas y Conceptos completada.")
        else:
            # Si ya se han extraído resultados, se muestran en sus expanders correspondientes.
            if "pdf_results" in st.session_state:
                for art in st.session_state["selected_articles"]:
                    link = art["link_article"]
                    if link in st.session_state["pdf_results"]:
                        with st.expander(f"**{art['title']}**"):
                            st.markdown(st.session_state["pdf_results"][link][0])
        
    # ---------- Fase 4: Medir congruencias entre Secciones (Comparación de ideas) ----------
    if st.session_state.get("pdf_results"):
        st.header("4. Evaluar Congruencia entre Artículos")
        
        # Comparamos la selección actual con la que se usó la última vez para la congruencia.
        current_ids = set(art["link_article"] for art in st.session_state["selected_articles"])
        # Si se cambia la selección, reiniciamos el resultado de congruencia para forzar el reprocesamiento.
        if st.session_state.get("congruence_selected_ids", set()) != current_ids:
            st.session_state["congruence_selected_ids"] = current_ids
            st.session_state.pop("congruence_result", None)
    
        if st.button("Comparar Ideas y Conceptos"):
            with st.spinner("Comparando ideas y conceptos..."):
                with st.expander("**Comparación Entre Artículos**"):
                    cong_placeholder = st.empty()
                    # Aquí se procesa la congruencia usando los resultados actuales de PDF.
                    full_c_output, congruence_result = check_congruence(st.session_state["pdf_results"], stream_placeholder=cong_placeholder)
                    cong_placeholder.markdown(full_c_output)
                    st.session_state["congruence_result"] = [full_c_output, congruence_result]
            st.success("Comparación completada.")
        else:
            # Si ya se ha calculado la congruencia, se muestra en un expander.
            if "congruence_result" in st.session_state:
                with st.expander("**Comparación**"):
                    st.markdown(st.session_state["congruence_result"][0])

    # ---------- Fase 5: Construir JSON de Notebook con info Consolidada ----------
    if (st.session_state.get("selected_articles") and 
        st.session_state.get("pdf_results") and 
        st.session_state.get("congruence_result")):
        
        st.header("5. Consolidar Información y Generar Notebook Final")
        
        # Si se pulsa el botón, se genera la información consolidada y el notebook
        if st.button("Consolidar Información y Generar Notebook Final"):
            
            # Construir el texto unificado consolidado
            unified_text = "### Material Educativo Consolidado\n\n"
            cong = st.session_state["congruence_result"][1]
            unified_text += f"**Conclusión de Congruencia:** {cong.get('conclusion', 'No se encontró relación')}\n\n"
            unified_text += f"**Detalles:** {cong.get('details', '')}\n\n"
            
            for art in st.session_state["selected_articles"]:
                art_id = art["link_article"]
                summary = st.session_state["pdf_results"].get(art_id, {})[1]
                unified_text += f"## {art['title']}\n\n"
                # Recorrer cada clave del resumen extraído (omitimos 'chain_of_thought' si existe)
                for key, values in summary.items():
                    if key.lower() != "chain_of_thought":
                        if isinstance(values, list):
                            unified_text += f"**{key.capitalize()}:** {', '.join(values)}\n\n"
                        else:
                            unified_text += f"**{key.capitalize()}:** {values}\n\n"
                # Ejemplo de código para ilustrar la implementación
                unified_text += "\n```python\n# Ejemplo de implementación:\nprint('Ejemplo de código para material educativo')\n```\n\n"
            
            # Guardamos el texto unificado en el estado para conservarlo
            st.session_state["unified_text"] = unified_text
            st.success("Información consolidada.")
            
            # Mostrar el texto unificado en un expander permanente
            with st.expander("**Ver Texto Unificado**"):
                st.text_area("Texto Unificado", unified_text, height=300)
            
            # Generar el notebook JSON usando un spinner (fuera del expander)
            with st.spinner("Generando Notebook..."):
                with st.expander("**Notebook Unificado**"):
                    cong_placeholder = st.empty()
                    full_n_output, notebook_json = join_ideas(unified_text, stream_placeholder=cong_placeholder)
                    st.session_state["notebook_json"] = [full_n_output, notebook_json]
                    cong_placeholder.markdown(full_n_output)
                
        else:
            # Si ya se ha procesado previamente, se muestran los resultados guardados
            
            if "unified_text" in st.session_state:
                with st.expander("Ver Texto Unificado"):
                    st.text_area("Texto Unificado", st.session_state["unified_text"], height=300)
            
            if "notebook_json" in st.session_state:
                with st.expander("**Notebook Unificado**"):
                    st.markdown(st.session_state["notebook_json"][0])
                
    # ---------- Fase 6: Generar Notebook Consolidado ----------
    if (st.session_state.get("selected_articles") and 
    st.session_state.get("pdf_results") and
    st.session_state.get("notebook_json")):
        st.header("6. Generar Notebook Consolidado")
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
                    notebook_json=st.session_state["notebook_json"][1]
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
