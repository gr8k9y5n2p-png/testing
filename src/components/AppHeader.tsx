import Image from "next/image";
import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { HOST } from "@/lib/copy";

export function AppHeader() {
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-4 sm:gap-6">
          <Link href="/" aria-label="Aftertax home" className="flex items-center gap-2.5">
            <Image
              src="/aftertax-monogram.png"
              alt=""
              width={32}
              height={33}
              sizes="32px"
              className="h-8 w-auto"
              priority
            />
            <p className="font-serif text-[15px] leading-tight tracking-tight text-ink">
              Aftertax
            </p>
          </Link>
          <AppNav />
        </div>
        <p className="hidden text-right text-xs text-muted sm:block">
          Taxable impact in dollars
          <span className="mt-0.5 block text-faint">{HOST}</span>
        </p>
      </div>
    </header>
  );
}
