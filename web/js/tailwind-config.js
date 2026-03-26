window.tailwind = window.tailwind || {};
window.tailwind.config = {
  theme: {
    extend: {
      colors: {
        bg: '#000000',
        panel: '#242424',
        panelSoft: '#2d2d2d',
        accent: '#0095F6',
        text: '#f5f5f5',
        textSoft: '#a8a8a8',
        border: '#262626',
        danger: '#ed4956',
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
