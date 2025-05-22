#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import base64
import logging
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

def generate_heatmap(data, title="Distribution du signal WiFi", colormap="viridis", size=(800, 600)):
    """
    Génère une carte de chaleur à partir des données de signal WiFi

    Args:
        data (dict): Données au format {position: signal_strength}
                     où position est un tuple (x, y) et signal_strength un nombre
        title (str): Titre du graphique
        colormap (str): Nom de la palette de couleurs matplotlib
        size (tuple): Dimensions (largeur, hauteur) en pixels

    Returns:
        ImageTk.PhotoImage: Image pour l'interface Tkinter
    """
    try:
        # Extraction des coordonnées et valeurs
        if not data:
            logger.warning("Aucune donnée pour générer la heatmap")
            return None

        positions = list(data.keys())
        values = list(data.values())

        # Crée une grille pour la heatmap
        x_vals = [p[0] for p in positions]
        y_vals = [p[1] for p in positions]

        if not x_vals or not y_vals:
            logger.warning("Données insuffisantes pour générer la heatmap")
            return None

        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)

        # Ajout d'une marge
        x_range = max(1, x_max - x_min)
        y_range = max(1, y_max - y_min)
        margin = 0.1
        x_min -= margin * x_range
        x_max += margin * x_range
        y_min -= margin * y_range
        y_max += margin * y_range

        # Création de la grille
        grid_size = 50
        xi = np.linspace(x_min, x_max, grid_size)
        yi = np.linspace(y_min, y_max, grid_size)
        xi, yi = np.meshgrid(xi, yi)

        # Interpolation des valeurs sur la grille
        from scipy.interpolate import griddata
        zi = griddata(positions, values, (xi, yi), method='linear', fill_value=-100)

        # Création de la figure
        fig = Figure(figsize=(size[0]/100, size[1]/100), dpi=100)
        ax = fig.add_subplot(111)

        # Génération de la heatmap
        c = ax.pcolormesh(xi, yi, zi, shading='auto', cmap=colormap)
        ax.set_title(title)
        ax.set_xlabel('Position X')
        ax.set_ylabel('Position Y')
        fig.colorbar(c, ax=ax, label='Force du signal (dBm)')

        # Ajout des points de mesure
        ax.scatter([p[0] for p in positions], [p[1] for p in positions],
                  c='black', s=10, alpha=0.5, marker='o')

        # Conversion en image pour Tkinter
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        img = Image.open(buf)
        img = img.resize(size, Image.LANCZOS)

        return ImageTk.PhotoImage(img)

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la heatmap: {e}")
        return None

def generate_signal_over_time_chart(timestamps, signal_values, title="Signal WiFi au cours du temps", size=(800, 400)):
    """
    Génère un graphique de l'évolution du signal WiFi au cours du temps

    Args:
        timestamps (list): Liste des horodatages
        signal_values (list): Liste des valeurs de signal correspondantes
        title (str): Titre du graphique
        size (tuple): Dimensions (largeur, hauteur) en pixels

    Returns:
        ImageTk.PhotoImage: Image pour l'interface Tkinter
    """
    try:
        if not timestamps or not signal_values or len(timestamps) != len(signal_values):
            logger.warning("Données insuffisantes ou incohérentes pour générer le graphique")
            return None

        fig = Figure(figsize=(size[0]/100, size[1]/100), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(timestamps, signal_values, '-o', color='blue', alpha=0.7)
        ax.set_title(title)
        ax.set_xlabel('Temps')
        ax.set_ylabel('Force du signal (dBm)')
        ax.grid(True, linestyle='--', alpha=0.7)

        # Rotation des labels pour meilleure lisibilité
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        fig.tight_layout()

        # Conversion en image pour Tkinter
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        img = Image.open(buf)
        img = img.resize(size, Image.LANCZOS)

        return ImageTk.PhotoImage(img)

    except Exception as e:
        logger.error(f"Erreur lors de la génération du graphique: {e}")
        return None
