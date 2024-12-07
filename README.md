#  Alexandria: Building an Autonomous and Cooperative Artificial Intelligence Academic High-Quality Library

![alejandria](./figures/logo_alejandria.png)

Este repositorio tiene como objetivo la construcción de una biblioteca autónoma potenciada con IA, que permita destilar el conocimiento científico en material educativo de muy alta calidad, así como la generación automática de conocimiento en temas de inteligencia artificial, y en un futuro, de todo el conocimiento humano. Inspirada en la [Biblioteca de Alejandría](https://en.wikipedia.org/wiki/Library_of_Alexandria).

---

## **Requisitos**

Antes de ejecutar el repositorio, asegúrate de cumplir con los siguientes requisitos:

1. **Clonar el repositorio**:
    ```bash
    git clone https://github.com/AprendizajeProfundo/Alejandria.git
    ```

2. **Cambiar al directorio del repositorio**:
    ```bash
    cd Alejandria
    ```

3. **Crear un entorno virtual** (opcional pero recomendado):
    - Si usas `conda`:
      ```bash
      conda env create -f requirements.yml
      ```
    - Si usas `virtualenv` o `venv`:
      ```bash
      python -m venv venv
      source venv/bin/activate  # Para Linux/Mac
      venv\Scripts\activate     # Para Windows
      pip install -r requirements.txt
      ```

4. **Activar el entorno** (si usas conda):
    ```bash
    conda activate alejandria
    ```

---

## **Variables de Entorno**

Asegúrate de tener un archivo `.env` en el directorio raíz del proyecto con las siguientes variables configuradas:

```env
OPENAI_API_KEY=PONER_OPENAI_API_KEY_AQUI
OLLAMA_API_KEY=ollama
CEREBR_API_KEY=PONER_CEREBRAS_API_KEY_AQUI
GROQ__API__KEY=PONER_GROQ_API_KEY_AQUI

OLLAMA_HOST=http://localhost:11434/v1
CEREBR_HOST=https://api.cerebras.ai/v1
```
El archivo `.env.example` te dará una plantilla sobre la que puedas poner tus API Keys de manera segura.

---

## **Contribuciones**

Las contribuciones son bienvenidas. Siéntete libre de abrir un issue o enviar un pull request.

---

## **Licencia**

Este proyecto está bajo la [licencia Apache 2.0](https://opensource.org/license/apache-2-0).

---

¡Disfruta usando `Alejandria` para aprender de manera continua y entender el fabuloso mundo del autoaprendizaje! Si tienes preguntas o encuentras algún problema, no dudes en abrir un issue en el repositorio.

---