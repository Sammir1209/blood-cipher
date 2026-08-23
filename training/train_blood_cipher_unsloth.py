# ==============================================================================
# Blood-Cipher v1.5 - Script de Fine-Tuning con Unsloth (Google Colab / GPU T4)
# ==============================================================================
# Este script está optimizado para ejecutarse en Google Colab con GPU gratuita (T4)
# Entrena un modelo base (Llama-3-8B o Qwen2.5-Coder-7B) con LoRA y lo exporta a GGUF
# para usarlo directamente en Ollama con Blood-Cipher.
# ==============================================================================

# 1. Instalación de Unsloth y dependencias (ejecutar en Colab):
# !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
# !pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes

import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Parámetros del Modelo
MAX_SEQ_LENGTH = 2048
DTYPE = None  # None para auto-detección (Float16 en T4, Bfloat16 en Ampere/A100)
LOAD_IN_4BIT = True  # 4bit quantization para ahorrar 70% de VRAM

# Modelo base recomendado (muy rápido y potente para código y comandos)
MODEL_NAME = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
# Alternativa: "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"

print(f"[*] Cargando modelo base: {MODEL_NAME}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
)

# 2. Configurar LoRA / QLoRA
print("[*] Configurando adaptadores LoRA...")
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # Rango de LoRA (8, 16, 32, 64)
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,  # Optimizado a 0 en Unsloth
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# 3. Formateo de Datos (ChatML / ShareGPT / Llama-3 Template)
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="llama-3")

def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return {"text": texts}

# Cargar dataset local o subido a Colab
print("[*] Cargando dataset de Blood-Cipher...")
dataset = load_dataset("json", data_files="blood_cipher_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched=True)

# 4. Entrenador SFTTrainer
print("[*] Iniciando entrenamiento...")
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,  # Ajustar entre 60 y 200 según tamaño del dataset
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

trainer_stats = trainer.train()
print("[✓] ¡Entrenamiento completado!")

# 5. Exportar modelo a formato GGUF para Ollama (Q4_K_M o Q8_0)
print("[*] Exportando modelo a GGUF (4-bit Q4_K_M) para Ollama...")
model.save_pretrained_gguf("blood_cipher_model", tokenizer, quantization_method="q4_k_m")
print("[✓] Archivo GGUF generado en: blood_cipher_model/")
print("[*] Descarga el archivo .gguf a tu máquina para usarlo con Ollama.")
