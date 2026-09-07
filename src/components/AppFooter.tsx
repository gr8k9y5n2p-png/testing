import { HOST } from "@/lib/copy";

export function AppFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-2 px-4 py-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>Aftertax · {HOST}</p>
        <p>Illustrative estimates only. Not tax, legal, or investment advice.</p>
      </div>
    </footer>
  );
}
