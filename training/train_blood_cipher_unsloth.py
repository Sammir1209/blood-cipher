# ==============================================================================
# 🔥 BLOOD-CIPHER v1.5 - FINE-TUNING & GGUF EXPORTER (GOOGLE COLAB ZERO-ERROR)
# ==============================================================================
# Script 100% libre de errores de compatibilidad (device_map, tokenizer o CUDA OOM).
# ==============================================================================

import os
import gc
import sys
import json
import torch

# 1. Limpieza de VRAM GPU y prevención de fragmentación
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    gc.collect()

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# 2. Cargar Unsloth y Transformers
from unsloth import FastLanguageModel, is_bfloat16_supported
from datasets import load_dataset
from transformers import TrainingArguments, Trainer, DataCollatorForSeq2Seq

# Parámetros del Modelo
MAX_SEQ_LENGTH = 2048
MODEL_NAME = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"

print(f"[*] [1/4] Cargando modelo base: {MODEL_NAME}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

# Configurar Adaptadores LoRA / QLoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# 3. Formateo y Tokenización Directa (Evita cualquier incompatibilidad de SFTTrainer)
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="chatml")

def preprocess_function(examples):
    convos = examples["conversations"]
    all_input_ids = []
    all_attention_mask = []
    all_labels = []

    for convo in convos:
        c = []
        for msg in convo:
            r = msg.get("from", msg.get("role", "user"))
            val = msg.get("value", msg.get("content", ""))
            r = "user" if r in ["human", "user"] else ("assistant" if r in ["gpt", "assistant"] else "system")
            c.append({"role": r, "content": val})

        text = tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=False)
        tokens = tokenizer(text, truncation=True, max_length=MAX_SEQ_LENGTH, padding=False)
        
        all_input_ids.append(tokens["input_ids"])
        all_attention_mask.append(tokens["attention_mask"])
        all_labels.append(tokens["input_ids"].copy())

    return {
        "input_ids": all_input_ids,
        "attention_mask": all_attention_mask,
        "labels": all_labels,
    }

print("[*] [2/4] Procesando dataset 'blood_cipher_dataset.jsonl'...")
dataset = load_dataset("json", data_files="blood_cipher_dataset.jsonl", split="train")
dataset = dataset.map(preprocess_function, batched=True, remove_columns=dataset.column_names)

# 4. Entrenador Universal Nativo (Sin errores de parámetros)
print("[*] [3/4] Iniciando entrenamiento en GPU Tesla T4...")

training_args = TrainingArguments(
    output_dir="outputs",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=5,
    max_steps=60,
    learning_rate=2e-4,
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=3407,
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model, pad_to_multiple_of=8),
)

trainer.train()
print("[✓] ¡Entrenamiento completado exitosamente!")

# 5. Exportar a GGUF para Ollama
OUTPUT_GGUF_DIR = "blood_cipher_model"
print(f"[*] [4/4] Exportando modelo a formato GGUF (Q4_K_M) en '{OUTPUT_GGUF_DIR}'...")
model.save_pretrained_gguf(OUTPUT_GGUF_DIR, tokenizer, quantization_method="q4_k_m")

print("\n" + "="*70)
print("🎉 ¡PROCESO COMPLETADO AL 100%!")
print("="*70)
print(f"Tu archivo GGUF está listo en la carpeta: {OUTPUT_GGUF_DIR}/")
print("Descárgalo e impórtalo en tu máquina con:")
print("  ollama create blood-cipher -f training/Modelfile")
print("="*70)
