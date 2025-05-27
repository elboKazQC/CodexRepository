#!/usr/bin/env python

import re
import sys

def add_error_handling_to_file(file_path):
    """Ajoute une gestion d'erreur aux fonctions de navigation du fichier."""

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Correction 1: Fonction go_to_start
    pattern1 = r'def go_to_start\(self\):\s+"""Va au début des données"""\s+self\.is_real_time = False\s+self\.realtime_var\.set\(False\)\s+self\.current_view_start = 0\s+self\.update_display\(\)\s+self\.update_position_info\(\)'
    replacement1 = '''def go_to_start(self):
        """Va au début des données"""
        try:
            self.is_real_time = False
            self.realtime_var.set(False)
            self.current_view_start = 0
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_to_start: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern1, replacement1, content)

    # Correction 2: Fonction go_to_end
    pattern2 = r'def go_to_end\(self\):\s+"""Va à la fin des données"""\s+if self\.samples:\s+self\.current_view_start = max\(0, len\(self\.samples\) - self\.current_view_window\)\s+self\.update_display\(\)\s+self\.update_position_info\(\)'
    replacement2 = '''def go_to_end(self):
        """Va à la fin des données"""
        try:
            if self.samples:
                self.current_view_start = max(0, len(self.samples) - self.current_view_window)
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_to_end: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern2, replacement2, content)

    # Correction 3: Fonction go_previous
    pattern3 = r'def go_previous\(self\):\s+"""Recule dans le temps"""\s+self\.is_real_time = False\s+self\.realtime_var\.set\(False\)\s+step = max\(1, self\.current_view_window // 4\)\s+self\.current_view_start = max\(0, self\.current_view_start - step\)\s+self\.update_display\(\)\s+self\.update_position_info\(\)'
    replacement3 = '''def go_previous(self):
        """Recule dans le temps"""
        try:
            self.is_real_time = False
            self.realtime_var.set(False)
            step = max(1, self.current_view_window // 4)
            self.current_view_start = max(0, self.current_view_start - step)
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_previous: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern3, replacement3, content)

    # Correction 4: Fonction go_next
    pattern4 = r'def go_next\(self\):\s+"""Avance dans le temps"""\s+self\.is_real_time = False\s+self\.realtime_var\.set\(False\)\s+if self\.samples:\s+step = max\(1, self\.current_view_window // 4\)\s+max_start = max\(0, len\(self\.samples\) - self\.current_view_window\)\s+self\.current_view_start = min\(max_start, self\.current_view_start \+ step\)\s+self\.update_display\(\)\s+self\.update_position_info\(\)'
    replacement4 = '''def go_next(self):
        """Avance dans le temps"""
        try:
            self.is_real_time = False
            self.realtime_var.set(False)
            if self.samples:
                step = max(1, self.current_view_window // 4)
                max_start = max(0, len(self.samples) - self.current_view_window)
                self.current_view_start = min(max_start, self.current_view_start + step)
            self.update_display()
            self.update_position_info()
        except Exception as e:
            logging.error(f"Erreur dans go_next: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern4, replacement4, content)

    # Correction 5: Fonction pause_navigation
    pattern5 = r'def pause_navigation\(self\):\s+"""Met en pause/reprend la navigation automatique"""\s+self\.is_real_time = not self\.is_real_time\s+self\.realtime_var\.set\(self\.is_real_time\)'
    replacement5 = '''def pause_navigation(self):
        """Met en pause/reprend la navigation automatique"""
        try:
            self.is_real_time = not self.is_real_time
            self.realtime_var.set(self.is_real_time)
        except Exception as e:
            logging.error(f"Erreur dans pause_navigation: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern5, replacement5, content)

    # Correction 6: Fonction update_position_info
    pattern6 = r'def update_position_info\(self\):\s+"""Met à jour l\'info de position"""\s+if self\.samples:\s+total = len\(self\.samples\)\s+start = self\.current_view_start \+ 1\s+end = min\(total, self\.current_view_start \+ self\.current_view_window\)\s+self\.position_label\.config\(text=f"Position: {start}-{end}/{total} échantillons"\)'
    replacement6 = '''def update_position_info(self):
        """Met à jour l'info de position"""
        try:
            if self.samples:
                total = len(self.samples)
                start = self.current_view_start + 1
                end = min(total, self.current_view_start + self.current_view_window)
                self.position_label.config(text=f"Position: {start}-{end}/{total} échantillons")
        except Exception as e:
            logging.error(f"Erreur dans update_position_info: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern6, replacement6, content)

    # Correction 7: Améliorer la fonction update_display pour utiliser une copie des échantillons
    pattern7 = r'def update_display\(self\):\s+"""Met à jour les graphiques avec navigation temporelle""".*?# Déterminer la plage d\'affichage selon le mode\s+if self\.is_real_time:\s+# Mode temps réel : afficher les derniers échantillons\s+start_idx = max\(0, len\(self\.samples\) - self\.current_view_window\)\s+end_idx = len\(self\.samples\)\s+else:\s+# Mode navigation : afficher la fenêtre sélectionnée\s+start_idx = self\.current_view_start\s+end_idx = min\(len\(self\.samples\), start_idx \+ self\.current_view_window\)\s+# Extraire les données à afficher\s+display_samples = self\.samples\[start_idx:end_idx\]'
    replacement7 = '''def update_display(self):
        """Met à jour les graphiques avec navigation temporelle"""
        if not self.samples:
            return

        try:
            # Créer une copie locale des échantillons pour éviter les problèmes
            # de concurrence lorsque la liste est modifiée pendant la navigation
            samples_snapshot = list(self.samples)

            # Déterminer la plage d'affichage selon le mode
            if self.is_real_time:
                # Mode temps réel : afficher les derniers échantillons
                start_idx = max(0, len(samples_snapshot) - self.current_view_window)
                end_idx = len(samples_snapshot)
            else:
                # Mode navigation : afficher la fenêtre sélectionnée
                start_idx = self.current_view_start
                end_idx = min(len(samples_snapshot), start_idx + self.current_view_window)

            # Extraire les données à afficher
            display_samples = samples_snapshot[start_idx:end_idx]'''
    content = re.sub(pattern7, replacement7, content)

    # Correction 8: Améliorer la fonction mark_alerts_on_graphs pour utiliser une copie des échantillons
    pattern8 = r'def mark_alerts_on_graphs\(self\):\s+"""Marque les points d\'alerte sur les graphiques""".*?# Déterminer la plage d\'affichage\s+if self\.is_real_time:\s+start_idx = max\(0, len\(self\.samples\) - self\.current_view_window\)\s+else:\s+start_idx = self\.current_view_start\s+# Marquer les points avec alertes\s+for i, sample in enumerate\(self\.samples\[start_idx:start_idx \+ self\.current_view_window\]\):'
    replacement8 = '''def mark_alerts_on_graphs(self):
        """Marque les points d'alerte sur les graphiques"""
        try:
            # Effacer les anciens marqueurs
            for marker in self.alert_markers:
                try:
                    marker.remove()
                except:
                    pass
            self.alert_markers = []

            if not self.samples:
                return

            # Créer une copie locale des échantillons pour éviter les problèmes de concurrence
            samples_snapshot = list(self.samples)

            # Déterminer la plage d'affichage
            if self.is_real_time:
                start_idx = max(0, len(samples_snapshot) - self.current_view_window)
            else:
                start_idx = self.current_view_start

            # S'assurer que les indices sont valides
            end_idx = min(len(samples_snapshot), start_idx + self.current_view_window)

            # Marquer les points avec alertes
            for i, sample in enumerate(samples_snapshot[start_idx:end_idx]):'''
    content = re.sub(pattern8, replacement8, content)

    # Ajouter le bloc try/except à la fin de mark_alerts_on_graphs
    pattern9 = r'if has_alert:\s+# Marquer sur les deux graphiques\s+marker1 = self\.ax1\.axvline\(x=i, color=\'red\', alpha=0\.5, linewidth=1\)\s+marker2 = self\.ax2\.axvline\(x=i, color=\'red\', alpha=0\.5, linewidth=1\)\s+self\.alert_markers\.extend\(\[marker1, marker2\]\)'
    replacement9 = '''if has_alert:
                # Marquer sur les deux graphiques
                marker1 = self.ax1.axvline(x=i, color='red', alpha=0.5, linewidth=1)
                marker2 = self.ax2.axvline(x=i, color='red', alpha=0.5, linewidth=1)
                self.alert_markers.extend([marker1, marker2])
        except Exception as e:
            logging.error(f"Erreur dans mark_alerts_on_graphs: {str(e)}")
            # Éviter le crash en cas d'erreur'''
    content = re.sub(pattern9, replacement9, content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"Les modifications ont été appliquées à {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_navigation.py CHEMIN_DU_FICHIER")
        sys.exit(1)

    add_error_handling_to_file(sys.argv[1])
