# -*- coding: utf-8 -*-
# fix_main.py - Script pour corriger l'erreur de syntaxe dans main.py

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Recherche la ligne problématique et la corrige
for i in range(len(lines)):
    if 'message += f"Type' in lines[i] and lines[i].strip().endswith('Type'):
        # Remplacer la ligne incomplète par la ligne corrigée
        lines[i] = 'message += f"Type de radio: {data[\'radio_type\']}\\n"\n'
        break

# Écrit le fichier corrigé
with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Correction terminée. Le fichier main.py a été mis à jour.")