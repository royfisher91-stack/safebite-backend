import Image from 'next/image';
import Link from 'next/link';
import { ReactNode } from 'react';

type Props = {
  children: ReactNode;
};

const navItems = [
  { href: '/products', label: 'Products' },
  { href: '/offers', label: 'Offers' },
  { href: '/import-review', label: 'Import review' },
  { href: '/login', label: 'Login' },
];

export default function AppShell({ children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand-lockup" href="/products">
          <Image
            alt="SafeBite"
            className="brand-logo"
            height={44}
            priority
            src="/safebite-logo.png"
            width={44}
          />
          <span>SafeBite</span>
        </Link>
        <nav className="side-nav" aria-label="Dashboard">
          {navItems.map((item) => (
            <Link href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="main-panel">{children}</main>
    </div>
  );
}
