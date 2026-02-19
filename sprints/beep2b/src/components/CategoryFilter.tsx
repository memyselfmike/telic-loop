import type { Category } from '../lib/sanity';

export interface CategoryFilterProps {
  categories: Category[];
  currentCategory?: string; // Current category slug (if on a category page) or undefined (if on "All Posts")
  currentPath: string; // Current URL pathname for determining active state
}

/**
 * CategoryFilter - Horizontal navigation bar for blog category filtering
 *
 * Used on:
 * - Blog listing page (/blog) - currentCategory undefined, "All Posts" active
 * - Category pages (/blog/category/[slug]) - currentCategory set, that category active
 *
 * This is a React island (client:load) to allow for interactive filtering behavior.
 * Currently static links, but architected as React island to enable client-side
 * filtering enhancements in the future.
 */
export default function CategoryFilter({ categories, currentCategory, currentPath }: CategoryFilterProps) {
  // Determine if we're on the "All Posts" view (blog listing, not a category page)
  const isAllPostsActive = !currentCategory && (currentPath === '/blog' || currentPath.startsWith('/blog/') && !currentPath.includes('/category/'));

  return (
    <nav aria-label="Blog categories" className="bg-white border-b border-slate-200 px-4 py-3 sticky top-16 z-30">
      <div className="max-w-5xl mx-auto overflow-x-auto">
        <ul className="flex gap-2 min-w-max">
          {/* All Posts link */}
          <li>
            <a
              href="/blog"
              className={`inline-block px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                isAllPostsActive
                  ? 'bg-primary-800 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              All Posts
            </a>
          </li>

          {/* Category links */}
          {categories.map((cat) => {
            const isActive = currentCategory === cat.slug.current;

            return (
              <li key={cat._id}>
                <a
                  href={`/blog/category/${cat.slug.current}`}
                  className={`inline-block px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-800 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-primary-50 hover:text-primary-700'
                  }`}
                >
                  {cat.title}
                </a>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
