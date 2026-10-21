// -*- coding: utf-8 -*-
//! Katman B: Vektör Hashing ve Kuantizasyon Sözlüğü (VQ Codebook)
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.2.0

use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use sha2::{Sha256, Digest};
use crate::triplet::{SemanticTriplet, TypedEntity, EntityType};

/// Latent VQ Sözlük Motoru
pub struct VectorQuantizedCodebook {
    codebook: Arc<RwLock<HashMap<u32, SemanticTriplet>>>,
    reverse_index: Arc<RwLock<HashMap<String, u32>>>,
}

impl VectorQuantizedCodebook {
    pub fn new() -> Self {
        let instance = Self {
            codebook: Arc::new(RwLock::new(HashMap::new())),
            reverse_index: Arc::new(RwLock::new(HashMap::new())),
        };
        instance.seed_default_codes();
        instance
    }

    /// 12 Temel Evrensel Bilim ve Mühendislik Alanı için Çekirdek Referans Senaryolar
    fn seed_default_codes(&self) {
        let omni = [
            (8421, SemanticTriplet::new(
                "Toprak", "test_etti",
                vec![TypedEntity::new("ESP32", EntityType::Hardware), TypedEntity::new("nRF24L01", EntityType::Hardware)],
                vec![TypedEntity::new("SPI", EntityType::Protocol), TypedEntity::new("laboratuvar", EntityType::Generic)],
            )),
            (8422, SemanticTriplet::new(
                "Gelistirici", "deploy_etti",
                vec![TypedEntity::new("Kubernetes", EntityType::Software), TypedEntity::new("PostgreSQL", EntityType::Software)],
                vec![TypedEntity::new("Docker", EntityType::Software), TypedEntity::new("production", EntityType::Generic)],
            )),
            (8423, SemanticTriplet::new(
                "Analist", "tespit_etti",
                vec![TypedEntity::new("CVE-2024-1234", EntityType::Vulnerability), TypedEntity::new("BufferOverflow", EntityType::Vulnerability)],
                vec![TypedEntity::new("DMZ", EntityType::Generic), TypedEntity::new("Exploit", EntityType::Software)],
            )),
            (8424, SemanticTriplet::new(
                "Fizikci", "dolasiklastirdi",
                vec![TypedEntity::new("Qubit", EntityType::Quantum), TypedEntity::new("BellState", EntityType::Quantum)],
                vec![TypedEntity::new("Kriyostat", EntityType::Quantum), TypedEntity::new("Qiskit", EntityType::Quantum)],
            )),
            (8425, SemanticTriplet::new(
                "Genetikci", "modifiye_etti",
                vec![TypedEntity::new("CRISPR", EntityType::Bio), TypedEntity::new("Exon", EntityType::Bio)],
                vec![TypedEntity::new("AlphaFold", EntityType::Bio), TypedEntity::new("hucre", EntityType::Bio)],
            )),
            (8426, SemanticTriplet::new(
                "Muhendis", "kalibre_etti",
                vec![TypedEntity::new("Telemetry", EntityType::Aerospace), TypedEntity::new("Gyroscope", EntityType::Aerospace)],
                vec![TypedEntity::new("yorunge", EntityType::Aerospace), TypedEntity::new("Uydu", EntityType::Aerospace)],
            )),
            (8427, SemanticTriplet::new(
                "Surucu_Yazilimi", "denetledi",
                vec![TypedEntity::new("ECU", EntityType::Automotive), TypedEntity::new("LiDAR", EntityType::Automotive)],
                vec![TypedEntity::new("CAN", EntityType::Protocol), TypedEntity::new("otoyol", EntityType::Automotive)],
            )),
            (8428, SemanticTriplet::new(
                "AlgoTrader", "arbitraj_yapti",
                vec![TypedEntity::new("OrderBook", EntityType::Finance), TypedEntity::new("Derivative", EntityType::Finance)],
                vec![TypedEntity::new("Borsa", EntityType::Finance), TypedEntity::new("NASDAQ", EntityType::Finance)],
            )),
            (8429, SemanticTriplet::new(
                "Kontrolcu", "harekete_gecirdi",
                vec![TypedEntity::new("Actuator", EntityType::Robotics), TypedEntity::new("Manipulator", EntityType::Robotics)],
                vec![TypedEntity::new("ROS", EntityType::Software), TypedEntity::new("fabrika", EntityType::Robotics)],
            )),
            (8430, SemanticTriplet::new(
                "Kriptograf", "dogruladi",
                vec![TypedEntity::new("ZK-SNARK", EntityType::Crypto), TypedEntity::new("SHA-256", EntityType::Crypto)],
                vec![TypedEntity::new("TLS", EntityType::Protocol), TypedEntity::new("Blockchain", EntityType::Crypto)],
            )),
            (8431, SemanticTriplet::new(
                "Arastirmaci", "fine_tune_etti",
                vec![TypedEntity::new("Transformer", EntityType::Software), TypedEntity::new("Weights", EntityType::Software)],
                vec![TypedEntity::new("LoRA", EntityType::Software), TypedEntity::new("GPU_Cluster", EntityType::Hardware)],
            )),
            (8432, SemanticTriplet::new(
                "Insan", "arastirdi",
                vec![TypedEntity::new("Bilgi", EntityType::Generic), TypedEntity::new("Hipotez", EntityType::Generic)],
                vec![TypedEntity::new("Evren", EntityType::Generic), TypedEntity::new("Kutuphane", EntityType::Generic)],
            )),
        ];

        for (code, trip) in omni {
            self.register_with_code(code, trip);
        }
    }

    fn compute_signature(triplet: &SemanticTriplet) -> String {
        let mut sorted_objs: Vec<String> = triplet
            .objects
            .iter()
            .map(|o| o.to_tagged_string().to_lowercase())
            .collect();
        sorted_objs.sort();
        let obj_str = sorted_objs.join("+");

        let mut sorted_ctxs: Vec<String> = triplet
            .contexts
            .iter()
            .map(|c| c.to_tagged_string().to_lowercase())
            .collect();
        sorted_ctxs.sort();
        let ctx_str = sorted_ctxs.join("|");

        format!(
            "{}::{}::{}::{}",
            triplet.subject.trim().to_lowercase(),
            triplet.predicate.trim().to_lowercase(),
            obj_str.trim().to_lowercase(),
            ctx_str.trim().to_lowercase()
        )
    }

    /// Çizgeyi sözlüğe kaydeder ve tamsayı kodunu (#CODE) döner
    pub fn register(&self, triplet: SemanticTriplet) -> u32 {
        let sig = Self::compute_signature(&triplet);
        
        {
            let rev = self.reverse_index.read().unwrap();
            if let Some(&code) = rev.get(&sig) {
                return code;
            }
        }

        // SHA-256 tabanlı deterministik 16-bit kuantizasyon
        let mut hasher = Sha256::new();
        hasher.update(sig.as_bytes());
        let hash = hasher.finalize();
        let raw_int = u32::from_be_bytes([hash[0], hash[1], hash[2], hash[3]]);
        let mut code_id = (raw_int % 80000) + 1000;

        let mut book = self.codebook.write().unwrap();
        let mut rev = self.reverse_index.write().unwrap();

        while book.contains_key(&code_id) {
            if Self::compute_signature(&book[&code_id]) == sig {
                return code_id;
            }
            code_id += 1;
        }

        book.insert(code_id, triplet);
        rev.insert(sig, code_id);
        code_id
    }

    pub fn register_with_code(&self, code_id: u32, triplet: SemanticTriplet) {
        let sig = Self::compute_signature(&triplet);
        let mut book = self.codebook.write().unwrap();
        let mut rev = self.reverse_index.write().unwrap();
        book.insert(code_id, triplet);
        rev.insert(sig, code_id);
    }

    pub fn lookup(&self, code_id: u32) -> Option<SemanticTriplet> {
        let book = self.codebook.read().unwrap();
        book.get(&code_id).cloned()
    }

    pub fn size(&self) -> usize {
        let book = self.codebook.read().unwrap();
        book.len()
    }
}
