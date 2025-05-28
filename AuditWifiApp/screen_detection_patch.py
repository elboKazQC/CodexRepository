#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch de correction pour la détection d'écran portable
À appliquer au fichier runner.py
"""

def apply_screen_detection_fix():
    """Applique la correction de détection d'écran portable"""
    
    # Code de la méthode is_portable_screen() à ajouter
    is_portable_screen_method = '''
    def is_portable_screen(self):
        """Détermine si l'écran est un écran portable basé sur la taille physique et le DPI"""
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        try:
            # Calculer la taille physique de l'écran
            dpi = self.master.winfo_fpixels('1i')
            diagonal_pixels = (screen_width**2 + screen_height**2)**0.5
            diagonal_inches = diagonal_pixels / dpi
            
            # Critères pour écran portable :
            # - Écran physique <= 16.5 pouces (laptops 15-16")
            # - OU résolution classique faible
            # - OU DPI élevé (écrans haute densité, souvent portables)
            is_portable = (
                diagonal_inches <= 16.5 or  
                screen_width < 1366 or screen_height < 768 or  
                dpi > 110  
            )
            
            return is_portable, diagonal_inches, dpi
            
        except Exception:
            # Fallback si la détection DPI échoue
            return screen_width < 1366 or screen_height < 768, None, None
'''
    
    # Modifications pour setup_style()
    setup_style_fix = '''
        # Utiliser la détection centralisée
        is_small_screen, diagonal_inches, dpi = self.is_portable_screen()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
'''
    
    # Modifications pour optimize_window_for_screen()
    optimize_window_fix = '''
        # Utiliser la méthode centralisée de détection
        is_small_screen, diagonal_inches, dpi = self.is_portable_screen()
        
        if is_small_screen:
            # Pour les petits écrans (laptops), utiliser 95% de l'écran
            window_width = int(screen_width * 0.95)
            window_height = int(screen_height * 0.90)
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")
            if diagonal_inches:
                print(f"📱 Fenêtre optimisée: {window_width}x{window_height} pour écran portable {diagonal_inches:.1f}″ (DPI:{dpi:.0f})")
            else:
                print(f"📱 Fenêtre optimisée: {window_width}x{window_height} pour écran portable")
        else:
            # Pour les grands écrans, maximiser
            try:
                self.master.state('zoomed')  # Windows
            except tk.TclError:
                try:
                    self.master.attributes('-zoomed', True)  # Linux/Unix
                except tk.TclError:
                    # Fallback pour la compatibilité
                    self.master.geometry("1200x800")
            print(f"🖥️ Fenêtre maximisée pour grand écran")
'''
    
    # Modifications pour setup_graphs()
    setup_graphs_fix = '''
        # Utiliser la détection centralisée pour cohérence
        is_small_screen, diagonal_inches, dpi = self.is_portable_screen()
'''
    
    print("📋 PATCH DE CORRECTION - DÉTECTION ÉCRAN PORTABLE")
    print("=" * 60)
    print()
    print("🎯 OBJECTIF:")
    print("   Corriger la détection d'écran portable pour résoudre")
    print("   le problème d'interface coupée sur écran 15\" en 1920x1080")
    print()
    print("🔧 CORRECTIONS À APPLIQUER:")
    print("   1. Ajouter la méthode is_portable_screen()")
    print("   2. Modifier setup_style() pour utiliser la détection centralisée")
    print("   3. Modifier optimize_window_for_screen() pour la nouvelle logique")
    print("   4. Modifier setup_graphs() pour la cohérence")
    print()
    print("📱 CRITÈRES DE DÉTECTION:")
    print("   • Taille physique ≤ 16.5 pouces (laptops)")
    print("   • DPI > 110 (écrans haute densité)")
    print("   • Résolution < 1366x768 (critère original)")
    print()
    print("✅ RÉSULTAT ATTENDU:")
    print("   Écran 15\" en 1920x1080 → Détecté comme portable")
    print("   Écran 24\" en 1920x1080 → Détecté comme grand écran")
    print()
    print("📁 FICHIERS AFFECTÉS:")
    print("   • runner.py (corrections appliquées)")
    print("   • SCREEN_DETECTION_REPORT.md (documentation)")
    print("   • quick_screen_test.py (test de validation)")
    
    return {
        'method': is_portable_screen_method,
        'setup_style': setup_style_fix,
        'optimize_window': optimize_window_fix,
        'setup_graphs': setup_graphs_fix
    }

def main():
    print("🚀 Application du patch de détection d'écran portable")
    print()
    
    fixes = apply_screen_detection_fix()
    
    print()
    print("📋 INSTRUCTIONS D'APPLICATION:")
    print("   1. Les corrections ont été documentées")
    print("   2. Testez avec quick_screen_test.py")
    print("   3. Lancez l'application sur votre laptop 15\"")
    print("   4. Vérifiez que l'interface responsive s'active")
    print()
    print("🔍 VALIDATION:")
    print("   • Recherchez le message: '📱 Interface adaptée pour écran portable'")
    print("   • Vérifiez que les boutons de navigation ne sont plus coupés")
    print("   • Confirmez que la fenêtre utilise 95% de l'écran")
    print()
    print("✅ Patch prêt à tester!")

if __name__ == "__main__":
    main()
