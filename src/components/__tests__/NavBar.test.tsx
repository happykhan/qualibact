import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import NavBar from '../NavBar';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...rest}>{children}</a>
  ),
}));

// Mock ThemeToggle
vi.mock('../ThemeToggle', () => ({
  default: function MockThemeToggle() {
    return <button data-testid="theme-toggle">Toggle</button>;
  },
}));

describe('NavBar', () => {
  it('renders the QualiBact brand link', () => {
    render(<NavBar />);
    expect(screen.getByText('QualiBact')).toBeInTheDocument();
  });

  it('renders all navigation links', () => {
    render(<NavBar />);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Methods')).toBeInTheDocument();
    expect(screen.getByText('All Species')).toBeInTheDocument();
    expect(screen.getByText('Compare')).toBeInTheDocument();
    expect(screen.getByText('Summary')).toBeInTheDocument();
    expect(screen.getByText('FAQ')).toBeInTheDocument();
  });

  it('toggles mobile menu on hamburger click', () => {
    render(<NavBar />);
    const hamburger = screen.getByLabelText('Toggle navigation menu');
    expect(hamburger).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(hamburger);
    expect(hamburger).toHaveAttribute('aria-expanded', 'true');

    fireEvent.click(hamburger);
    expect(hamburger).toHaveAttribute('aria-expanded', 'false');
  });

  it('renders ThemeToggle', () => {
    render(<NavBar />);
    const toggles = screen.getAllByTestId('theme-toggle');
    expect(toggles.length).toBeGreaterThanOrEqual(1);
  });
});
