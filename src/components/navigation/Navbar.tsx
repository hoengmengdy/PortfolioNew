import { Menu, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useActiveSection } from '../../hooks/useActiveSection';
import { useLanguage } from '../../hooks/useLanguage';
import { useScrolledPast } from '../../hooks/useScrolledPast';
import { CvButton } from '../ui/CvButton';
import { LogoMark } from '../ui/Logo';
import { LanguageSwitcher } from './LanguageSwitcher';
import { navItems } from './navItems';
import { ThemeToggle } from './ThemeToggle';

export function Navbar() {
  const { t } = useLanguage();
  const active = useActiveSection(navItems);
  const scrolled = useScrolledPast(24);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDialogElement>(null);

  // A native modal dialog provides the focus trap, Escape key, and focus restoration.
  useEffect(() => {
    const menu = menuRef.current;
    if (!menu) return;
    if (menuOpen && !menu.open) menu.showModal();
    if (!menuOpen && menu.open) menu.close();
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-40 border-b transition-colors duration-300 ${
        scrolled
          ? 'border-line bg-[var(--glass)] backdrop-blur-md'
          : 'border-transparent bg-transparent'
      }`}
    >
      <div className="wrap flex h-[4.5rem] items-center justify-between gap-4">
        <a href="#home" className="flex items-center gap-3" aria-label={t.common.name}>
          <LogoMark className="size-9 shrink-0" />
          <span className="hidden font-display text-sm font-semibold tracking-[0.18em] uppercase sm:block">
            {t.common.name}
          </span>
        </a>

        <nav aria-label={t.nav.label} className="hidden xl:block">
          <ul className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = active === item;
              return (
                <li key={item}>
                  <a
                    href={`#${item}`}
                    aria-current={isActive ? 'true' : undefined}
                    className={`group relative block px-3 py-2 text-sm transition-colors ${
                      isActive ? 'text-gold-text' : 'text-muted hover:text-fg'
                    }`}
                  >
                    {t.nav[item]}
                    <span
                      aria-hidden="true"
                      className={`absolute inset-x-3 bottom-1 h-px origin-left bg-gold transition-transform duration-300 ${
                        isActive ? 'scale-x-100' : 'scale-x-0 group-hover:scale-x-100'
                      }`}
                    />
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
          <CvButton
            downloadLabel={t.nav.downloadCv}
            requestLabel={t.nav.requestCv}
            className="btn btn-line hidden xl:inline-flex"
          />
          <button
            type="button"
            aria-label={t.nav.openMenu}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(true)}
            className="grid size-10 place-items-center rounded-full border border-line transition-colors hover:border-gold xl:hidden"
          >
            <Menu aria-hidden="true" className="size-5" />
          </button>
        </div>
      </div>

      <dialog
        ref={menuRef}
        aria-label={t.nav.label}
        onClose={closeMenu}
        className="nav-dialog xl:hidden"
      >
        <div className="wrap flex h-full flex-col overflow-y-auto pb-8">
          <div className="flex h-[4.5rem] shrink-0 items-center justify-between">
            <LogoMark className="size-9" />
            <button
              type="button"
              aria-label={t.nav.closeMenu}
              onClick={closeMenu}
              className="grid size-10 place-items-center rounded-full border border-line transition-colors hover:border-gold"
            >
              <X aria-hidden="true" className="size-5" />
            </button>
          </div>
          <nav aria-label={t.nav.label} className="mt-6 flex-1">
            <ul>
              {navItems.map((item) => (
                <li key={item} className="border-b border-line">
                  <a
                    href={`#${item}`}
                    onClick={closeMenu}
                    aria-current={active === item ? 'true' : undefined}
                    className={`block py-4 font-display text-2xl ${
                      active === item ? 'text-gold-text' : 'text-fg'
                    }`}
                  >
                    {t.nav[item]}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <CvButton
            downloadLabel={t.nav.downloadCv}
            requestLabel={t.nav.requestCv}
            onClick={closeMenu}
            className="btn btn-gold mt-8 w-full"
          />
        </div>
      </dialog>
    </header>
  );
}
