# Navbar Export

Exact navbar export from this project. Copy these files/styles into another Next.js + Tailwind project.

## Dependencies

```bash
npm install @headlessui/react clsx
```

Requires Next.js `next/link`, React, Tailwind CSS v4 classes, and matching project fonts for identical typography.

## Navbar Items

- AI Insights -> https://ai-insights.100xbetter.ai/
- Stock Valuation Tool -> https://stockvaluecalculator.100xbetter.ai/
- AI training -> /ai-training
- About -> /about
- contact -> /contact
- Training Login -> https://course.100xbetter.ai/login

## Notes

- Header is client component because mobile popover + scroll shadow use React state/effect.
- Desktop nav appears at `md` and above.
- Mobile nav uses Headless UI Popover.
- Logo is inline SVG from current project.
- `globals.css` section is included because navbar classes depend on Tailwind v4 import/theme setup.

## src/components/Header.jsx

```jsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Popover,
  PopoverButton,
  PopoverBackdrop,
  PopoverPanel,
} from "@headlessui/react";
import clsx from "clsx";

import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { Logo } from "@/components/Logo";
import { NavLink } from "@/components/NavLink";

function MobileNavLink({ href, children, target, rel }) {
  return (
    <PopoverButton as={Link} href={href} target={target} rel={rel} prefetch={false} className="block w-full p-2">
      {children}
    </PopoverButton>
  );
}

function MobileNavIcon({ open }) {
  return (
    <svg
      aria-hidden="true"
      className="h-3.5 w-3.5 overflow-visible stroke-slate-700"
      fill="none"
      strokeWidth={2}
      strokeLinecap="round"
    >
      <path
        d="M0 1H14M0 7H14M0 13H14"
        className={clsx(
          "origin-center transition",
          open && "scale-90 opacity-0",
        )}
      />
      <path
        d="M2 2L12 12M12 2L2 12"
        className={clsx(
          "origin-center transition",
          !open && "scale-90 opacity-0",
        )}
      />
    </svg>
  );
}

function MobileNavigation() {
  return (
    <Popover>
      <PopoverButton
        className="relative z-10 flex h-8 w-8 items-center justify-center focus:not-data-focus:outline-hidden"
        aria-label="Toggle Navigation"
      >
        {({ open }) => <MobileNavIcon open={open} />}
      </PopoverButton>
      <PopoverBackdrop
        transition
        className="fixed inset-0 bg-slate-300/50 duration-75 data-closed:opacity-0 data-enter:ease-out data-leave:ease-in"
      />
      <PopoverPanel
        transition
        className="absolute inset-x-0 top-full mt-4 flex origin-top flex-col rounded-2xl bg-white p-4 text-lg tracking-tight text-slate-900 ring-1 shadow-xl ring-slate-900/5 data-closed:scale-95 data-closed:opacity-0 data-enter:duration-75 data-enter:ease-out data-leave:duration-75 data-leave:ease-in"
      >
        <MobileNavLink
          href="https://ai-insights.100xbetter.ai/"
          target="_blank"
          rel="noopener noreferrer"
        >
          AI Insights
        </MobileNavLink>
        <MobileNavLink
          href="https://stockvaluecalculator.100xbetter.ai/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Stock Valuation Tool
        </MobileNavLink>
        <MobileNavLink href="/ai-training">AI training</MobileNavLink>
        <MobileNavLink href="/about">About</MobileNavLink>
        <MobileNavLink href="/contact">contact</MobileNavLink>
        <MobileNavLink
          href="https://course.100xbetter.ai/login"
          target="_blank"
          rel="noopener noreferrer"
        >
          Training Login
        </MobileNavLink>
      </PopoverPanel>
    </Popover>
  );
}

export function Header() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 0);
    };

    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={clsx(
        "sticky top-0 z-50 md:bg-transparent sm:bg-white  py-2",
        scrolled &&
          "md:shadow-md md:bg-white/70 bg-white md:backdrop-blur md:supports-[backdrop-filter]:bg-white/60 transition-shadow",
      )}
    >
      <Container>
        <nav className="relative z-50 flex justify-between">
          <div className="flex items-center md:gap-x-12">
            <Link href="/" className="100xbetter" aria-label="Home">
              <Logo className="h-6 w-auto" />
            </Link>
            <div className="hidden md:flex md:gap-x-6 items-center">
              <NavLink
                href="https://ai-insights.100xbetter.ai/"
                target="_blank"
                rel="noopener noreferrer"
              >
                AI Insights
              </NavLink>
              <NavLink
                href="https://stockvaluecalculator.100xbetter.ai/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Stock Valuation Tool
              </NavLink>
              <NavLink href="/ai-training">AI training</NavLink>
              <NavLink href="/about">About</NavLink>
              <NavLink href="/contact">contact</NavLink>
              <NavLink
                href="https://course.100xbetter.ai/login"
                target="_blank"
                rel="noopener noreferrer"
              >
                Training Login
              </NavLink>
            </div>
          </div>
          <div className="flex items-center gap-x-5 md:gap-x-8">
            <div className="-mr-1 md:hidden">
              <MobileNavigation />
            </div>
          </div>
        </nav>
      </Container>
    </header>
  );
}

```

## src/components/NavLink.jsx

```jsx
import Link from "next/link";

export function NavLink({ href, children, ...props }) {
  return (
    <Link
      href={href}
      {...props}
      className="inline-block rounded-lg px-2 py-1 text-sm text-slate-700 hover:bg-slate-100 hover:text-slate-900"
    >
      {children}
    </Link>
  );
}

```

## src/components/Container.jsx

```jsx
import clsx from 'clsx'

export function Container({ className, ...props }) {
  return (
    <div
      className={clsx('mx-auto max-w-7xl px-4 sm:px-6 lg:px-8', className)}
      {...props}
    />
  )
}

```

## src/components/Logo.jsx

```jsx
import { useId } from "react";

export function Logo(props) {
  const uniqueId = useId();
  const gradientId = `paint0_linear_2091_4_${uniqueId}`;
  return (
    <svg
      width="100"
      height="60"
      viewBox="0 0 1200 800"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="100" height="60" fill="white" />
      <path
        d="M118.95 160.25V128.01H183.43V354H147.78V160.25H118.95ZM231.979 238.06C231.979 202.307 237.972 174.407 249.959 154.36C262.152 134.107 283.026 123.98 312.579 123.98C342.132 123.98 362.902 134.107 374.889 154.36C387.082 174.407 393.179 202.307 393.179 238.06C393.179 274.227 387.082 302.54 374.889 323C362.902 343.253 342.132 353.38 312.579 353.38C283.026 353.38 262.152 343.253 249.959 323C237.972 302.54 231.979 274.227 231.979 238.06ZM358.459 238.06C358.459 221.32 357.322 207.163 355.049 195.59C352.982 184.017 348.642 174.613 342.029 167.38C335.416 159.94 325.599 156.22 312.579 156.22C299.559 156.22 289.742 159.94 283.129 167.38C276.516 174.613 272.072 184.017 269.799 195.59C267.732 207.163 266.699 221.32 266.699 238.06C266.699 255.42 267.732 269.99 269.799 281.77C271.866 293.55 276.206 303.057 282.819 310.29C289.639 317.523 299.559 321.14 312.579 321.14C325.599 321.14 335.416 317.523 342.029 310.29C348.849 303.057 353.292 293.55 355.359 281.77C357.426 269.99 358.459 255.42 358.459 238.06ZM430.573 238.06C430.573 202.307 436.566 174.407 448.553 154.36C460.746 134.107 481.619 123.98 511.173 123.98C540.726 123.98 561.496 134.107 573.483 154.36C585.676 174.407 591.773 202.307 591.773 238.06C591.773 274.227 585.676 302.54 573.483 323C561.496 343.253 540.726 353.38 511.173 353.38C481.619 353.38 460.746 343.253 448.553 323C436.566 302.54 430.573 274.227 430.573 238.06ZM557.053 238.06C557.053 221.32 555.916 207.163 553.643 195.59C551.576 184.017 547.236 174.613 540.623 167.38C534.009 159.94 524.193 156.22 511.173 156.22C498.153 156.22 488.336 159.94 481.723 167.38C475.109 174.613 470.666 184.017 468.393 195.59C466.326 207.163 465.293 221.32 465.293 238.06C465.293 255.42 466.326 269.99 468.393 281.77C470.459 293.55 474.799 303.057 481.413 310.29C488.233 317.523 498.153 321.14 511.173 321.14C524.193 321.14 534.009 317.523 540.623 310.29C547.443 303.057 551.886 293.55 553.953 281.77C556.019 269.99 557.053 255.42 557.053 238.06ZM706.976 267.51L762.156 354H722.166L685.276 296.03L650.556 354H613.666L668.846 269.99L613.666 183.19H653.656L690.546 241.16L725.266 183.19H762.156L706.976 267.51ZM243.57 553.33C255.143 555.397 264.96 561.493 273.02 571.62C281.08 581.747 285.11 593.217 285.11 606.03C285.11 616.983 282.217 626.903 276.43 635.79C270.85 644.47 262.687 651.393 251.94 656.56C241.193 661.52 228.69 664 214.43 664H128.25V448.55H210.4C225.073 448.55 237.68 451.03 248.22 455.99C258.76 460.95 266.717 467.667 272.09 476.14C277.463 484.407 280.15 493.707 280.15 504.04C280.15 516.44 276.843 526.773 270.23 535.04C263.617 543.307 254.73 549.403 243.57 553.33ZM163.59 539.07H207.3C218.873 539.07 227.863 536.487 234.27 531.32C240.883 525.947 244.19 518.3 244.19 508.38C244.19 498.667 240.883 491.123 234.27 485.75C227.863 480.17 218.873 477.38 207.3 477.38H163.59V539.07ZM211.33 635.17C223.317 635.17 232.72 632.277 239.54 626.49C246.36 620.703 249.77 612.643 249.77 602.31C249.77 591.77 246.153 583.4 238.92 577.2C231.687 571 222.077 567.9 210.09 567.9H163.59V635.17H211.33ZM480.064 574.41C480.064 580.817 479.65 586.603 478.824 591.77H348.314C349.347 605.41 354.41 616.363 363.504 624.63C372.597 632.897 383.757 637.03 396.984 637.03C415.997 637.03 429.43 629.073 437.284 613.16H475.414C470.247 628.867 460.844 641.783 447.204 651.91C433.77 661.83 417.03 666.79 396.984 666.79C380.657 666.79 365.984 663.173 352.964 655.94C340.15 648.5 330.024 638.167 322.584 624.94C315.35 611.507 311.734 596.007 311.734 578.44C311.734 560.873 315.247 545.477 322.274 532.25C329.507 518.817 339.53 508.483 352.344 501.25C365.364 494.017 380.244 490.4 396.984 490.4C413.104 490.4 427.467 493.913 440.074 500.94C452.68 507.967 462.497 517.887 469.524 530.7C476.55 543.307 480.064 557.877 480.064 574.41ZM443.174 563.25C442.967 550.23 438.317 539.793 429.224 531.94C420.13 524.087 408.867 520.16 395.434 520.16C383.24 520.16 372.804 524.087 364.124 531.94C355.444 539.587 350.277 550.023 348.624 563.25H443.174ZM556.072 522.02V616.57C556.072 622.977 557.518 627.627 560.412 630.52C563.512 633.207 568.678 634.55 575.912 634.55H597.612V664H569.712C553.798 664 541.605 660.28 533.132 652.84C524.658 645.4 520.422 633.31 520.422 616.57V522.02H500.272V493.19H520.422V450.72H556.072V493.19H597.612V522.02H556.072ZM671.414 522.02V616.57C671.414 622.977 672.86 627.627 675.754 630.52C678.854 633.207 684.02 634.55 691.254 634.55H712.954V664H685.054C669.14 664 656.947 660.28 648.474 652.84C640 645.4 635.764 633.31 635.764 616.57V522.02H615.614V493.19H635.764V450.72H671.414V493.19H712.954V522.02H671.414ZM902.075 574.41C902.075 580.817 901.662 586.603 900.835 591.77H770.325C771.359 605.41 776.422 616.363 785.515 624.63C794.609 632.897 805.769 637.03 818.995 637.03C838.009 637.03 851.442 629.073 859.295 613.16H897.425C892.259 628.867 882.855 641.783 869.215 651.91C855.782 661.83 839.042 666.79 818.995 666.79C802.669 666.79 787.995 663.173 774.975 655.94C762.162 648.5 752.035 638.167 744.595 624.94C737.362 611.507 733.745 596.007 733.745 578.44C733.745 560.873 737.259 545.477 744.285 532.25C751.519 518.817 761.542 508.483 774.355 501.25C787.375 494.017 802.255 490.4 818.995 490.4C835.115 490.4 849.479 493.913 862.085 500.94C874.692 507.967 884.509 517.887 891.535 530.7C898.562 543.307 902.075 557.877 902.075 574.41ZM865.185 563.25C864.979 550.23 860.329 539.793 851.235 531.94C842.142 524.087 830.879 520.16 817.445 520.16C805.252 520.16 794.815 524.087 786.135 531.94C777.455 539.587 772.289 550.023 770.635 563.25H865.185ZM972.194 517.99C977.36 509.31 984.18 502.593 992.654 497.84C1001.33 492.88 1011.56 490.4 1023.34 490.4V526.98H1014.35C1000.51 526.98 989.967 530.493 982.734 537.52C975.707 544.547 972.194 556.74 972.194 574.1V664H936.854V493.19H972.194V517.99Z"
        fill="url(#paint0_linear_2105_6)"
      />
      <defs>
        <linearGradient
          id="paint0_linear_2105_6"
          x1="105"
          y1="639.59"
          x2="979.365"
          y2="14.925"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#4F39F6" stopOpacity="0.952941" />
        </linearGradient>
      </defs>
    </svg>
  );
}

```

## src/app/globals.css

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);
  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);
  --font-sans: var(--font-inter);
  --font-display: var(--font-lexend);
}

:root {
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: oklch(0.145 0 0);
  --sidebar-primary: oklch(0.205 0 0);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.97 0 0);
  --sidebar-accent-foreground: oklch(0.205 0 0);
  --sidebar-border: oklch(0.922 0 0);
  --sidebar-ring: oklch(0.708 0 0);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.205 0 0);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.205 0 0);
  --popover-foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.269 0 0);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.556 0 0);
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
  --sidebar: oklch(0.205 0 0);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.488 0.243 264.376);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.269 0 0);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(1 0 0 / 10%);
  --sidebar-ring: oklch(0.556 0 0);
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}

html {
  scroll-behavior: smooth;
}

/* width */
::-webkit-scrollbar {
  width: 10px;
}

/* Track */
::-webkit-scrollbar-track {
  background-color: transparent;
}

/* Handle */
::-webkit-scrollbar-thumb {
  background: #4f39f6;
  border-radius: 10px;
  box-shadow:;
}

/* Handle on hover */
::-webkit-scrollbar-thumb:hover {
  background: #4f39f6;
}

```
