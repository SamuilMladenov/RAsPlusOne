/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // TriageFlow: navy #002B5B, medium blue #3488C0, accents #4BC6D3–#7EE2E8
        primary: {
          50: "#f0f9fc",
          100: "#e0f4f8",
          200: "#b8e8f0",
          300: "#7ee2e8",
          400: "#4bc6d3",
          500: "#4a9ecf",
          600: "#3488c0",
          700: "#2a6f9e",
          800: "#002b5b",
          900: "#001a38",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
