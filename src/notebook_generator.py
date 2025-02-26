# notebook_generator.py
import nbformat

def create_notebook_json(cells):
    """
    Crea un notebook a partir de una lista de celdas.
    """
    nb = nbformat.v4.new_notebook()
    nb.cells = cells
    return nb

# Prueba de Notebook Generator
if __name__ == "__main__":
    import nbformat
    from agent_educator import build_notebook_cells_from_sections
    sections = [
        {"title": "Ejemplo", "cell_type": "markdown", "content": "Contenido teórico."},
        {"title": "Código", "cell_type": "code", "content": "print('Hola')"}
    ]
    cells = build_notebook_cells_from_sections(sections)
    nb = create_notebook_json(cells)
    print(nb)
