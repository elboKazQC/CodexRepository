#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger le fichier runner_fixed_new.py
"""

import os
import re
import sys

def fix_indentation(file_path):
    """
    Corrige l'indentation de la fonction main() dans le fichier spécifié
    """
    print(f"Correction du fichier: {file_path}")
    
    # Lire le contenu du fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Faire une copie de sauvegarde
    backup_path = file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Sauvegarde créée: {backup_path}")
    
    # Corriger l'indentation de la fonction main()
    pattern = r'# Redéfinir la fonction main pour qu\'elle soit correctement exportable\ndef main\(\):'
    replacement = '\n\n# Redéfinir la fonction main pour qu\'elle soit correctement exportable\ndef main():'
    
    # Trouver les positions des méthodes de classe et de la fonction main
    new_content = re.sub(pattern, replacement, content)
    
    # Écrire le contenu corrigé
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Correction terminée avec succès.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "runner_fixed_new.py"
    
    if os.path.exists(file_path):
        success = fix_indentation(file_path)
        if success:
            print(f"Le fichier {file_path} a été corrigé avec succès.")
            print("Vous pouvez maintenant exécuter la commande:")
            print(f"python {file_path}")
        else:
            print(f"Erreur lors de la correction du fichier {file_path}")
    else:
        print(f"Le fichier {file_path} n'existe pas.")
