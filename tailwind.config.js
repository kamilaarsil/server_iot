/** @type {import('tailwindcss').Config} */
module.exports = {
    mode: 'jit',
    content: ["app/templates/**/*.html"],
    theme: {
        extend: {
            fontFamily: {
                poppins: ["Poppins", "sans-serif"],
              },
        },
    },
    plugins: [],
}; 