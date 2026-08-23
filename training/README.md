# 🧠 Blood-Cipher — Pipeline de Entrenamiento y Fine-Tuning de IA

Esta carpeta contiene todo el pipeline necesario para entrenar un modelo de Inteligencia Artificial propio y personalizado para **Blood-Cipher** de forma 100% gratuita utilizando Google Colab (GPU T4) y ejecutarlo de forma local y offline con **Ollama**.

---

## 📁 Archivos Incluidos

- [`dataset_generator.py`](dataset_generator.py): Script en Python para generar y expandir el dataset de entrenamiento en formato JSONL (`blood_cipher_dataset.jsonl`).
- [`train_blood_cipher_unsloth.py`](train_blood_cipher_unsloth.py): Script optimizado para Google Colab con **Unsloth (QLoRA)** para ajustar modelos como `Llama-3.1-8B-Instruct` o `Qwen2.5-Coder-7B` y exportarlos a formato `.gguf`.
- [`Modelfile`](Modelfile): Archivo de manifiesto para importar el modelo `.gguf` en **Ollama**.
- [`blood_cipher_dataset.jsonl`](blood_cipher_dataset.jsonl): Dataset estructurado listo para entrenar.

---

## 🚀 Guía Paso a Paso

### Paso 1: Personalizar / Expandir el Dataset (Opcional)
Para agregar nuevos ejemplos de comandos o respuestas:
1. Abre `dataset_generator.py` y añade nuevos ejemplos a la lista `TRAINING_SAMPLES`.
2. Ejecuta:
   ```bash
   python training/dataset_generator.py
   ```
   Esto generará el archivo `blood_cipher_dataset.jsonl`.

---

### Paso 2: Entrenar en Google Colab (Gratis con GPU)
1. Abre [Google Colab](https://colab.research.google.com/).
2. Ve a **Entorno de ejecución** -> **Cambiar tipo de entorno de ejecución** -> Selecciona **GPU T4** (gratuita).
3. Sube los archivos `train_blood_cipher_unsloth.py` y `blood_cipher_dataset.jsonl` a la sesión de Colab.
4. En una celda de código, instala Unsloth:
   ```bash
   !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   !pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes
   ```
5. Ejecuta el script de entrenamiento:
   ```bash
   !python train_blood_cipher_unsloth.py
   ```
6. Al finalizar (toma entre 15 y 30 minutos), Unsloth generará una carpeta con el archivo cuantizado:
   - `blood_cipher_model/blood-cipher-q4_k_m.gguf`
7. Descarga el archivo `.gguf` a tu máquina.

---

### Paso 3: Registrar el Modelo en Ollama Local
1. Coloca el archivo `.gguf` descargado dentro de esta carpeta `training/` (con el nombre `blood-cipher-q4_k_m.gguf`).
2. Abre tu terminal y ejecuta:
   ```bash
   ollama create blood-cipher -f training/Modelfile
   ```
3. Verifica que el modelo esté creado:
   ```bash
   ollama list
   ```

---

### Paso 4: Conectar el Modelo a Blood-Cipher
Abre la configuración de Blood-Cipher:
```bash
blood-cipher config
```
1. Selecciona: **Ollama (100% Local / Offline)**.
2. Escribe el nombre del modelo: **`blood-cipher`**.
3. ¡Listo! A partir de ese momento, Blood-Cipher utilizará tu propio modelo entrenado de forma 100% offline y sin ninguna restricción externa.
