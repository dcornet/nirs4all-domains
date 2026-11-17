/** Public synthetic fixture shared by actual IO and browser qualification. */
export function fixture(): {
  files: { name: string; mimeType: string; buffer: Uint8Array }[];
};
