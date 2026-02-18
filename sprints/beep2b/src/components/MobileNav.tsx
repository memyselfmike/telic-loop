import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetClose,
  SheetTitle,
  SheetDescription,
} from './ui/sheet';

interface NavLink {
  href: string;
  label: string;
}

interface MobileNavProps {
  links: NavLink[];
  currentPath: string;
}

export default function MobileNav({ links, currentPath }: MobileNavProps) {
  return (
    <div className="md:hidden">
      <Sheet>
        <SheetTrigger asChild>
          <button
            type="button"
            aria-label="Open navigation menu"
            className="inline-flex items-center justify-center p-2 rounded-md text-white hover:text-primary-200 hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white transition-colors"
          >
            {/* Hamburger icon */}
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
        </SheetTrigger>

        <SheetContent
          side="left"
          className="w-72 bg-brand-dark border-r-0 p-0 text-white"
        >
          <div className="flex flex-col h-full">
            {/* Sheet header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-primary-800">
              <SheetTitle className="text-white text-lg font-bold">
                <span className="text-primary-300 font-extrabold">B2B</span>{' '}
                Beep2B
              </SheetTitle>
              <SheetDescription className="sr-only">
                Site navigation menu
              </SheetDescription>
            </div>

            {/* Navigation links */}
            <nav aria-label="Mobile navigation" className="flex-1 px-4 py-3">
              <ul className="space-y-1">
                {links.map((link) => {
                  const isActive =
                    link.href === '/'
                      ? currentPath === '/'
                      : currentPath.startsWith(link.href);
                  return (
                    <li key={link.href}>
                      <SheetClose asChild>
                        <a
                          href={link.href}
                          aria-current={isActive ? 'page' : undefined}
                          className={`block px-3 py-2 rounded-md text-base font-medium transition-colors ${
                            isActive
                              ? 'bg-primary-600 text-white'
                              : 'text-white hover:bg-primary-700 hover:text-white'
                          }`}
                        >
                          {link.label}
                        </a>
                      </SheetClose>
                    </li>
                  );
                })}
              </ul>
            </nav>

            {/* CTA at bottom */}
            <div className="px-4 py-4 border-t border-primary-800">
              <SheetClose asChild>
                <a
                  href="/contact"
                  className="block w-full text-center px-4 py-2 bg-primary-500 hover:bg-primary-400 text-white text-sm font-semibold rounded-md transition-colors"
                >
                  Get Started
                </a>
              </SheetClose>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
