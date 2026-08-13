class EstilosModernos:
    """Sistema visual compartido para Carnes Luévanos."""

    COLORS = {
        # Marca Carnes Luévanos: negro, marfil y dorado.
        'primary1': '#b38a47',
        'primary2': '#8b682f',
        'primary': '#20242c',
        'primary_light': '#f7f0e5',
        'primary_dark': '#1d2026',
        'primary_dark1': '#8b682f',

        # Acentos del logo
        'secondary': '#8b682f',
        'secondary1': '#b38a47',
        'secondary_light': '#ead9b9',
        'secondary_dark': '#6f5123',
        'wine': '#b38a47',
        'wine_dark': '#8b682f',
        'olive': '#6b5a3b',
        'gold': '#d7b56d',

        # Estados
        'success': '#18964b',
        'success_dark': '#11743a',
        'warning': '#d7b56d',
        'warning_dark': '#a77f32',
        'danger': '#c21f28',
        'danger_dark': '#8f070c',
        'info': '#3f6fa8',
        'info2': '#315c8c',

        # Neutros
        'white': '#ffffff',
        'Verde': '#18964b',
        'Tinto': '#8b682f',
        'light': '#faf9f7',
        'light_gray': '#ece9e4',
        'gray': '#68707d',
        'dark_gray': '#4b515b',
        'dark': '#20242c',
        'black': '#111827',

        # Superficies
        'accent': '#b38a47',
        'accent1': '#d7b56d',
        'accent_light': '#f7f0e5',
        'accent_dark': '#8b682f',
        'bg_primary': '#f8f8f7',
        'bg_primary1': '#b38a47',
        'bg_secondary': '#ffffff',
        'bg_card': '#ffffff',
        'bg_hover': '#f6efe4',
        'sidebar': '#ffffff',
        'sidebar_soft': '#faf8f4',
        'sidebar_active': '#f7f0e5',

        # Bordes
        'border': '#e7e4df',
        'border_focus': '#b38a47',
        'border_error': '#c21f28',
    }

    FONTS = {
        'primary': 'Poppins',
        'secondary': 'Montserrat',
        'display': 'Montserrat',
        'brand': 'Andimante Personal Use',
        'monospace': 'Consolas',
        'sizes': {
            'xs': 8,
            'sm': 9,
            'base': 10,
            'lg': 11,
            'xl': 12,
            '2xl': 14,
            '3xl': 16,
            '4xl': 18,
            '5xl': 21,
        }
    }

    BUTTON_STYLES = {
        'primary': {
            'bg': COLORS['primary1'],
            'fg': COLORS['white'],
            'hover_bg': COLORS['success_dark'],
            'active_bg': COLORS['primary1'],
            'font': (FONTS['primary'], FONTS['sizes']['base'], 'bold'),
            'padding': (15, 8),
            'relief': 'flat',
            'cursor': 'hand2'
        },
        'secondary': {
            'bg': COLORS['secondary'],
            'fg': COLORS['white'],
            'hover_bg': COLORS['secondary_dark'],
            'active_bg': COLORS['secondary_light'],
            'font': (FONTS['primary'], FONTS['sizes']['base'], 'bold'),
            'padding': (15, 8),
            'relief': 'flat',
            'cursor': 'hand2'
        },
        'success': {
            'bg': COLORS['success'],
            'fg': COLORS['white'],
            'hover_bg': COLORS['success_dark'],
            'active_bg': COLORS['success'],
            'font': (FONTS['primary'], FONTS['sizes']['base'], 'bold'),
            'padding': (15, 8),
            'relief': 'flat',
            'cursor': 'hand2'
        },
        'warning': {
            'bg': COLORS['warning'],
            'fg': COLORS['white'],
            'hover_bg': COLORS['warning_dark'],
            'active_bg': COLORS['warning'],
            'font': (FONTS['primary'], FONTS['sizes']['base'], 'bold'),
            'padding': (15, 8),
            'relief': 'flat',
            'cursor': 'hand2'
        },
        'danger': {
            'bg': COLORS['danger'],
            'fg': COLORS['white'],
            'hover_bg': COLORS['danger_dark'],
            'active_bg': COLORS['danger'],
            'font': (FONTS['primary'], FONTS['sizes']['base'], 'bold'),
            'padding': (15, 8),
            'relief': 'flat',
            'cursor': 'hand2'
        },
        'outline': {
            'bg': COLORS['white'],
            'fg': COLORS['primary'],
            'hover_bg': COLORS['bg_hover'],
            'active_bg': COLORS['light_gray'],
            'font': (FONTS['primary'], FONTS['sizes']['base'], 'bold'),
            'padding': (15, 8),
            'relief': 'solid',
            'bd': 1,
            'cursor': 'hand2'
        }
    }

    CARD_STYLES = {
        'default': {
            'bg': COLORS['bg_card'],
            'relief': 'flat',
            'bd': 1,
            'highlightbackground': COLORS['border'],
            'highlightthickness': 1
        },
        'elevated': {
            'bg': COLORS['bg_card'],
            'relief': 'flat',
            'bd': 1,
            'highlightbackground': COLORS['border'],
            'highlightthickness': 1
        }
    }

    ENTRY_STYLES = {
        'default': {
            'font': (FONTS['primary'], FONTS['sizes']['base']),
            'bg': COLORS['white'],
            'fg': COLORS['dark'],
            'relief': 'solid',
            'bd': 1,
            'highlightbackground': COLORS['border'],
            'highlightcolor': COLORS['border_focus'],
            'highlightthickness': 1
        }
    }

    LABEL_STYLES = {
        'title': {
            'font': (FONTS['primary'], FONTS['sizes']['3xl'], 'bold'),
            'fg': COLORS['dark'],
            'bg': COLORS['bg_primary']
        },
        'subtitle': {
            'font': (FONTS['primary'], FONTS['sizes']['xl'], 'bold'),
            'fg': COLORS['dark_gray'],
            'bg': COLORS['bg_primary']
        },
        'body': {
            'font': (FONTS['primary'], FONTS['sizes']['base']),
            'fg': COLORS['gray'],
            'bg': COLORS['bg_primary']
        },
        'caption': {
            'font': (FONTS['primary'], FONTS['sizes']['sm']),
            'fg': COLORS['gray'],
            'bg': COLORS['bg_primary']
        }
    }

    @staticmethod
    def ajustar_brillo_color(color_hex, factor):
        color_hex = color_hex.lstrip('#')
        rgb = tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4))
        rgb_ajustado = []
        for componente in rgb:
            if factor > 0:
                nuevo_valor = componente + (255 - componente) * (factor / 100)
            else:
                nuevo_valor = componente * (1 + factor / 100)
            rgb_ajustado.append(max(0, min(255, int(nuevo_valor))))
        return f"#{rgb_ajustado[0]:02x}{rgb_ajustado[1]:02x}{rgb_ajustado[2]:02x}"

    @staticmethod
    def crear_gradiente_color(color1, color2, pasos=10):
        color1 = color1.lstrip('#')
        color2 = color2.lstrip('#')
        rgb1 = tuple(int(color1[i:i + 2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(color2[i:i + 2], 16) for i in (0, 2, 4))

        gradiente = []
        for i in range(pasos):
            factor = i / (pasos - 1)
            rgb_intermedio = tuple(
                int(rgb1[j] + (rgb2[j] - rgb1[j]) * factor) for j in range(3)
            )
            gradiente.append(f"#{rgb_intermedio[0]:02x}{rgb_intermedio[1]:02x}{rgb_intermedio[2]:02x}")
        return gradiente


estilos = EstilosModernos()


