/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  theme: {
    extend: {
      colors: {
        gh: {
          bg: '#0f1117',
          panel: '#161b22',
          border: '#30363d',
          muted: '#8b949e',
          accent: '#58a6ff',
        },
      },
    },
  },
  plugins: [],
};
