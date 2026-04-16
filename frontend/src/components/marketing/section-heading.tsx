type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  description?: string;
  align?: 'left' | 'center';
};

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = 'left'
}: SectionHeadingProps) {
  const alignment = align === 'center' ? 'text-center mx-auto' : 'text-left';

  return (
    <div className={`max-w-3xl ${alignment}`}>
      <div className="text-sm font-semibold uppercase tracking-[0.2em] text-[#4b61ff]">
        {eyebrow}
      </div>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white md:text-5xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-5 text-lg leading-8 text-white/68">{description}</p>
      ) : null}
    </div>
  );
}