/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'neon-cyan': '#00f5ff',
        'neon-orange': '#ff8c00',
        'neon-amber': '#ffb300',
        'bg-lab': '#0a0e1a',
        'grid-line': '#1a2340',
        'cell-empty': '#0d1426',
        'cell-hover': '#111d38',
      },
      boxShadow: {
        'neon-cyan': '0 0 8px #00f5ff, 0 0 20px rgba(0,245,255,0.3)',
        'neon-orange': '0 0 8px #ff8c00, 0 0 20px rgba(255,140,0,0.3)',
        'neon-amber': '0 0 8px #ffb300, 0 0 20px rgba(255,179,0,0.3)',
      },
      fontFamily: {
        mono: ['"Courier New"', 'Courier', 'monospace'],
      },
    },
  },
  plugins: [],
}
