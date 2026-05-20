'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import ThemeToggle from './ThemeToggle';
import QualiBactLogo from './QualiBactLogo';

const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/priority-pathogens', label: 'Priority Pathogens' },
  { href: '/species', label: 'All Species' },
  { href: '/methods', label: 'Methods' },
  { href: '/compare', label: 'Compare' },
  { href: '/summary', label: 'Summary' },
  { href: '/organism-requests', label: 'Requests' },
  { href: '/contributing', label: 'Contributing' },
  { href: '/contributors', label: 'Contributors' },
  { href: '/faq', label: 'FAQ' },
];

function isActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function NavBar() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <nav className="gx-nav" aria-label="Main navigation">
      <div className="gx-nav-inner">
        <div className="gx-nav-row">
          <Link href="/" className="gx-nav-logo">
            <QualiBactLogo className="gx-nav-logo-icon" />
            <span className="gx-nav-logo-name">QualiBact</span>
          </Link>

          {/* Desktop nav */}
          <div className="gx-nav-desktop">
            {NAV_LINKS.filter((l) => l.href !== '/').map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="gx-nav-link"
                aria-current={isActive(pathname, href) ? 'page' : undefined}
              >
                {label}
              </Link>
            ))}
            <ThemeToggle />
          </div>

          {/* Mobile: theme + hamburger */}
          <div className="gx-nav-mobile-toggle">
            <ThemeToggle />
            <button
              type="button"
              onClick={() => setOpen(!open)}
              className="gx-nav-iconbtn"
              aria-expanded={open}
              aria-label="Toggle navigation menu"
            >
              {open ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {open && (
        <div className="gx-nav-dropdown">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className="gx-nav-dropdown-link"
              aria-current={isActive(pathname, href) ? 'page' : undefined}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
