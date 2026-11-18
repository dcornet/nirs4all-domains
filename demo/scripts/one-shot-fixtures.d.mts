export interface OneShotFixtureFile {
  readonly name: string;
  readonly text: string;
}

export interface OneShotFixtureCase {
  readonly id: string;
  readonly expected: 'loaded' | 'needs_input';
  readonly files: readonly OneShotFixtureFile[];
  readonly na?: string;
  readonly review?: { readonly metadataCoverage: 'allow_missing' };
}

export declare const oneShotFixtureCases: readonly OneShotFixtureCase[];

export declare function filesForOneShotCase(id: string): { name: string; bytes: Uint8Array }[];
