//! Explicit browser provider identities; availability alone is not qualification.
pub const LEGACY: &str = "1.3.13+abi.2.20.0";
pub const CANDIDATE: &str = "1.5.1+abi.2.24.0";

pub fn admitted(version: &str) -> bool {
    matches!(version, LEGACY | CANDIDATE)
}

pub fn required_abi_minor(version: &str) -> Option<u32> {
    match version {
        LEGACY => Some(20),
        CANDIDATE => Some(24),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn only_explicit_version_and_abi_pairs_are_admitted() {
        assert!(admitted(LEGACY));
        assert!(admitted(CANDIDATE));
        for value in [
            "1.5.0+abi.2.24.0",
            "1.5.1+abi.2.20.0",
            "1.5.2+abi.2.24.0",
            "",
        ] {
            assert!(!admitted(value));
            assert_eq!(required_abi_minor(value), None);
        }
    }
}
