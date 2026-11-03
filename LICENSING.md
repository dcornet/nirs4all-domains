# Licensing — nirs4all-domains

`nirs4all-domains` is part of the **nirs4all ecosystem** and, like its sibling
repositories, is offered under a **dual open-source license**.

> **SPDX-License-Identifier:** `CECILL-2.1 OR AGPL-3.0-or-later`

You may use, modify and redistribute this software under the terms of **either**,
at your option:

1. the **CeCILL Free Software License Agreement, version 2.1** — full text in
   [`LICENSES/CeCILL-2.1.txt`](LICENSES/CeCILL-2.1.txt); **or**
2. the **GNU Affero General Public License, version 3.0 or (at your option) any
   later version** — full text in [`LICENSES/AGPL-3.0-or-later.txt`](LICENSES/AGPL-3.0-or-later.txt).

CeCILL-2.1 is the French GPL/AGPL-compatible license; AGPL-3.0-or-later is its
internationally recognized equivalent. The two are co-equal. The root `LICENSE`
file keeps the AGPL-3.0-or-later text so code hosts display a recognized SPDX
license; this does not diminish the CeCILL-2.1 option.

The two Rust crates (`nirs4all-domains`, `nirs4all-domains-cli`) and the Python
bridge (`nirs4all-domains-bridge`) carry the same expression. Releases up to Rust
`0.1.0-alpha.16` / bridge `0.1.0a21` were published under AGPL-3.0-or-later only.

## Dependencies

Every Rust and Python dependency is permissive (MIT, Apache-2.0, BSD, ISC, Zlib,
Unicode-3.0, PSF, MPL-2.0 for `certifi`) or an ecosystem package under
`CECILL-2.1 OR AGPL-3.0-or-later` (Preflight, DAG-ML, Datasets, nirs4all) or
CeCILL-2.1 (Methods). None requires a single copyleft license for this code.
Native Methods libraries are not redistributed here; a release that bundles
binaries must ship their own notices.

## Data

Datasets, reports and aggregates derived from them retain their source licenses
and access restrictions; this software license does not relicense data.
