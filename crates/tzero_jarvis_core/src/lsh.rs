// -*- coding: utf-8 -*-
//! T-ZERO RUST NATIVE SUB-MICROSECOND MINHASH LSH ENGINE
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.5.0

use std::collections::{HashMap, HashSet};
use crate::triplet::SemanticTriplet;

const MERSENNE_PRIME: u64 = 2147483647;
const NUM_HASHES: usize = 64;
const BANDS: usize = 16;
const ROWS_PER_BAND: usize = 4;

#[derive(Debug, Clone)]
pub struct RustMinHashSignature {
    pub triplet_code: u32,
    pub signature: [u64; NUM_HASHES],
    pub label: String,
}

impl RustMinHashSignature {
    pub fn jaccard_similarity(&self, other: &RustMinHashSignature) -> f64 {
        let mut matches = 0;
        for i in 0..NUM_HASHES {
            if self.signature[i] == other.signature[i] {
                matches += 1;
            }
        }
        matches as f64 / NUM_HASHES as f64
    }
}

pub struct RustMinHashLSH {
    pub signatures: HashMap<u32, RustMinHashSignature>,
    pub buckets: Vec<HashMap<u64, HashSet<u32>>>,
    pub hash_seeds: Vec<(u64, u64)>,
}

impl RustMinHashLSH {
    pub fn new() -> Self {
        let mut seeds = Vec::with_capacity(NUM_HASHES);
        for i in 0..NUM_HASHES {
            let a = ((i as u64 * 1664525 + 1013904223) % (MERSENNE_PRIME - 1)) + 1;
            let b = (i as u64 * 214013 + 2531011) % MERSENNE_PRIME;
            seeds.push((a, b));
        }

        Self {
            signatures: HashMap::new(),
            buckets: vec![HashMap::new(); BANDS],
            hash_seeds: seeds,
        }
    }

    fn shingle_triplet(triplet: &SemanticTriplet) -> Vec<u64> {
        let mut shingles = Vec::new();
        // Basit hash fonksiyonu ile shingle tokenları 64-bit tam sayılara dönüştür
        let mut push_token = |prefix: &str, val: &str| {
            let mut h: u64 = 5381;
            for b in prefix.bytes().chain(val.bytes()) {
                h = ((h << 5).wrapping_add(h)).wrapping_add(b as u64);
            }
            shingles.push(h % MERSENNE_PRIME);
        };

        push_token("sub:", &triplet.subject);
        push_token("prd:", &triplet.predicate);
        for o in &triplet.objects {
            push_token("obj:", &o.name);
        }
        for c in &triplet.contexts {
            push_token("ctx:", &c.name);
        }

        shingles
    }

    pub fn compute_signature(&self, triplet: &SemanticTriplet, code: u32) -> RustMinHashSignature {
        let shingles = Self::shingle_triplet(triplet);
        let mut sig = [MERSENNE_PRIME; NUM_HASHES];

        for &tok_h in &shingles {
            for i in 0..NUM_HASHES {
                let (a, b) = self.hash_seeds[i];
                let perm_val = (a.wrapping_mul(tok_h).wrapping_add(b)) % MERSENNE_PRIME;
                if perm_val < sig[i] {
                    sig[i] = perm_val;
                }
            }
        }

        RustMinHashSignature {
            triplet_code: code,
            signature: sig,
            label: triplet.to_graph_string(),
        }
    }

    pub fn insert(&mut self, triplet: &SemanticTriplet, code: u32) {
        let sig = self.compute_signature(triplet, code);

        for b_idx in 0..BANDS {
            let start = b_idx * ROWS_PER_BAND;
            let mut band_h: u64 = 0;
            for r in 0..ROWS_PER_BAND {
                band_h = band_h.wrapping_mul(31).wrapping_add(sig.signature[start + r]);
            }
            self.buckets[b_idx].entry(band_h).or_default().insert(code);
        }

        self.signatures.insert(code, sig);
    }

    pub fn query_near_duplicates(&self, triplet: &SemanticTriplet, threshold: f64) -> Vec<(u32, f64)> {
        let temp_sig = self.compute_signature(triplet, 0);
        let mut candidates = HashSet::new();

        for b_idx in 0..BANDS {
            let start = b_idx * ROWS_PER_BAND;
            let mut band_h: u64 = 0;
            for r in 0..ROWS_PER_BAND {
                band_h = band_h.wrapping_mul(31).wrapping_add(temp_sig.signature[start + r]);
            }
            if let Some(set) = self.buckets[b_idx].get(&band_h) {
                candidates.extend(set.iter().copied());
            }
        }

        let mut results = Vec::new();
        for code in candidates {
            if let Some(cand_sig) = self.signatures.get(&code) {
                let sim = temp_sig.jaccard_similarity(cand_sig);
                if sim >= threshold {
                    results.push((code, sim));
                }
            }
        }

        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        results
    }
}
