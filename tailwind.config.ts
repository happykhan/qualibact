import type { Config } from 'tailwindcss'
import typography from '@tailwindcss/typography'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './content/**/*.{md,mdx}'
  ],
  // Dark mode is driven by data-theme="dark" on <html>, set by next-themes.
  // See WORKPLAN.md §2 and memory:styling-decisions.
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        // brand-* maps to the GenomicX teal accent (--gx-accent = #0d9488 light,
        // #2dd4bf dark). Existing brand-500/600/700 classnames keep working;
        // they now render in the fleet teal. (Tailwind 'teal' palette verbatim.)
        brand: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',  // matches --gx-accent (dark theme)
          500: '#14b8a6',
          600: '#0d9488',  // matches --gx-accent (light theme)
          700: '#0f766e',  // matches --gx-accent-hover (light theme)
          800: '#115e59',
          900: '#134e4a'
        },
        accent: {
          500: '#E57A66'
        },
        // Slate-aligned neutrals that match the --gx-* token values used
        // elsewhere. These are also what mashtreewebx / brigx use for
        // backgrounds and muted text, so fleet-pure.
        neutral: {
          50:  '#f8fafc',   // matches --gx-bg
          100: '#f1f5f9',   // matches --gx-bg-alt / --gx-code-bg
          200: '#e2e8f0',   // matches --gx-border (light)
          300: '#cbd5e1',
          400: '#94a3b8',   // matches --gx-text-muted (dark theme)
          500: '#64748b',   // matches --gx-text-muted (light theme)
          600: '#475569',
          700: '#334155',   // matches --gx-border / --gx-surface-hover (dark)
          800: '#1e293b',   // matches --gx-surface / --gx-bg-alt (dark)
          900: '#0f172a',   // matches --gx-bg (dark) / --gx-text (light)
        }
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'ui-sans-serif', 'system-ui'],
        header: ['var(--font-sans)', 'Inter', 'ui-sans-serif', 'system-ui'],
        serif: ['var(--font-sans)', 'Georgia', 'serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'Fira Code', 'ui-monospace', 'SFMono-Regular', 'monospace']
      },
      boxShadow: {
        'card': '0 6px 18px rgba(19, 31, 63, 0.06)',
        'btn': '0 4px 10px rgba(19, 31, 63, 0.06)'
      },
      borderRadius: {
        xl: '0.75rem'
      },
      container: {
        // Aligned with .gx-nav-inner / .gx-footer-inner so the nav logo,
        // body content, and footer all share the same left/right edges.
        // Full-bleed below xl, capped at 80rem (1280px) at xl+, with
        // 1rem / 1.5rem / 2rem responsive horizontal padding.
        center: true,
        screens: {
          sm: '100%',
          md: '100%',
          lg: '100%',
          xl: '80rem',
          '2xl': '80rem',
        },
        padding: { DEFAULT: '1rem', sm: '1.5rem', lg: '2rem' }
      },
      typography: () => ({
        DEFAULT: {
          css: {
            color: 'var(--gx-text)',
            a: {
              color: 'var(--gx-accent)',
              fontWeight: '500',
              '&:hover': { color: 'var(--gx-accent-hover)' }
            },
            strong: { color: 'var(--gx-text)' },
            hr: { borderColor: 'var(--gx-border)' },
            blockquote: { color: 'var(--gx-text-muted)', borderLeftColor: 'var(--gx-border)' },
            h1: { fontWeight: 700, fontFamily: 'var(--font-sans)', letterSpacing: '-0.02em', lineHeight: '1.15', color: 'var(--gx-text)' },
            h2: { fontWeight: 700, fontFamily: 'var(--font-sans)', marginTop: '1.6rem', marginBottom: '0.8rem', color: 'var(--gx-text)' },
            h3: { fontWeight: 600, color: 'var(--gx-text)' },
            h4: { fontWeight: 600, color: 'var(--gx-text)' },
            p: { lineHeight: '1.8', marginTop: '0.65rem', marginBottom: '0.65rem' },
            code: { color: 'var(--gx-text)', backgroundColor: 'var(--gx-code-bg)', padding: '0.1em 0.35em', borderRadius: '4px', fontWeight: '500' },
            'code::before': { content: 'none' },
            'code::after': { content: 'none' },
            pre: { backgroundColor: 'var(--gx-code-bg)', color: 'var(--gx-text)' },
            li: { marginTop: '0.25em', marginBottom: '0.25em' },
            'ul > li::marker': { color: 'var(--gx-text-muted)' },
            'ol > li::marker': { color: 'var(--gx-text-muted)' },
            table: { borderColor: 'var(--gx-border)' },
            thead: { borderBottomColor: 'var(--gx-border)', color: 'var(--gx-text)' },
            'tbody tr': { borderBottomColor: 'var(--gx-border)' }
          }
        }
      })
    }
  },
  plugins: [typography]
}
export default config
