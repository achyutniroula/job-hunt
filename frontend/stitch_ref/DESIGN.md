# Design System Document: The Obsidian Ether

## 1. Overview & Creative North Star
**The Creative North Star: "The Digital Concierge"**
This design system moves away from the utilitarian "SaaS dashboard" aesthetic and toward a high-end editorial experience. It treats job seeking not as a chore, but as a premium, curated journey. By utilizing deep tonal layering, intentional asymmetry, and "ethereal" light sources, we create an immersive environment that feels quiet, authoritative, and futuristic.

To break the "template" look, we prioritize **negative space as a functional element**. Information is not crammed; it is staged. We utilize overlapping glass panels and varying levels of frosted transparency to create a sense of physical depth—like looking through sheets of dark, polished crystal.

---

## 2. Colors & Surface Architecture
The color palette is anchored in deep obsidian tones, utilizing the Material Design surface-tiering logic to create depth without relying on heavy shadows.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. Structural boundaries must be defined through:
1.  **Background Shifts:** Placing a `surface_container_low` card on a `surface` background.
2.  **Tonal Transitions:** Using the `surface_container` tiers to create organic separation.
3.  **Luminous Accents:** Utilizing the `secondary` (#7CD0FF) or `tertiary` (#D6BAFF) tokens at 5-10% opacity to create a "glow" that defines an edge.

### Surface Hierarchy & Nesting
Treat the UI as a series of nested, translucent layers.
*   **Base Layer:** `surface` (#111317) with a subtle radial gradient toward `surface_container_low`.
*   **Primary Containers:** `surface_container` (#1e2024) with `backdrop-filter: blur(12px)`.
*   **Floating Elements:** `surface_bright` (#37393e) used sparingly for elevated interaction points.

### The "Glass & Gradient" Rule
Main Call-to-Actions (CTAs) should never be flat. Use a linear gradient from `primary` (#C6C6C7) to `primary_fixed_dim` to simulate a metallic, reflected surface. For "RGB Glow" accents mentioned in the brief, use a `20px` blurred outer shadow of `secondary` (#7CD0FF) at **0.1 opacity** around section titles.

---

## 3. Typography
The typography system pairs the technical precision of **Inter** with the editorial elegance of **Manrope**.

*   **Display & Headlines (Manrope):** These are the "voice" of the system. Large, light-weight (`300` or `400`), and generously tracked. `display-lg` should be used for high-impact AI insights, creating a sense of "prestige."
*   **Body & UI (Inter):** Used for data density and readability. We lean into `body-md` for the majority of dashboard content to maintain a sleek, minimalist footprint.
*   **Intentional Contrast:** Pair a `headline-sm` in `on_surface` with a `label-sm` in `tertiary_fixed_dim`. This high-contrast pairing (large/thin vs. small/vibrant) mimics high-end fashion editorials.

---

## 4. Elevation & Depth
In this system, depth is "felt" rather than "seen."

*   **The Layering Principle:** To lift a card, do not use a black shadow. Instead, change the token from `surface_container_low` to `surface_container_high`. The subtle shift in gray value creates a natural, atmospheric lift.
*   **Ambient Shadows:** For floating modals, use a custom shadow: `0px 24px 48px rgba(0, 0, 0, 0.5)` combined with a 1px "Ghost Border."
*   **The "Ghost Border":** Where a border is necessary for accessibility, use `outline_variant` at **15% opacity**. The stroke must be `0.5px` or `1px` max. It should look like a faint reflection on the edge of a glass pane, not a box.
*   **Reflective Highlights:** Add a `linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 50%)` to the top-left corner of all glass panels to simulate a physical light source in the environment.

---

## 5. Components

### Buttons
*   **Primary (The Glass Button):** `surface_tint` background with a `0.5px` top-border of `primary_fixed`. Use `backdrop-filter: blur(8px)`. State changes (hover) should increase the `backdrop-filter` to `blur(16px)` rather than just darkening the color.
*   **Secondary:** `outline` border at 20% opacity. Text color `on_surface`.
*   **Tertiary:** No background or border. Use `label-md` uppercase with `2px` letter spacing.

### Cards & Lists
*   **Card Separation:** Forbid divider lines. Use `vertical white space` (minimum `32px`) or a shift from `surface_container_lowest` to `surface_container` to group information.
*   **Interactive Lists:** On hover, a list item should transition its background to `surface_container_highest` and trigger a faint `secondary` (blue) glow on the left-most edge.

### Chips (Skill/Status Tags)
*   **Style:** Rounded corners (e.g., `rounded-md`). Background: `surface_container_high` at 40% opacity. Border: `outline_variant` at 10%. Text: `label-sm`.

### AI Insight Tooltips
*   **Visual:** Deep translucent black (`surface_container_lowest` at 90% opacity). A `secondary_fixed` glow (soft RGB) should emanate from the pointer origin.

---

## 6. Do's and Don'ts

### Do
*   **Do** use asymmetrical layouts. A 3-column grid is "standard"; a 2-column wide layout with a floating utility rail feels "custom."
*   **Do** lean into `surface_container_lowest` for background "wells" where data lists reside.
*   **Do** use `manrope` for any numbers or data visualizations to keep the "luxury" feel.
*   **Do** ensure text contrast meets WCAG 2.1 AA standards by utilizing the `on_surface_variant` and `primary_fixed` tokens.

### Don't
*   **Don't** use pure `#000000`. Use the `surface` (#111317) token to ensure the "dark" feel has depth and isn't a "black hole."
*   **Don't** use vibrant, high-opacity neon colors. All "RGB Glows" must be diffused and faint (opacity < 15%).
*   **Don't** use standard `border-radius: 4px`. Stick to `xl` (0.75rem) for main panels and `md` (0.375rem) for smaller elements to maintain a sophisticated, softened look.
*   **Don't** use heavy, bold font weights. The "Luxury" aesthetic is built on thin, precise lines.