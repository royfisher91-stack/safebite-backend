export function formatPrice(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'Not available';
  }

  return `GBP ${value.toFixed(2)}`;
}

export function formatText(value: string | number | null | undefined, fallback = 'Not set'): string {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }

  return String(value);
}

export function listText(value: string[] | string | null | undefined): string {
  if (Array.isArray(value)) {
    return value.filter(Boolean).join(', ');
  }

  return value || '';
}

export function safetyClass(value: string | null | undefined): 'safe' | 'caution' | 'avoid' {
  const text = String(value || '').toLowerCase();

  if (text === 'safe') {
    return 'safe';
  }

  if (text === 'avoid') {
    return 'avoid';
  }

  return 'caution';
}
