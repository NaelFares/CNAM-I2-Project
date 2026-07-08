/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"]
      },
      // Colors/shadows/radii reference the CSS custom properties defined in
      // src/assets/main.css :root — that file is the single source of truth,
      // this config just exposes them as Tailwind utilities (bg-primary, etc).
      // Note: opacity modifiers (e.g. bg-primary/50) don't work with var()-based
      // colors in Tailwind 3; not used anywhere currently.
      colors: {
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        "surface-soft": "var(--color-surface-soft)",
        stroke: "var(--color-stroke)",
        "stroke-strong": "var(--color-stroke-strong)",
        text: "var(--color-text)",
        "text-muted": "var(--color-text-muted)",
        primary: {
          DEFAULT: "var(--color-primary)",
          soft: "var(--color-primary-soft)",
          strong: "var(--color-primary-strong)"
        },
        success: { DEFAULT: "var(--color-success)", soft: "var(--color-success-soft)" },
        danger: { DEFAULT: "var(--color-danger)", soft: "var(--color-danger-soft)" },
        info: { DEFAULT: "var(--color-info)", soft: "var(--color-info-soft)" }
      },
      boxShadow: {
        card: "var(--shadow-card)",
        "card-strong": "var(--shadow-card-strong)"
      },
      borderRadius: {
        card: "var(--radius-card)",
        control: "var(--radius-control)"
      },
      // sm/md/lg/xl/2xl keep Tailwind's defaults (640/768/1024/1280/1536) —
      // md = tablet/layout switch breakpoint, lg = desktop nav switch (AppLayout.vue).
      screens: {
        xs: "480px"
      }
    }
  },
  plugins: []
};
