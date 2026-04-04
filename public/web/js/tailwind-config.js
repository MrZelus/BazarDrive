window.tailwind = window.tailwind || {};
window.tailwind.config = {
  theme: {
    extend: {
      colors: {
        // Color tokens are mapped to CSS variables so dark/light themes can
        // switch without re-generating utility classes.
        bg: 'rgb(var(--feed-bg-rgb) / <alpha-value>)',
        panel: 'rgb(var(--feed-panel-rgb) / <alpha-value>)',
        panelSoft: 'rgb(var(--feed-panel-soft-rgb) / <alpha-value>)',
        accent: 'rgb(var(--feed-accent-rgb) / <alpha-value>)',
        text: 'rgb(var(--feed-text-rgb) / <alpha-value>)',
        textSoft: 'rgb(var(--feed-text-soft-rgb) / <alpha-value>)',
        border: 'rgb(var(--feed-border-rgb) / <alpha-value>)',
        danger: 'rgb(var(--feed-danger-rgb) / <alpha-value>)',
        success: 'rgb(var(--feed-success-rgb) / <alpha-value>)',
        warning: 'rgb(var(--feed-warning-rgb) / <alpha-value>)'
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
