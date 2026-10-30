# Public Methods parity data

`methods-hdbscan-v1.json` is an unchanged copy of the public Methods fixture
at commit `131a15a6bbf73a8ab941c7b3fb81b21f6b71b059`:
[original fixture](https://github.com/GBeurier/nirs4all-methods/blob/131a15a6bbf73a8ab941c7b3fb81b21f6b71b059/parity/fixtures/hdbscan_v1.json).
SHA-256: `294457336e820754b5047851760ea0d02391c1c552cd9420cc80223179297cd4`.
This is synthetic test data, not copied numerical implementation. Its reference
section records generator versions, seed, self-counting min_samples and stable
MST tie rules. Eight cases cover separated/varying-density blobs, EOM/leaf,
all-noise, single-cluster allowance, continuum and duplicated/tied coordinates.
Hex strings encode big-endian IEEE-754 doubles, including nonfinite diagnostics.

The native gate calls the existing Rust adapter on each case, compares exact
labels/tree links/sizes and checks persistence/lambda/stability within abs/rel
1e-12. It executes the published Methods binary, without rebuilding upstream.
