// Servicio para extracción de ideas/conceptos de artículos seleccionados

const extractionService = {
  async extractIdeas(article: { pdf_url?: string; id: string }) {
    if (!article.pdf_url) {
      return { error: 'No hay PDF disponible para este artículo.' };
    }
    try {
      const formData = new FormData();
      formData.append('pdf_url', article.pdf_url);
      const res = await fetch('http://localhost:8100/extract-ideas', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        return { error: 'Error al extraer ideas del backend.' };
      }
      return await res.json();
    } catch (e) {
      return { error: 'Error de red al extraer ideas.' };
    }
  }
};

export default extractionService;
