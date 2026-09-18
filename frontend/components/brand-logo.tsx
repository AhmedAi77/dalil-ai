import Image from "next/image";

export function BrandLogo() {
  return (
    <div className="flex items-center gap-2.5">
      <Image
        src="/contexta-logo.png"
        alt="Dalil AI"
        width={48}
        height={48}
        priority
        className="logo-glow h-11 w-11 object-contain"
      />
      <div>
        <div className="text-[15px] font-semibold tracking-[-.02em]">Dalil AI <span className="brand ms-1 font-medium">| دليل</span></div>
        <div className="text-muted text-[10px] font-medium tracking-[.16em] uppercase">Your knowledge guide</div>
      </div>
    </div>
  );
}
