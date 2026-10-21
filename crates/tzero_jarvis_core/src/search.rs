// -*- coding: utf-8 -*-
//! T-ZERO RUST NATIVE ZERO-VECTOR-DB HYBRID IN-MEMORY SEARCH
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.4.0

use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone)]
pub struct IndexedDoc {
    pub id: String,
    pub title: String,
    pub content: String,
    pub discrete_code: Option<u32>,
    pub domain: String,
    pub tokens: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct SearchHit {
    pub id: String,
    pub title: String,
    pub score: f64,
    pub discrete_code: Option<u32>,
    pub domain: String,
}

#[derive(Debug, Default)]
pub struct InvertedSearchEngine {
    pub documents: HashMap<String, IndexedDoc>,
    pub inverted_index: HashMap<String, HashSet<String>>,
    pub code_index: HashMap<u32, HashSet<String>>,
    pub doc_lengths: HashMap<String, usize>,
    pub avg_doc_len: f64,
    pub k1: f64,
    pub b: f64,
}

impl InvertedSearchEngine {
    pub fn new() -> Self {
        Self {
            documents: HashMap::new(),
            inverted_index: HashMap::new(),
            code_index: HashMap::new(),
            doc_lengths: HashMap::new(),
            avg_doc_len: 0.0,
            k1: 1.5,
            b: 0.75,
        }
    }

    pub fn tokenize(text: &str) -> Vec<String> {
        text.to_lowercase()
            .split(|c: char| !c.is_alphanumeric() && c != '#')
            .filter(|w| w.len() > 1)
            .map(|s| s.to_string())
            .collect()
    }

    pub fn add_document(&mut self, id: &str, title: &str, content: &str, discrete_code: Option<u32>, domain: &str) {
        let combined = format!("{} {} {}", title, content, domain);
        let tokens = Self::tokenize(&combined);
        let len = tokens.len();

        let doc = IndexedDoc {
            id: id.to_string(),
            title: title.to_string(),
            content: content.to_string(),
            discrete_code,
            domain: domain.to_string(),
            tokens: tokens.clone(),
        };

        for tok in tokens.iter() {
            self.inverted_index.entry(tok.clone()).or_default().insert(id.to_string());
        }

        if let Some(code) = discrete_code {
            self.code_index.entry(code).or_default().insert(id.to_string());
        }

        self.doc_lengths.insert(id.to_string(), len);
        self.documents.insert(id.to_string(), doc);

        let total_len: usize = self.doc_lengths.values().sum();
        self.avg_doc_len = total_len as f64 / self.documents.len().max(1) as f64;
    }

    pub fn search(&self, query: &str, top_k: usize) -> Vec<SearchHit> {
        let q_tokens = Self::tokenize(query);
        let mut scores: HashMap<String, f64> = HashMap::new();
        let n_docs = self.documents.len() as f64;

        for tok in &q_tokens {
            if let Some(postings) = self.inverted_index.get(tok) {
                let df = postings.len() as f64;
                let idf = (1.0 + (n_docs - df + 0.5) / (df + 0.5)).ln();

                for doc_id in postings {
                    if let Some(doc) = self.documents.get(doc_id) {
                        let tf = doc.tokens.iter().filter(|&t| t == tok).count() as f64;
                        let doc_len = *self.doc_lengths.get(doc_id).unwrap_or(&1) as f64;
                        let denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len.max(1.0)));
                        let bm25 = idf * ((tf * (self.k1 + 1.0)) / denom.max(1e-5));
                        *scores.entry(doc_id.clone()).or_default() += bm25;
                    }
                }
            }
        }

        let mut hits: Vec<SearchHit> = scores
            .into_iter()
            .filter_map(|(id, score)| {
                self.documents.get(&id).map(|d| SearchHit {
                    id,
                    title: d.title.clone(),
                    score,
                    discrete_code: d.discrete_code,
                    domain: d.domain.clone(),
                })
            })
            .collect();

        hits.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        hits.truncate(top_k);
        hits
    }
}
