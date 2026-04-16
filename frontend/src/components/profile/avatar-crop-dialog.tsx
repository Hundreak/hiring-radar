'use client';

import {useEffect, useMemo, useRef, useState} from 'react';
import type {PointerEvent as ReactPointerEvent} from 'react';
import Image from 'next/image';
import {Move, ZoomIn} from 'lucide-react';

type Position = {x: number; y: number};
type ImageDimensions = {width: number; height: number};

const VIEWPORT_SIZE = 320;
const MIN_ZOOM = 0.78;
const MAX_ZOOM = 2.6;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

async function loadImageElement(imageUrl: string): Promise<HTMLImageElement> {
  return await new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new window.Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Görsel işlenemedi.'));
    image.src = imageUrl;
  });
}

async function loadImageDimensions(imageUrl: string): Promise<ImageDimensions> {
  const image = await loadImageElement(imageUrl);
  return {width: image.naturalWidth || image.width, height: image.naturalHeight || image.height};
}

function drawAvatarComposition({
  context,
  image,
  imageDimensions,
  position,
  zoom,
  outputSize,
}: {
  context: CanvasRenderingContext2D;
  image: HTMLImageElement;
  imageDimensions: ImageDimensions;
  position: Position;
  zoom: number;
  outputSize: number;
}) {
  const baseScale = Math.max(outputSize / imageDimensions.width, outputSize / imageDimensions.height);
  const effectiveScale = baseScale * zoom;
  const positionScale = outputSize / VIEWPORT_SIZE;

  const drawWidth = imageDimensions.width * effectiveScale;
  const drawHeight = imageDimensions.height * effectiveScale;
  const drawX = (outputSize - drawWidth) / 2 + position.x * positionScale;
  const drawY = (outputSize - drawHeight) / 2 + position.y * positionScale;

  const backdropScale = Math.max(outputSize / imageDimensions.width, outputSize / imageDimensions.height) * 1.12;
  const backdropWidth = imageDimensions.width * backdropScale;
  const backdropHeight = imageDimensions.height * backdropScale;
  const backdropX = (outputSize - backdropWidth) / 2 + position.x * positionScale * 0.18;
  const backdropY = (outputSize - backdropHeight) / 2 + position.y * positionScale * 0.18;

  context.clearRect(0, 0, outputSize, outputSize);

  context.save();
  context.filter = 'blur(26px)';
  context.globalAlpha = 0.6;
  context.drawImage(image, backdropX, backdropY, backdropWidth, backdropHeight);
  context.restore();

  context.save();
  context.fillStyle = 'rgba(15, 23, 42, 0.05)';
  context.fillRect(0, 0, outputSize, outputSize);
  context.restore();

  context.drawImage(image, drawX, drawY, drawWidth, drawHeight);
}

async function renderAvatarBlob(
  imageUrl: string,
  imageDimensions: ImageDimensions,
  position: Position,
  zoom: number,
  outputSize = 512,
): Promise<Blob> {
  const image = await loadImageElement(imageUrl);
  const canvas = document.createElement('canvas');
  canvas.width = outputSize;
  canvas.height = outputSize;
  const context = canvas.getContext('2d');
  if (!context) {
    throw new Error('Görsel işleme başlatılamadı.');
  }

  drawAvatarComposition({context, image, imageDimensions, position, zoom, outputSize});

  return await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error('Görsel dışa aktarılamadı.'));
    }, 'image/jpeg', 0.92);
  });
}

async function renderAvatarPreviewUrl(
  imageUrl: string,
  imageDimensions: ImageDimensions,
  position: Position,
  zoom: number,
  outputSize = VIEWPORT_SIZE,
): Promise<string> {
  const image = await loadImageElement(imageUrl);
  const canvas = document.createElement('canvas');
  canvas.width = outputSize;
  canvas.height = outputSize;
  const context = canvas.getContext('2d');
  if (!context) {
    throw new Error('Önizleme hazırlanamadı.');
  }

  drawAvatarComposition({context, image, imageDimensions, position, zoom, outputSize});
  return canvas.toDataURL('image/jpeg', 0.9);
}

export function AvatarCropDialog({
  open,
  imageUrl,
  filename,
  onClose,
  onConfirm,
  saving = false,
}: {
  open: boolean;
  imageUrl: string | null;
  filename: string | null;
  onClose: () => void;
  onConfirm: (file: File) => Promise<void> | void;
  saving?: boolean;
}) {
  if (!open || !imageUrl) {
    return null;
  }

  return (
    <AvatarCropDialogInner
      key={`${imageUrl}:${open ? 'open' : 'closed'}`}
      imageUrl={imageUrl}
      filename={filename}
      onClose={onClose}
      onConfirm={onConfirm}
      saving={saving}
    />
  );
}

function AvatarCropDialogInner({
  imageUrl,
  filename,
  onClose,
  onConfirm,
  saving,
}: {
  imageUrl: string;
  filename: string | null;
  onClose: () => void;
  onConfirm: (file: File) => Promise<void> | void;
  saving: boolean;
}) {
  const dragStartRef = useRef<{x: number; y: number; initialX: number; initialY: number} | null>(null);
  const [position, setPosition] = useState<Position>({x: 0, y: 0});
  const [zoom, setZoom] = useState(1);
  const [imageDimensions, setImageDimensions] = useState<ImageDimensions | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    let cancelled = false;

    void loadImageDimensions(imageUrl)
      .then((dimensions) => {
        if (!cancelled) {
          setImageDimensions(dimensions);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setImageDimensions({width: VIEWPORT_SIZE, height: VIEWPORT_SIZE});
        }
      });

    return () => {
      cancelled = true;
    };
  }, [imageUrl]);

  const geometry = useMemo(() => {
    if (!imageDimensions) {
      return {
        width: VIEWPORT_SIZE,
        height: VIEWPORT_SIZE,
        maxOffsetX: VIEWPORT_SIZE * 0.28,
        maxOffsetY: VIEWPORT_SIZE * 0.28,
      };
    }

    const baseScale = Math.max(VIEWPORT_SIZE / imageDimensions.width, VIEWPORT_SIZE / imageDimensions.height);
    const effectiveScale = baseScale * zoom;
    const width = imageDimensions.width * effectiveScale;
    const height = imageDimensions.height * effectiveScale;

    return {
      width,
      height,
      maxOffsetX: Math.max(18, Math.abs(width - VIEWPORT_SIZE) / 2),
      maxOffsetY: Math.max(18, Math.abs(height - VIEWPORT_SIZE) / 2),
    };
  }, [imageDimensions, zoom]);

  const clampedPosition = useMemo(
    () => ({
      x: clamp(position.x, -geometry.maxOffsetX, geometry.maxOffsetX),
      y: clamp(position.y, -geometry.maxOffsetY, geometry.maxOffsetY),
    }),
    [geometry.maxOffsetX, geometry.maxOffsetY, position.x, position.y],
  );

  useEffect(() => {
    if (!imageDimensions) {
      return;
    }

    let cancelled = false;

    void renderAvatarPreviewUrl(imageUrl, imageDimensions, clampedPosition, zoom)
      .then((url) => {
        if (!cancelled) {
          setPreviewUrl(url);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPreviewUrl(imageUrl);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [imageUrl, imageDimensions, clampedPosition, zoom]);

  async function handleConfirm() {
    if (!imageDimensions) return;
    const blob = await renderAvatarBlob(imageUrl, imageDimensions, clampedPosition, zoom);
    const safeName = (filename || 'avatar').replace(/\.[^.]+$/, '');
    const file = new File([blob], `${safeName}-avatar.jpg`, {type: 'image/jpeg'});
    await onConfirm(file);
  }

  function onPointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    dragStartRef.current = {
      x: event.clientX,
      y: event.clientY,
      initialX: clampedPosition.x,
      initialY: clampedPosition.y,
    };
    setIsDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (!dragStartRef.current) return;

    const deltaX = event.clientX - dragStartRef.current.x;
    const deltaY = event.clientY - dragStartRef.current.y;

    setPosition({
      x: clamp(dragStartRef.current.initialX + deltaX, -geometry.maxOffsetX, geometry.maxOffsetX),
      y: clamp(dragStartRef.current.initialY + deltaY, -geometry.maxOffsetY, geometry.maxOffsetY),
    });
  }

  function onPointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    dragStartRef.current = null;
    setIsDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/35 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
        <div className="w-full max-w-3xl rounded-[32px] border border-border bg-background shadow-[0_30px_120px_-40px_rgba(15,23,42,0.55)]">
          <div className="flex flex-col gap-6 p-6 sm:p-8 lg:flex-row lg:items-stretch">
            <div className="flex-1 space-y-4">
              <div>
                <div className="text-xl font-semibold tracking-tight text-foreground">Profil fotoğrafını yerleştir</div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Fotoğrafını daire içine sürükleyip tam oturt. İstersen biraz uzaklaştırabilir, istersen yakınlaştırıp yüzünü merkeze alabilirsin.
                </p>
              </div>

              <div className="rounded-[28px] border border-border bg-muted/20 p-4">
                <div
                  className={`relative mx-auto flex aspect-square w-full max-w-[320px] items-center justify-center overflow-hidden rounded-full border border-border bg-background shadow-inner select-none touch-none ${
                    isDragging ? 'cursor-grabbing' : 'cursor-grab'
                  }`}
                  onPointerDown={onPointerDown}
                  onPointerMove={onPointerMove}
                  onPointerUp={onPointerUp}
                  onPointerCancel={onPointerUp}
                >
                  {previewUrl ? (
                    <Image
                      src={previewUrl}
                      alt="Avatar önizleme"
                      unoptimized
                      draggable={false}
                      fill
                      sizes="320px"
                      className="pointer-events-none absolute inset-0 h-full w-full select-none object-cover"
                    />
                  ) : (
                    <Image
                      src={imageUrl}
                      alt="Avatar önizleme"
                      unoptimized
                      draggable={false}
                      fill
                      sizes="320px"
                      className="pointer-events-none absolute inset-0 h-full w-full select-none object-cover opacity-80"
                    />
                  )}
                </div>
              </div>
            </div>

            <div className="w-full space-y-5 lg:max-w-sm">
              <div className="rounded-[24px] border border-border bg-muted/15 p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <Move className="size-4" />
                  Konumlandırma
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Fotoğrafı fare veya parmağınla sürükleyebilirsin. Alanın üzerinde el simgesi görünür; tutup bırakman yeterli olur.
                </p>
              </div>

              <div className="rounded-[24px] border border-border bg-muted/15 p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <ZoomIn className="size-4" />
                  Yakınlaştırma / Uzaklaştırma
                </div>
                <input
                  type="range"
                  min={MIN_ZOOM}
                  max={MAX_ZOOM}
                  step={0.01}
                  value={zoom}
                  onChange={(event) => setZoom(Number(event.target.value))}
                  className="mt-4 w-full"
                />
                <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Daha geniş görünüm</span>
                  <span>Daha yakın görünüm</span>
                </div>
              </div>

              <div className="rounded-[24px] border border-border bg-muted/15 p-5 text-sm leading-6 text-muted-foreground">
                Buradaki önizleme ile profil alanında göreceğin sonuç aynı kırpma mantığıyla hazırlanır. Böylece kaydettikten sonra sürpriz bir görünüm oluşmaz.
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={saving || !imageDimensions}
                  className="inline-flex h-11 flex-1 items-center justify-center rounded-2xl bg-foreground px-5 text-sm font-medium text-background transition hover:opacity-95 disabled:opacity-60"
                >
                  {saving ? 'Kaydediliyor...' : 'Fotoğrafı Kaydet'}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={saving}
                  className="inline-flex h-11 items-center justify-center rounded-2xl border border-border bg-background px-5 text-sm font-medium text-foreground transition hover:bg-muted/50 disabled:opacity-60"
                >
                  Vazgeç
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
