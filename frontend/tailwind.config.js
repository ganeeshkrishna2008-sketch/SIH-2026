/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#082f49',
        },
        slate: {
          50: 'rgba(var(--color-slate-50), <alpha-value>)',
          100: 'rgba(var(--color-slate-100), <alpha-value>)',
          200: 'rgba(var(--color-slate-200), <alpha-value>)',
          300: 'rgba(var(--color-slate-300), <alpha-value>)',
          400: 'rgba(var(--color-slate-400), <alpha-value>)',
          500: 'rgba(var(--color-slate-500), <alpha-value>)',
          600: 'rgba(var(--color-slate-600), <alpha-value>)',
          700: 'rgba(var(--color-slate-700), <alpha-value>)',
          800: 'rgba(var(--color-slate-800), <alpha-value>)',
          900: 'rgba(var(--color-slate-900), <alpha-value>)',
          950: 'rgba(var(--color-slate-950), <alpha-value>)',
        }
      }
    },
  },
  plugins: [],
}
