import spacy

nlp = spacy.load("pt_core_news_lg")

textos_teste = [
    "Plano revisto por João Silva",
    "O João Silva revisou o plano",
    "João Silva fez a revisão",
    "Contactar Maria Santos para aprovação"
]

for texto in textos_teste:
    doc = nlp(texto)
    print(f"\n📝 Texto: {texto}")
    print(f"   Entidades detectadas: {[(ent.text, ent.label_) for ent in doc.ents]}")