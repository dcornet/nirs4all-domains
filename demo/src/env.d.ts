/// <reference types="vite/client" />
declare module 'virtual:nirs4all-io' {
  export function init(): Promise<void>;
  export const inferDataset: typeof import('@nirs4all/io-wasm').inferDataset;
  export const assembleDataset: typeof import('@nirs4all/io-wasm').assembleDataset;
  export const validate: typeof import('@nirs4all/io-wasm').validate;
}
declare module 'virtual:nirs4all-formats' {
  export function init(): Promise<void>;
  export const openWithSidecars: typeof import('@nirs4all/formats-wasm').openWithSidecars;
}
