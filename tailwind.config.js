/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./project/templates/**/*.html",
        "./project/static/**/*.js"
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
