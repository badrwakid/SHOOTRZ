// SHOOTRZ App Theme - Matching the logo design
export const SHOOTRZ_THEME = {
  // Primary Colors (matching logo)
  colors: {
    // Background colors (dark theme)
    background: '#000000', // Pure black background like logo
    surface: '#1a1a1a', // Slightly lighter for cards
    surfaceElevated: '#2a2a2a', // Elevated surfaces

    // Primary brand colors from logo
    primary: '#FF6B35', // Vibrant orange from logo
    primaryLight: '#FF8A65', // Lighter orange
    primaryDark: '#E65100', // Darker orange

    // Secondary colors (light blue from logo)
    secondary: '#42A5F5', // Light blue from logo outline
    secondaryLight: '#64B5F6', // Lighter blue
    secondaryDark: '#1976D2', // Darker blue

    // Text colors
    textPrimary: '#FFFFFF', // White text on dark background
    textSecondary: '#B0BEC5', // Light gray for secondary text
    textMuted: '#78909C', // Muted gray

    // Accent colors
    accent: '#00BCD4', // Cyan accent for highlights
    success: '#4CAF50', // Green for success states
    warning: '#FF9800', // Orange for warnings
    error: '#F44336', // Red for errors

    // Circuit board effect colors
    circuitGlow: '#00E5FF', // Bright cyan for glow effects
    circuitLine: '#42A5F5', // Blue for circuit lines
  },

  // Typography (matching logo font style)
  typography: {
    // Main headings (like "SHOOTRZ")
    heading1: {
      fontSize: 32,
      fontWeight: 'bold' as const,
      color: '#FFFFFF',
      letterSpacing: 1,
    },
    heading2: {
      fontSize: 24,
      fontWeight: 'bold' as const,
      color: '#FFFFFF',
      letterSpacing: 0.5,
    },
    heading3: {
      fontSize: 20,
      fontWeight: '600' as const,
      color: '#FFFFFF',
    },

    // Body text (like "PERFECT THE GAME")
    body: {
      fontSize: 16,
      fontWeight: 'normal' as const,
      color: '#B0BEC5',
      lineHeight: 24,
    },
    bodySmall: {
      fontSize: 14,
      fontWeight: 'normal' as const,
      color: '#B0BEC5',
      lineHeight: 20,
    },

    // Button text
    button: {
      fontSize: 16,
      fontWeight: 'bold' as const,
      color: '#FFFFFF',
    },

    // Caption text
    caption: {
      fontSize: 12,
      fontWeight: 'normal' as const,
      color: '#78909C',
    },
  },

  // Spacing
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },

  // Border radius
  borderRadius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    round: 50,
  },

  // Shadows (for depth on dark background)
  shadows: {
    small: {
      shadowColor: '#FF6B35',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 3,
    },
    medium: {
      shadowColor: '#FF6B35',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 5,
    },
    large: {
      shadowColor: '#FF6B35',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.2,
      shadowRadius: 16,
      elevation: 8,
    },
  },

  // Gradient effects (like logo outline)
  gradients: {
    primary: ['#FF6B35', '#FF8A65'],
    primaryDark: ['#E65100', '#FF6B35'],
    secondary: ['#42A5F5', '#64B5F6'],
    secondaryDark: ['#1976D2', '#42A5F5'],
    circuit: ['#00E5FF', '#42A5F5'],
    accent: ['#00BCD4', '#00E5FF'],
    success: ['#4CAF50', '#66BB6A'],
    card: ['rgba(26, 26, 26, 0.8)', 'rgba(42, 42, 42, 0.95)'],
    orange_glow: ['rgba(255, 107, 53, 0.2)', 'rgba(255, 107, 53, 0)'],
    blue_glow: ['rgba(66, 165, 245, 0.2)', 'rgba(66, 165, 245, 0)'],
  },

  // Animation timings
  animations: {
    fast: 150,
    normal: 300,
    slow: 500,
    verySlow: 800,
  },

  // Easing functions (for Animated API)
  easing: {
    easeInOut: 'ease-in-out',
    easeOut: 'ease-out',
    spring: 'spring',
  },
};

// Component-specific styles
export const COMPONENT_STYLES = {
  // Button styles
  button: {
    primary: {
      backgroundColor: SHOOTRZ_THEME.colors.primary,
      borderRadius: SHOOTRZ_THEME.borderRadius.md,
      paddingVertical: SHOOTRZ_THEME.spacing.md,
      paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
      ...SHOOTRZ_THEME.shadows.small,
    },
    secondary: {
      backgroundColor: 'transparent',
      borderWidth: 2,
      borderColor: SHOOTRZ_THEME.colors.secondary,
      borderRadius: SHOOTRZ_THEME.borderRadius.md,
      paddingVertical: SHOOTRZ_THEME.spacing.md,
      paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
    },
  },

  // Card styles
  card: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.lg,
    ...SHOOTRZ_THEME.shadows.medium,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },

  // Input styles
  input: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderWidth: 1,
    borderRadius: SHOOTRZ_THEME.borderRadius.md,
    padding: SHOOTRZ_THEME.spacing.md,
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
};
