window.tailwind = window.tailwind || {};
window.tailwind.config = {
  theme: {
    extend: {
      colors: {
        bg: '#050812',
        panel: '#1a2742',
        panelSoft: '#243252',
        accent: '#6aa1ff',
        text: '#edf2ff',
        textSoft: '#b3bedb',
        success: '#34d399',
        warning: '#fbbf24'
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
