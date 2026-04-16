'use client';

import {useState} from 'react';
import {ChevronDown} from 'lucide-react';

type FaqItem = {
  question: string;
  answer: string;
};

export function FaqAccordion({items}: {items: FaqItem[]}) {
  const [openIndex, setOpenIndex] = useState<number>(0);

  return (
    <div className="space-y-4">
      {items.map((item, index) => {
        const isOpen = openIndex === index;

        return (
          <div
            key={item.question}
            className="overflow-hidden rounded-[24px] border border-white/10 bg-[#171717]"
          >
            <button
              type="button"
              onClick={() => setOpenIndex(isOpen ? -1 : index)}
              className="flex w-full items-center justify-between gap-6 px-6 py-5 text-left"
            >
              <span className="text-lg font-semibold text-white">{item.question}</span>
              <ChevronDown
                className={`size-5 shrink-0 text-[#7c8dff] transition-transform ${
                  isOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {isOpen ? (
              <div className="border-t border-white/8 px-6 py-5 text-base leading-8 text-white/68">
                {item.answer}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}