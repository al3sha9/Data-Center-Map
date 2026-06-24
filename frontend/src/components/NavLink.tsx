import { Link } from "./Link";

export function NavLink({ href, children, ...props }: any) {
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
