import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Nunito", "system-ui", "sans-serif"],
        display: ["Nunito", "system-ui", "sans-serif"]
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))"
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))"
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))"
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))"
        },
        bloom: {
          ink: "#243042",
          leaf: "hsl(var(--bloom-leaf))",
          sky: "hsl(var(--bloom-sky))",
          sun: "hsl(var(--bloom-sun))",
          coral: "hsl(var(--bloom-coral))",
          cream: "#fff8ea",
          green: "hsl(var(--bloom-green))",
          "green-deep": "hsl(var(--bloom-green-deep))",
          blue: "hsl(var(--bloom-blue))"
        },
        petal: {
          green: "hsl(var(--petal-green))",
          blue: "hsl(var(--petal-blue))",
          yellow: "hsl(var(--petal-yellow))",
          coral: "hsl(var(--petal-coral))"
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        xl: "1rem",
        "2xl": "1.5rem",
        "3xl": "2rem"
      },
      boxShadow: {
        bloom: "0 18px 45px rgba(36, 48, 66, 0.12)",
        soft: "var(--shadow-soft)",
        card: "var(--shadow-card)"
      },
      backgroundImage: {
        "hero-bloom": "linear-gradient(135deg, hsl(var(--hero-from)), hsl(var(--hero-to)))"
      }
    }
  },
  plugins: []
};

export default config;
