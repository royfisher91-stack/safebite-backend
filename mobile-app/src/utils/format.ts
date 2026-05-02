import { SafetyResult } from '../types/api';

export function asList(value: string[] | string | null | undefined): string[] {
  if (Array.isArray(value)) {
    return value.filter((item) => String(item).trim().length > 0);
  }

  if (typeof value === 'string') {
    return value
      .split(/[|,]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

export function sentence(value: string[] | string | null | undefined, fallback: string): string {
  const items = asList(value);
  return items.length ? items.join(', ') : fallback;
}

export function formatPrice(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'Not available';
  }

  return `GBP ${value.toFixed(2)}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return 'Unknown time';
  }

  const normalised = value.includes('T') ? value : value.replace(' ', 'T');
  const parsed = new Date(normalised);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function safetyTone(result: SafetyResult | null | undefined): 'safe' | 'caution' | 'avoid' {
  const text = String(result ?? '').toLowerCase();

  if (text === 'safe') {
    return 'safe';
  }

  if (text === 'avoid') {
    return 'avoid';
  }

  return 'caution';
}
