---
name: Lumina Velocity
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#43474f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737780'
  outline-variant: '#c3c6d1'
  surface-tint: '#3a5f94'
  primary: '#001e40'
  on-primary: '#ffffff'
  primary-container: '#003366'
  on-primary-container: '#799dd6'
  inverse-primary: '#a7c8ff'
  secondary: '#00696e'
  on-secondary: '#ffffff'
  secondary-container: '#00f4fe'
  on-secondary-container: '#006c71'
  tertiary: '#0e1f32'
  on-tertiary: '#ffffff'
  tertiary-container: '#243448'
  on-tertiary-container: '#8c9cb5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a7c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#1f477b'
  secondary-fixed: '#63f7ff'
  secondary-fixed-dim: '#00dce5'
  on-secondary-fixed: '#002021'
  on-secondary-fixed-variant: '#004f53'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Montserrat
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The design system is engineered for a "Smart Travel" experience, bridging the gap between high-tech precision and the warmth of global exploration. The brand personality is **innovative, reliable, and welcoming**, aimed at modern travelers who value efficiency without sacrificing the joy of discovery.

The aesthetic follows a **Modern Corporate** foundation infused with **Glassmorphism** for data-heavy overlays and interactive maps. It uses generous whitespace to ensure the UI feels breathable and premium, while subtle motion and depth create a sense of intelligence and "living" technology. The goal is to evoke a feeling of effortless navigation through complex travel landscapes.

## Colors

The palette is anchored by **Deep Ocean Blue (#003366)**, providing a foundation of trust and professional authority. **Bright Turquoise (#00F5FF)** acts as a high-energy accent color, used sparingly for primary actions, progress indicators, and AI-driven insights to signify innovation.

Backgrounds utilize **Clean White (#FFFFFF)** for core content areas and **Subtle Grey (#F8FAFC)** for structural surfaces and page-level backgrounds to reduce eye strain. Interactive states for secondary elements use **Slate Grey (#64748B)** to maintain a sophisticated, neutral balance that allows travel photography to remain the focal point.

## Typography

The typography strategy pairs **Montserrat** for headlines with **Inter** for body and UI elements. Montserrat’s geometric clarity provides a modern, confident "startup" feel for headings and branding elements. 

Inter is utilized for all functional text, ensuring maximum readability at small sizes and within high-density data visualizations. We use tight letter-spacing on larger headings to maintain a "tech-forward" appearance, while body copy maintains standard spacing for optimal legibility during long-form itinerary reading.

## Layout & Spacing

The design system utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. A strict 8px spacing power-of-two scale ensures vertical rhythm and consistent alignment across all components.

- **Desktop:** 12 columns, 24px gutters, 40px side margins.
- **Tablet:** 8 columns, 20px gutters, 24px side margins.
- **Mobile:** 4 columns, 16px gutters, 16px side margins.

Content is grouped using logical containers with `padding-lg (32px)` for primary sections and `padding-md (16px)` for internal card elements. Safe areas are strictly enforced for camera-overlay interfaces to prevent UI overlap with hardware notches or interactive gestures.

## Elevation & Depth

Hierarchy is established through **Ambient Shadows** and **Glassmorphism**. Surfaces are tiered as follows:

1.  **Base (0dp):** The neutral background (#F8FAFC).
2.  **Surface (1dp):** White cards with a subtle 1px border (#E2E8F0) and a very soft, diffused shadow (0px 4px 20px rgba(0, 51, 102, 0.05)).
3.  **Overlay (Glass):** Used for camera HUDs, floating navigation bars, and map tooltips. This effect uses a 12px backdrop-blur with a 60% white semi-transparent fill and a thin white inner-stroke to simulate polished glass.
4.  **Interactive (Floating):** Elements like "Book Now" buttons use a slightly deeper shadow (0px 8px 30px rgba(0, 245, 255, 0.2)) to appear lifted off the page.

## Shapes

The shape language is consistently **Rounded (0.5rem base)**. This soft geometry balances the "high-tech" coldness of the blue palette with a friendly, approachable feel. 

- **Standard Buttons & Inputs:** 0.5rem (8px) radius.
- **Cards & Modals:** 1rem (16px) radius for a modern, distinct appearance.
- **Search Bars & Tags:** 3rem (Pill-shaped) to differentiate them as highly interactive or status-based elements.

## Components

### Buttons
- **Primary:** Deep Ocean Blue background, white text, 8px radius. High-impact for conversion.
- **Secondary:** White background with a 1px Turquoise border and Turquoise text.
- **CTA:** For AI features, use a gradient from Deep Ocean Blue to Turquoise with a subtle glow shadow.

### Input Fields
Inputs use a white background with a subtle grey border. On focus, the border transitions to Turquoise with a 2px outer glow. Labels are positioned above the field in **label-md** typography.

### Cards
Cards are the primary container for travel destinations. They feature a full-bleed image at the top, followed by content in the white body area. Apply a 16px corner radius and a soft ambient shadow to distinguish from the background.

### Glassmorphism Overlays
Used for "Smart View" camera interfaces. These must feature a white border (0.5px opacity 30%) and a `backdrop-filter: blur(12px)`. Text inside must be high-contrast (Deep Ocean Blue) or White with a thin dark text-shadow for readability over varied camera backgrounds.

### Chips & Tags
Used for categories (e.g., "Eco-friendly", "Luxury"). These should be pill-shaped with light Turquoise backgrounds (#E0FBFC) and Turquoise text.