const khmerDigits = ['០', '១', '២', '៣', '៤', '៥', '៦', '៧', '៨', '៩'];

export function toKhmerDigits(value: string): string {
  return value.replace(/\d/g, (digit) => khmerDigits[Number(digit)] ?? digit);
}

/** Section and project indexes: `2` becomes `02`, or `០២` in Khmer. */
export function formatIndex(index: number, language: 'en' | 'km'): string {
  const padded = String(index).padStart(2, '0');
  return language === 'km' ? toKhmerDigits(padded) : padded;
}
