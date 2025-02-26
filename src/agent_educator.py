# agent_educator.py
import nbformat

def build_notebook_cells_from_sections(sections):
    """
    A partir de una lista de secciones (cada una es un diccionario con keys:
    'title', 'cell_type' (markdown o code), 'content'),
    construye una lista de celdas para el notebook.
    """
    cells = []
    for sec in sections:
        if sec.get("cell_type") == "code":
            cell = nbformat.v4.new_code_cell(sec.get("content", ""))
        else:
            # Por defecto, markdown
            cell = nbformat.v4.new_markdown_cell(sec.get("content", ""))
        # Opcional: incluir el título de la sección como encabezado (si se desea)
        if sec.get("title"):
            cell.source = f"### {sec['title']}\n\n" + cell.source
        cells.append(cell)
    return cells

def review_notebook_json(notebook_json):
    cells = notebook_json.get("cells", [])
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    markdown_cells = [cell for cell in cells if cell.get("cell_type") == "markdown"]
    review = {
        "code_cells": len(code_cells),
        "markdown_cells": len(markdown_cells),
        "status": "Aprobado" if code_cells and markdown_cells else "Revisar"
    }
    return review

# Prueba de Educator
if __name__ == "__main__":
    import nbformat
    cells = build_notebook_cells_from_sections([
        {"title": "Intro", "cell_type": "markdown", "content": "Contenido de introducción."},
        {"title": "Código", "cell_type": "code", "content": "print('Hola')"}
    ])
    nb = nbformat.v4.new_notebook()
    nb.cells = cells
    print(review_notebook_json(nb))
