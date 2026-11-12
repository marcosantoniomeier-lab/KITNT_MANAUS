from pathlib import Path

for arq in Path(".").rglob("*.py"):
    if arq.name == "corrigir_encoding.py":
        continue
    dados = arq.read_bytes()
    try:
        texto = dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = dados.decode("cp1252")
    arq.write_text(texto, encoding="utf-8", newline="")
    print("OK:", arq)
