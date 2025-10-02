/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Cantarell", "Noto Sans", "Arial", "Apple Color Emoji", "Segoe UI Emoji"],
      },
      colors: {
        brand: {
          50: '#eef7ff',
          100: '#d9ecff',
          200: '#b6dbff',
          300: '#86c4ff',
          400: '#55a6ff',
          500: '#2b86ff',
          600: '#1767e6',
          700: '#124fc0',
          800: '#133f93',
          900: '#14366f'
        }
      }
    }
  },
  plugins: [],
}


