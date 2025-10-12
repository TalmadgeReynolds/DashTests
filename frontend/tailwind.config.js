/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design system colors from UI spec
        indigo: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          600: '#6366F1',
          700: '#4F46E5',
          800: '#4338CA',
        },
        slate: {
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          600: '#475569',
        },
        green: {
          100: '#D1FAE5',
          900: '#065F46',
        },
        blue: {
          100: '#DBEAFE',
          800: '#1E40AF',
        },
        red: {
          100: '#FEE2E2',
          300: '#FCA5A5',
          500: '#EF4444',
          900: '#991B1B',
        },
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.1)',
        'card-hover': '0 4px 6px rgba(0,0,0,0.1)',
        'modal': '0 20px 25px -5px rgba(0,0,0,0.2)',
      },
      borderRadius: {
        'card': '12px',
        'modal': '16px',
      },
    },
  },
  plugins: [],
}
