# Skill: UI-UX-PRO-MAX

## Purpose
AI-powered design intelligence providing searchable databases of UI styles, color palettes, font pairings, UX guidelines, and chart types across 16 tech stacks. Used to generate professional design systems and audit/improve UI/UX quality.

## Source
- GitHub: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- NPM: `uipro-cli` (v2.5.0)
- License: MIT
- Installed: `.github/prompts/ui-ux-pro-max/`

## Install / Update
```bash
npx uipro-cli init --ai copilot
```
Generated path: `.github/prompts/ui-ux-pro-max/`

## When to Use
Activate this skill when the user requests:
- Building or improving a web page / landing page / dashboard
- Choosing a color scheme, typography, or UI style
- Reviewing UI/UX quality or accessibility
- Generating a design system for a project

## Inputs
- Product type description (e.g. "SaaS documentation portal")
- Style keywords (e.g. "dark, minimal, knowledge")
- Tech stack (e.g. `html-tailwind`, `react`, `nextjs`)
- Project name (optional)

## Steps
1. **Generate design system** (always start here):
   ```bash
   python3 .github/prompts/ui-ux-pro-max/scripts/search.py "<product_type> <keywords>" --design-system -p "Project Name"
   ```
2. **Domain deep-dives** as needed:
   ```bash
   python3 .github/prompts/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <style|color|typography|ux|chart|landing|product>
   ```
3. **Stack guidelines**:
   ```bash
   python3 .github/prompts/ui-ux-pro-max/scripts/search.py "<keyword>" --stack html-tailwind
   ```
4. Implement recommendations; verify against the Pre-Delivery Checklist in `PROMPT.md`.

## Available Domains
`style` · `color` · `typography` · `chart` · `ux` · `landing` · `product`

## Available Stacks
`html-tailwind` · `react` · `nextjs` · `astro` · `vue` · `nuxtjs` · `svelte` · `shadcn` · `swiftui` · `react-native` · `flutter` · `jetpack-compose`

## Outputs
- Recommended design system (pattern, style, colors, typography, effects, anti-patterns)
- Domain-specific design data (styles, palettes, fonts, UX rules, chart types)
- Pre-delivery checklist for quality assurance
