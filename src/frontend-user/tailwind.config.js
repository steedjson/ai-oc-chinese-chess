/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        chess: {
          board: '#dcb35c',
          boardDark: '#c9a050',
          pieceRed: '#c00',
          pieceBlack: '#111',
          line: '#8b7355',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        chinese: ['Noto Serif SC', 'Songti SC', 'simsun', 'serif'],
      },
      animation: {
        'piece-move': 'pieceMove 0.3s ease-in-out',
        'piece-capture': 'pieceCapture 0.2s ease-in',
        'check-pulse': 'checkPulse 1s infinite',
      },
      keyframes: {
        pieceMove: {
          '0%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
          '100%': { transform: 'translateY(0)' },
        },
        pieceCapture: {
          '0%': { opacity: '1', transform: 'scale(1)' },
          '100%': { opacity: '0', transform: 'scale(0.5)' },
        },
        checkPulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
    },
  },
  plugins: [],
}
