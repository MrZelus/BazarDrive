window.tailwind = window.tailwind || {};
window.tailwind.config = {
  theme: {
    extend: {
      colors: {
        bg: '#0b1020',
        panel: '#131a2b',
        panelSoft: '#1b2338',
        accent: '#4f8cff',
        text: '#e8edff',
        textSoft: '#9aa7c7',
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
