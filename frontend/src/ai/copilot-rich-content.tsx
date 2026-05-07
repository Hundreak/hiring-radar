import type {ReactNode} from 'react';

import {cn} from '@/lib/utils';

type ContentBlock =
  | {kind: 'heading'; text: string}
  | {kind: 'paragraph'; lines: string[]}
  | {kind: 'unordered_list'; items: string[]}
  | {kind: 'ordered_list'; items: string[]};

function normalizeLine(raw: string): string {
  return raw.replace(/\r/g, '').trim();
}

function isHeadingLine(line: string): boolean {
  return /^\*\*[^*].+[^*]\*\*:?$/.test(line);
}

function extractHeadingText(line: string): string {
  return line.replace(/^\*\*/, '').replace(/\*\*:?$/, '').trim();
}

function isUnorderedListLine(line: string): boolean {
  return /^[-*•]\s+/.test(line);
}

function isOrderedListLine(line: string): boolean {
  return /^\d+[.)]\s+/.test(line);
}

function stripListPrefix(line: string): string {
  return line.replace(/^[-*•]\s+/, '').replace(/^\d+[.)]\s+/, '').trim();
}

function parseBlocks(content: string): ContentBlock[] {
  const lines = content.split('\n').map(normalizeLine);
  const blocks: ContentBlock[] = [];
  let paragraphBuffer: string[] = [];
  let unorderedListBuffer: string[] = [];
  let orderedListBuffer: string[] = [];

  const flushParagraph = () => {
    if (paragraphBuffer.length === 0) return;
    blocks.push({kind: 'paragraph', lines: paragraphBuffer});
    paragraphBuffer = [];
  };

  const flushUnorderedList = () => {
    if (unorderedListBuffer.length === 0) return;
    blocks.push({kind: 'unordered_list', items: unorderedListBuffer});
    unorderedListBuffer = [];
  };

  const flushOrderedList = () => {
    if (orderedListBuffer.length === 0) return;
    blocks.push({kind: 'ordered_list', items: orderedListBuffer});
    orderedListBuffer = [];
  };

  const flushAll = () => {
    flushParagraph();
    flushUnorderedList();
    flushOrderedList();
  };

  for (const line of lines) {
    if (!line) {
      flushAll();
      continue;
    }

    if (isHeadingLine(line)) {
      flushAll();
      blocks.push({kind: 'heading', text: extractHeadingText(line)});
      continue;
    }

    if (isUnorderedListLine(line)) {
      flushParagraph();
      flushOrderedList();
      unorderedListBuffer.push(stripListPrefix(line));
      continue;
    }

    if (isOrderedListLine(line)) {
      flushParagraph();
      flushUnorderedList();
      orderedListBuffer.push(stripListPrefix(line));
      continue;
    }

    flushUnorderedList();
    flushOrderedList();
    paragraphBuffer.push(line);
  }

  flushAll();
  return blocks;
}

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /\*\*(.+?)\*\*/g;
  let cursor = 0;
  let match = pattern.exec(text);

  while (match) {
    if (match.index > cursor) {
      nodes.push(text.slice(cursor, match.index));
    }
    nodes.push(
      <strong key={`${match.index}-${match[1]}`} className="font-semibold text-white dark:text-violet-50">
        {match[1]}
      </strong>,
    );
    cursor = match.index + match[0].length;
    match = pattern.exec(text);
  }

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes;
}

export function CopilotRichContent({content, className}: {content: string; className?: string}) {
  const blocks = parseBlocks(content);

  return (
    <div className={cn('space-y-3 text-sm leading-7', className)}>
      {blocks.map((block, index) => {
        if (block.kind === 'heading') {
          return (
            <div
              key={`heading-${index}`}
              className="rounded-2xl border border-violet-400/20 bg-violet-500/10 px-3 py-2 text-sm font-semibold tracking-[0.01em] text-violet-200"
            >
              {block.text}
            </div>
          );
        }

        if (block.kind === 'unordered_list') {
          return (
            <ul key={`ul-${index}`} className="space-y-2 pl-1 text-slate-200 dark:text-slate-200">
              {block.items.map((item, itemIndex) => (
                <li key={`ul-item-${index}-${itemIndex}`} className="flex gap-3">
                  <span className="mt-2.5 inline-block size-1.5 shrink-0 rounded-full bg-violet-300" />
                  <span className="min-w-0">{renderInline(item)}</span>
                </li>
              ))}
            </ul>
          );
        }

        if (block.kind === 'ordered_list') {
          return (
            <ol key={`ol-${index}`} className="space-y-2 pl-1 text-slate-200 dark:text-slate-200">
              {block.items.map((item, itemIndex) => (
                <li key={`ol-item-${index}-${itemIndex}`} className="flex gap-3">
                  <span className="inline-flex min-w-6 justify-center rounded-full border border-violet-400/25 bg-violet-500/10 px-1 py-0.5 text-xs font-semibold text-violet-200">
                    {itemIndex + 1}
                  </span>
                  <span className="min-w-0">{renderInline(item)}</span>
                </li>
              ))}
            </ol>
          );
        }

        return (
          <p key={`p-${index}`} className="whitespace-pre-wrap text-slate-200 dark:text-slate-200">
            {block.lines.map((line, lineIndex) => (
              <span key={`p-line-${index}-${lineIndex}`}>
                {renderInline(line)}
                {lineIndex < block.lines.length - 1 ? <br /> : null}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
