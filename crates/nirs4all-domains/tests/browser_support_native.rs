//! Actual published native owner regression, separate from the transport spies.
#![cfg(feature = "native")]
use nirs4all_domains::{browser_support::SupportProvider, support_methods::SupportMethods};
use serde_json::json;

#[test]
#[ignore = "requires the pinned Methods 1.3.13 native library"]
fn unrelated_summary_and_invalid_transform_preserve_fitted_pca_until_destroy() {
    let path = std::env::var_os("N4DOMAINS_METHODS_LIBRARY").expect("N4DOMAINS_METHODS_LIBRARY");
    let provider = SupportMethods::load(std::path::Path::new(&path)).unwrap();
    let fit = provider.execute("pca_fit", &json!({"matrix":[[-3e100,0.],[-2e100,0.],[-1e100,0.],[1e100,0.],[2e100,0.],[3e100,0.]],"n_components":1})).unwrap();
    let error = provider
        .execute("summary", &json!({"values":[1e100,2e100]}))
        .unwrap_err();
    assert_eq!(error.reason, "NUMERICAL_DOMAIN_EXCEEDED");
    assert!(provider
        .execute("pca_transform", &json!({"matrix":[[1.]]}))
        .is_err());
    let projected = provider
        .execute("pca_transform", &json!({"matrix":[[0.,0.],[4e100,0.]]}))
        .unwrap();
    assert_eq!(fit["state_bytes"], projected["state_bytes"]);
    assert_eq!(projected["scores"].as_array().unwrap().len(), 2);
    provider.execute("pca_destroy", &json!({})).unwrap();
    assert!(provider
        .execute("pca_transform", &json!({"matrix":[[0.,0.]]}))
        .is_err());
}
