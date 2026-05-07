type LegalSection = {
  title: string;
  paragraphs?: string[];
  bullets?: string[];
};

export function LegalSections({sections}: {sections: LegalSection[]}) {
  return (
    <div className="space-y-10">
      {sections.map((section) => (
        <section key={section.title} className="rounded-[28px] border border-white/10 bg-[#171717] p-7 md:p-9">
          <h2 className="text-2xl font-semibold tracking-tight text-white">{section.title}</h2>

          {section.paragraphs?.map((paragraph) => (
            <p key={paragraph} className="mt-5 text-base leading-8 text-white/68">
              {paragraph}
            </p>
          ))}

          {section.bullets ? (
            <ul className="mt-5 space-y-3 text-base leading-8 text-white/68">
              {section.bullets.map((bullet) => (
                <li key={bullet} className="flex gap-3">
                  <span className="mt-[11px] size-2 shrink-0 rounded-full bg-[#6276ff]" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ))}
    </div>
  );
}