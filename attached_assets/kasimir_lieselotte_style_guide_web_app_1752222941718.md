# Kasimir + Lieselotte Internal Web App Style Guide

## Overview

This guide provides design specifications for internal web applications while maintaining the authentic Kasimir + Lieselotte brand identity. The focus is on creating modern, functional interfaces that retain the organic, premium feel of the brand while optimizing for productivity and usability.

---

## Color System

### Primary Brand Colors (Retained)
```
Natural Green:     #2D5B2D (Primary brand color)
Warm Earth Brown:  #8B4513 (Secondary brand color)
Cream/Off-White:   #FAF7F0 (Background base)
```

### Extended Digital Palette

#### Interface Colors
```
Deep Forest Green:  #1B3F1B (Navigation, headers)
Sage Green:        #87A96B (Active states, success)
Muted Olive:       #6B7B3A (Accents, borders)
Warm Terracotta:   #C17A5B (CTAs, warnings)
Soft Gold:         #D4A574 (Highlights, badges)
```

#### Neutral System
```
Charcoal:          #2C3E2C (Primary text)
Medium Gray:       #5A6B5A (Secondary text)
Light Gray:        #B8C5B8 (Disabled states)
Pale Green:        #F0F5F0 (Subtle backgrounds)
Pure White:        #FFFFFF (Cards, modals)
```

#### Semantic Colors
```
Success Green:     #4A7C4A (Success states)
Warning Amber:     #B8860B (Warning states)
Error Terracotta:  #A0522D (Error states)
Info Blue:         #5F8A8B (Information states)
```

---

## Typography

### Font Stack
**Primary:** `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
**Secondary:** `Georgia, 'Times New Roman', serif` (for organic, natural feels)
**Monospace:** `'JetBrains Mono', 'Fira Code', monospace` (for data/code)

### Type Scale
```
Display Large:     32px / 40px (Page titles)
Display Medium:    24px / 32px (Section headers)
Heading 1:         20px / 28px (Card titles)
Heading 2:         18px / 24px (Subsections)
Body Large:        16px / 24px (Primary text)
Body Medium:       14px / 20px (Secondary text)
Body Small:        12px / 16px (Captions, labels)
```

### Font Weights
- **Regular (400):** Body text, descriptions
- **Medium (500):** Labels, secondary headings
- **Semibold (600):** Primary buttons, important text
- **Bold (700):** Page titles, emphasis

---

## Layout & Spacing

### Grid System
- **Base Unit:** 8px
- **Container Max Width:** 1200px
- **Sidebar Width:** 280px
- **Header Height:** 64px

### Spacing Scale
```
xs:  4px   (tight spacing)
sm:  8px   (component padding)
md:  16px  (card padding)
lg:  24px  (section spacing)
xl:  32px  (page margins)
2xl: 48px  (major sections)
3xl: 64px  (page spacing)
```

### Responsive Breakpoints
```
sm:  640px  (Mobile landscape)
md:  768px  (Tablet)
lg:  1024px (Desktop)
xl:  1280px (Large desktop)
```

---

## Components

### Navigation

#### Top Navigation
- **Background:** Deep Forest Green (#1B3F1B)
- **Height:** 64px
- **Logo:** White/cream version
- **Links:** White text, hover with Sage Green (#87A96B)
- **User menu:** Cream background with Natural Green text

#### Sidebar Navigation
- **Background:** Pale Green (#F0F5F0)
- **Width:** 280px
- **Active state:** Natural Green (#2D5B2D) with white text
- **Hover state:** Light opacity of Natural Green
- **Icons:** Consistent with brand's natural aesthetic

### Cards & Containers

#### Standard Card
```css
background: #FFFFFF
border: 1px solid #B8C5B8
border-radius: 8px
box-shadow: 0 2px 8px rgba(45, 91, 45, 0.08)
padding: 24px
```

#### Elevated Card
```css
background: #FFFFFF
border: 1px solid #87A96B
border-radius: 12px
box-shadow: 0 4px 16px rgba(45, 91, 45, 0.12)
padding: 32px
```

### Buttons

#### Primary Button
```css
background: #2D5B2D
color: #FFFFFF
border-radius: 6px
padding: 12px 24px
font-weight: 600
hover: #1B3F1B
```

#### Secondary Button
```css
background: transparent
color: #2D5B2D
border: 2px solid #2D5B2D
border-radius: 6px
padding: 10px 22px
font-weight: 500
hover: background #F0F5F0
```

#### Tertiary Button
```css
background: transparent
color: #5A6B5A
border: none
padding: 8px 16px
font-weight: 500
hover: background #F0F5F0
```

### Form Elements

#### Input Fields
```css
background: #FFFFFF
border: 1px solid #B8C5B8
border-radius: 6px
padding: 12px 16px
font-size: 14px
focus: border-color #2D5B2D, box-shadow 0 0 0 3px rgba(45, 91, 45, 0.1)
```

#### Labels
```css
color: #2C3E2C
font-size: 14px
font-weight: 500
margin-bottom: 8px
```

#### Error States
```css
border-color: #A0522D
color: #A0522D
background: rgba(160, 82, 45, 0.05)
```

---

## Data Visualization

### Chart Colors
Primary data series should use brand colors in this order:
1. Natural Green (#2D5B2D)
2. Sage Green (#87A96B)
3. Warm Terracotta (#C17A5B)
4. Soft Gold (#D4A574)
5. Muted Olive (#6B7B3A)

### Table Design
```css
header-background: #F0F5F0
header-color: #2C3E2C
header-font-weight: 600
row-hover: rgba(45, 91, 45, 0.04)
border-color: #B8C5B8
```

---

## Interactive States

### Hover Effects
- **Buttons:** Darken by 10-15%
- **Cards:** Subtle shadow increase
- **Links:** Underline with brand color
- **Interactive elements:** 0.2s ease transition

### Focus States
- **Color:** Natural Green (#2D5B2D)
- **Style:** 2px solid outline with 2px offset
- **Box shadow:** 0 0 0 3px rgba(45, 91, 45, 0.2)

### Loading States
- **Color:** Sage Green (#87A96B)
- **Style:** Organic, smooth animations
- **Spinners:** Avoid harsh geometric shapes

---

## Iconography

### Style Guidelines
- **Style:** Outline icons preferred over filled
- **Weight:** 1.5px stroke width
- **Size:** 16px, 20px, 24px standard sizes
- **Color:** Match text color or use brand colors for emphasis

### Brand-Specific Icons
- Use botanical/organic shapes where possible
- Leaf motifs for growth/success indicators
- Avoid overly technical or industrial icons
- Prefer rounded corners over sharp edges

---

## Messaging & Content

### Tone for Internal Apps
- **Helpful & Supportive:** Clear instructions and guidance
- **Efficient:** Concise labels and descriptions
- **Organic:** Natural language, avoid overly technical jargon
- **Positive:** Encouraging success messages

### Error Messages
```
Structure: [What happened] + [Why it matters] + [How to fix]
Tone: Helpful, not blaming
Example: "We couldn't save your changes because the connection was lost. Please check your internet and try again."
```

### Success Messages
```
Tone: Warm celebration of achievements
Example: "Your inventory update has been successfully saved! 🌱"
```

---

## Layout Patterns

### Dashboard Layout
```
┌─────────────────────────────────────────────────────┐
│ Header (64px) - Deep Forest Green                   │
├─────────────────────────────────────────────────────┤
│ Sidebar │ Main Content Area                         │
│ (280px) │ - Cards with cream/white backgrounds      │
│ Pale    │ - Natural spacing                         │
│ Green   │ - Organic flow                            │
│ BG      │                                           │
└─────────────────────────────────────────────────────┘
```

### Form Layout
- **Single column** for better focus
- **Grouped related fields** with subtle backgrounds
- **Progressive disclosure** for complex forms
- **Clear hierarchy** with proper spacing

### Data Table Layout
- **Sticky headers** for long lists
- **Alternating row colors** for readability
- **Inline actions** with icon buttons
- **Responsive design** with horizontal scroll

---

## Performance & Accessibility

### Color Contrast
- **Text on light backgrounds:** Minimum 4.5:1 ratio
- **Text on dark backgrounds:** Minimum 4.5:1 ratio
- **Interactive elements:** Minimum 3:1 ratio

### Motion
- **Reduced motion support:** Respect user preferences
- **Transition duration:** 0.2s for micro-interactions, 0.3s for larger changes
- **Easing:** Natural, organic curves (ease-out preferred)

### Loading Performance
- **Skeleton screens** using brand colors
- **Progressive loading** for better perceived performance
- **Optimized images** with proper compression

---

## Implementation Examples

### CSS Custom Properties
```css
:root {
  /* Brand Colors */
  --color-natural-green: #2D5B2D;
  --color-earth-brown: #8B4513;
  --color-cream: #FAF7F0;
  --color-forest-green: #1B3F1B;
  --color-sage-green: #87A96B;
  --color-terracotta: #C17A5B;
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  
  /* Typography */
  --font-size-body: 14px;
  --font-size-heading: 20px;
  --line-height-body: 1.5;
  --line-height-heading: 1.4;
}
```

### Component Example
```css
.app-card {
  background: var(--color-cream);
  border: 1px solid var(--color-sage-green);
  border-radius: 8px;
  padding: var(--space-lg);
  transition: box-shadow 0.2s ease;
}

.app-card:hover {
  box-shadow: 0 4px 16px rgba(45, 91, 45, 0.12);
}
```

---

## Quality Checklist

### Before Launch
- [ ] Brand colors implemented correctly
- [ ] Typography scale consistent
- [ ] Accessibility standards met (WCAG 2.1 AA)
- [ ] Responsive design tested
- [ ] Loading states implemented
- [ ] Error handling designed
- [ ] Interactive states defined
- [ ] Brand voice maintained in content

### Ongoing Maintenance
- [ ] Regular color contrast audits
- [ ] User feedback integration
- [ ] Performance monitoring
- [ ] Brand consistency reviews
- [ ] Accessibility testing updates

---

*This internal app style guide ensures that all digital tools maintain the Kasimir + Lieselotte brand identity while providing modern, efficient user experiences for daily operations.*