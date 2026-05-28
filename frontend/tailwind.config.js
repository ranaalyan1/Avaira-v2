/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
    theme: {
        extend: {
            fontFamily: {
                heading: ['Rajdhani', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
                body: ['Inter', 'sans-serif'],
            },
            colors: {
                avaira: {
                    bg: '#050505',
                    card: '#111111',
                    surface: '#181818',
                    primary: '#E84444',
                    red: '#FF003C',
                    purple: '#7000FF',
                    green: '#39FF14',
                    yellow: '#FFD300',
                    redAlert: '#FF003C',
                    danger: '#FF003C',
                    redLegacy: '#FF003C',
                    border: '#3F3F3F',
                    muted: '#CBCBCB',
                    dim: '#A2A2A2',
                    data: '#00F0FF',
                },
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
                popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
                primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
                secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
                muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
                accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
                destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: { '1': 'hsl(var(--chart-1))', '2': 'hsl(var(--chart-2))', '3': 'hsl(var(--chart-3))', '4': 'hsl(var(--chart-4))', '5': 'hsl(var(--chart-5))' }
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            keyframes: {
                'accordion-down': { from: { height: '0' }, to: { height: 'var(--radix-accordion-content-height)' } },
                'accordion-up': { from: { height: 'var(--radix-accordion-content-height)' }, to: { height: '0' } },
                'glow-pulse': { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.5' } },
                'scan': { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
                'slide-in': { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
                'floating': { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
                'glitch': {
                    '0%': { transform: 'translate(0)' },
                    '20%': { transform: 'translate(-2px, 2px)' },
                    '40%': { transform: 'translate(-2px, -2px)' },
                    '60%': { transform: 'translate(2px, 2px)' },
                    '80%': { transform: 'translate(2px, -2px)' },
                    '100%': { transform: 'translate(0)' },
                },
                'hologram': { '0%, 100%': { opacity: '0.8' }, '50%': { opacity: '0.4' }, '70%': { opacity: '0.9' } },
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
                'scan': 'scan 4s linear infinite',
                'slide-in': 'slide-in 0.3s ease-out',
                'floating': 'floating 3s ease-in-out infinite',
                'glitch': 'glitch 0.2s ease-in-out infinite',
                'hologram': 'hologram 2s ease-in-out infinite',
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
};
