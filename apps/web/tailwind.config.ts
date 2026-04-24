import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        bloom: {
          ink: "#243042",
          leaf: "#18b26b",
          sky: "#29a8ff",
          sun: "#ffd34d",
          coral: "#ff6b57",
          cream: "#fff8ea"
        }
      },
      boxShadow: {
        bloom: "0 18px 45px rgba(36, 48, 66, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;
