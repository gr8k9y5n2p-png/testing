export default function Loading() {
  return (
    <main className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <div className="h-12 animate-pulse rounded-md bg-line/70" />
      <div className="mt-8 h-10 w-2/3 animate-pulse rounded-md bg-line/70" />
      <div className="mt-3 h-4 w-1/2 animate-pulse rounded-md bg-line/60" />
      <div className="mt-10 grid gap-4 md:grid-cols-2">
        {Array.from({ length: 2 }).map((_, index) => (
          <div
            key={index}
            className="h-80 animate-pulse rounded-lg border border-line bg-surface"
          />
        ))}
      </div>
      <div className="mt-4 h-80 animate-pulse rounded-lg border border-line bg-surface" />
      <div className="mt-10 h-96 animate-pulse rounded-lg border border-line bg-surface" />
    </main>
  );
}
