import type { Config } from "tailwindcss";
export default {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./features/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: { ink:"#111318", surface:"#191C23", surface2:"#222631", cream:"#F5F3ED", muted:"#A8ADBA",
      forge:"#FF6B35", forgeDark:"#D94E25", volt:"#5B7CFA", voltDark:"#3559D8", lime:"#C5F467", ivory:"#F7F4EC", warm:"#ECE9E1", coal:"#202126" },
    fontFamily: { display:["var(--font-display)","sans-serif"], sans:["var(--font-sans)","sans-serif"], mono:["var(--font-mono)","monospace"] },
  }},
  plugins: [],
} satisfies Config;
