window.tailwind = window.tailwind || {};
window.tailwind.config = {
  theme: {
    extend: {
      colors: {
        // Base canvas for the app shell.
        bg: '#C8D2DF',
        // Primary cards and form surfaces.
        panel: '#F1F5F9',
        // Raised or highlighted neutral areas inside cards.
        panelSoft: '#FFFFFF',
        // Instagram-inspired blue, shifted darker for WCAG contrast on light bg.
        accent: '#004BB5',
        // Primary readable text.
        text: '#0F172A',
        // Secondary/supporting text.
        textSoft: '#334155',
        // Dividers and subtle control outlines.
        border: '#94A3B8',
        // Semantic status colors used by alerts and badges.
        danger: '#ed4956',
        success: '#059669',
        warning: '#b45309'
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      },
      animation: {
        fadeInUp: 'fadeInUp 220ms ease-out'
      }
    }
  }
};
