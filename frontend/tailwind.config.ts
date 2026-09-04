import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        ink: {
          950: "#0a1220",
          900: "#0f1b2d",
          800: "#152538",
          700: "#1c3049",
          600: "#25405f",
          500: "#33557a",
        },
        brand: {
          50: "#eef4ff",
          100: "#dbe7fe",
          400: "#4d7fc4",
          500: "#2f5d94",
          600: "#234a78",
          700: "#1a3a5f",
        },
        status: {
          verified: "#1f7a4d",
          verifiedBg: "#e6f4ec",
          warning: "#a3660a",
          warningBg: "#fdf1de",
          failed: "#b3261e",
          failedBg: "#fce8e6",
          pending: "#5c6472",
          pendingBg: "#eef0f3",
          na: "#8a93a3",
          naBg: "#f2f3f5",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,27,45,0.06), 0 1px 1px rgba(15,27,45,0.04)",
        panel: "0 4px 14px rgba(15,27,45,0.10)",
      },
    },
  },
  plugins: [],
};
export default config;
