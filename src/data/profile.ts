/**
 * Facts only Hoeng Mengdy can confirm. Everything starts unset and the site adapts,
 * so nothing false is ever shown. Fill these in as they are confirmed.
 */
export const profile = {
  name: 'Hoeng Mengdy',
  /** Path to a real photo in `public/images`, e.g. '/images/hoeng-mengdy.webp'. */
  photo: null as string | null,
  /** Path to the CV in `public`, e.g. '/hoeng-mengdy-cv.pdf'. Unset, buttons offer "Request CV". */
  cvUrl: '/hoeng-meng-dy-cv.pdf' as string | null,
  /** Set to true only when actively open to opportunities. Shows the availability badge. */
  availableForOpportunities: false,
};
