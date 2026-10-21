// -*- coding: utf-8 -*-
//! Katman C: Dinamik Çözücü & Soft-Prompt / Virtual KV-Cache Enjeksiyonu
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.2.0

use serde::{Deserialize, Serialize};
use crate::triplet::SemanticTripletExtractor;
use crate::codebook::VectorQuantizedCodebook;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressionResult {
    pub original_text: String,
    pub original_token_count: usize,
    pub compressed_token_count: usize,
    pub token_savings: usize,
    pub reduction_ratio_pct: f64,
    pub graph_representations: Vec<String>,
    pub compact_codes: Vec<String>,
    pub codebook_ids: Vec<u32>,
    pub virtual_tokens: Vec<String>,
    pub virtual_token_string: String,
}

pub struct DynamicVirtualMemoryInjector {
    codebook: VectorQuantizedCodebook,
}

impl DynamicVirtualMemoryInjector {
    pub fn new() -> Self {
        Self {
            codebook: VectorQuantizedCodebook::new(),
        }
    }

    /// Doğal dili alır; A, B ve C katmanlarından geçirip sanal token üretir
    pub fn compress_text(&self, text: &str) -> CompressionResult {
        let triplets = SemanticTripletExtractor::extract_triplets(text);
        let raw_word_count = text.split_whitespace().count();
        let original_token_count = std::cmp::max(1, (raw_word_count as f64 * 1.3) as usize);

        let mut code_ids = Vec::new();
        let mut graph_strings = Vec::new();
        let mut compact_codes = Vec::new();
        let mut virtual_tokens = Vec::new();

        for trip in triplets {
            let graph_str = trip.to_graph_string();
            let compact_str = trip.to_compact_code();
            let code_id = self.codebook.register(trip);
            code_ids.push(code_id);
            graph_strings.push(graph_str);
            compact_codes.push(compact_str);
            virtual_tokens.push(format!("<|tzero:mem:{}|>", code_id));
        }

        let compressed_token_count = std::cmp::max(1, virtual_tokens.len());
        let token_savings = if original_token_count > compressed_token_count {
            original_token_count - compressed_token_count
        } else {
            0
        };

        let reduction_ratio_pct = ((token_savings as f64 / original_token_count as f64) * 100.0 * 100.0).round() / 100.0;
        let virtual_token_string = virtual_tokens.join(" ");

        CompressionResult {
            original_text: text.to_string(),
            original_token_count,
            compressed_token_count,
            token_savings,
            reduction_ratio_pct,
            graph_representations: graph_strings,
            compact_codes,
            codebook_ids: code_ids,
            virtual_tokens,
            virtual_token_string,
        }
    }

    /// Sanal token kodunu çözüp anlamsal özete dönüştürür
    pub fn decode_code(&self, code_id: u32) -> Option<String> {
        self.codebook.lookup(code_id).map(|trip| {
            let obj_str = trip.objects.iter().map(|o| o.name.clone()).collect::<Vec<_>>().join(" + ");
            let ctx_str = trip.contexts.iter().map(|c| c.name.clone()).collect::<Vec<_>>().join(" | ");
            if ctx_str.is_empty() {
                format!("{}, {} hedefini {}.", trip.subject, obj_str, trip.predicate)
            } else {
                format!("{}, {} hedefini {} bağlamında {}.", trip.subject, obj_str, ctx_str, trip.predicate)
            }
        })
    }
}
