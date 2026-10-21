// -*- coding: utf-8 -*-
//! T-ZERO HIGH-PERFORMANCE SEMANTIC TRIPLET & NER EXTRACTION ENGINE
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.2.0
//!
//! Bu modül, aşağıdaki 5 kritik optimizasyon ile donatılmış ultra-hızlı NLP çekirdeğidir:
//! 1. Zero-Allocation Stopwords (std::sync::LazyLock)
//! 2. Türkçe Bileşik Eylemler (Light Verbs) n-gram Dedektörü
//! 3. İsim Çekim Ekleri Temizleyici (Stemmer / Lemmatizer)
//! 4. Varlık Tipi Tespiti (NER Tagging: Hardware, IP, Protocol, Crypto, Vuln, Software)
//! 5. Ultra-Kompakt Anlamsal Kodlama (&S:Özne#P:Eylem#O:Nesne#C:Bağlam)

use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::net::Ipv4Addr;
use std::sync::LazyLock;

/// Varlık Türü (Named Entity Recognition - NER)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EntityType {
    Hardware,
    Protocol,
    IPAddress,
    Crypto,
    Vulnerability,
    Software,
    Quantum,
    Bio,
    Aerospace,
    Automotive,
    Finance,
    Robotics,
    Generic,
}

impl EntityType {
    pub fn as_tag(&self) -> &'static str {
        match self {
            EntityType::Hardware => "HARDWARE",
            EntityType::Protocol => "PROTOCOL",
            EntityType::IPAddress => "IP",
            EntityType::Crypto => "CRYPTO",
            EntityType::Vulnerability => "VULN",
            EntityType::Software => "SOFTWARE",
            EntityType::Quantum => "QUANTUM",
            EntityType::Bio => "BIO",
            EntityType::Aerospace => "AEROSPACE",
            EntityType::Automotive => "AUTOMOTIVE",
            EntityType::Finance => "FINANCE",
            EntityType::Robotics => "ROBOTICS",
            EntityType::Generic => "GENERIC",
        }
    }
}

/// Tipli Anlamsal Varlık
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TypedEntity {
    pub name: String,
    pub entity_type: EntityType,
}

impl TypedEntity {
    pub fn new(name: &str, entity_type: EntityType) -> Self {
        Self {
            name: name.to_string(),
            entity_type,
        }
    }

    pub fn to_tagged_string(&self) -> String {
        if self.entity_type == EntityType::Generic {
            self.name.clone()
        } else {
            format!("{}:{}", self.name, self.entity_type.as_tag())
        }
    }
}

/// Saf anlamsal çizge üçlüsü (Graph Triplet)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct SemanticTriplet {
    pub subject: String,
    pub predicate: String,
    pub objects: Vec<TypedEntity>,
    pub contexts: Vec<TypedEntity>,
}

impl SemanticTriplet {
    pub fn new(
        subject: &str,
        predicate: &str,
        objects: Vec<TypedEntity>,
        contexts: Vec<TypedEntity>,
    ) -> Self {
        Self {
            subject: subject.to_string(),
            predicate: predicate.to_string(),
            objects,
            contexts,
        }
    }

    /// Çizge metin formatı: (Özne)->[Yüklem]->(Nesne:TIP + Nesne:TIP | Bağlam:TIP)
    pub fn to_graph_string(&self) -> String {
        let obj_str = if self.objects.is_empty() {
            "Hedef".to_string()
        } else {
            self.objects
                .iter()
                .map(|o| o.to_tagged_string())
                .collect::<Vec<_>>()
                .join(" + ")
        };

        let ctx_str = self
            .contexts
            .iter()
            .map(|c| c.to_tagged_string())
            .collect::<Vec<_>>()
            .join(" | ");

        if ctx_str.is_empty() {
            format!("({})->[{}]->({})", self.subject, self.predicate, obj_str)
        } else {
            format!("({})->[{}]->({} | {})", self.subject, self.predicate, obj_str, ctx_str)
        }
    }

    /// 4. Kompakt Kodlama (Binary Token Serialization / Anlamsal ID)
    /// Token tasarrufu sağlayan ultra sıkışık format: &S:Özne#P:Eylem#O:Nesneler#C:Bağlamlar
    pub fn to_compact_code(&self) -> String {
        let obj_str = self
            .objects
            .iter()
            .map(|o| o.to_tagged_string())
            .collect::<Vec<_>>()
            .join("+");

        let ctx_str = self
            .contexts
            .iter()
            .map(|c| c.to_tagged_string())
            .collect::<Vec<_>>()
            .join("|");

        format!(
            "&S:{}#P:{}#O:{}#C:{}",
            self.subject, self.predicate, obj_str, ctx_str
        )
    }
}

// -----------------------------------------------------------------------------
// 1. BELLEK VE HIZ OPTİMİZASYONU: ZERO-ALLOCATION STATIC DATA (std::sync::LazyLock)
// -----------------------------------------------------------------------------
static STOPWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let words = [
        // Türkçe Dolgular
        "ve", "veya", "ile", "için", "icin", "dolayısıyla", "dolayisiyla", "bu", "şu", "su", "o",
        "bir", "birkaç", "birkac", "dün", "dun", "akşam", "aksam", "sabah", "öğle", "ogle", "gece",
        "bugün", "bugun", "yarın", "yarin", "şimdi", "simdi", "üzerinde", "uzerinde", "üzerine", "uzerine",
        "altında", "altinda", "yanında", "yaninda", "tarafından", "tarafindan", "aracılığıyla", "araciligiyla",
        "vasıtasıyla", "vasitasiyla", "bağlayarak", "baglayarak", "kullanarak", "yoluyla", "şekilde", "sekilde",
        "falan", "filan", "şey", "sey", "dair", "göre", "gore", "kadar", "beri", "sonra", "önce", "once",
        "dolayı", "dolayi", "ötürü", "oturu", "adeta", "neredeyse", "kartı", "karti", "kartını", "kartini",
        "modülünü", "modulunu", "modülü", "modulu", "portuna", "portu", "hattına", "hattina", "hattı", "hatti",
        "cihazını", "cihazi", "sunucusunu", "sunucusu", "kümesini", "kumesi", "tablosunu", "tablosu",
        // İngilizce Dolgular
        "and", "or", "with", "for", "therefore", "thus", "hence", "the", "a", "an",
        "yesterday", "evening", "today", "morning", "night", "now", "on", "in", "at",
        "by", "through", "using", "via", "connecting", "connected", "over", "under", "into",
        "from", "to", "after", "before", "while", "during", "towards", "as", "well"
    ];
    let mut set = HashSet::with_capacity(words.len() * 2);
    for w in words {
        set.insert(w);
    }
    set
});

// Bilinen Donanım Anahtar Kelimeleri
static HARDWARE_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let hw = [
        "ESP32", "ESP8266", "NRF24L01", "NRF24", "STM32", "ARDUINO", "RASPBERRY", "RASPBERRYPI",
        "PIC", "AVR", "FPGA", "CPLD", "RP2040", "TEENSY", "SENSOR", "OLED", "LCD", "SERVO",
        "MOTOR", "RELAY", "TRANSCEIVER", "ACCELEROMETER", "GYROSCOPE", "BAROMETER", "RFID"
    ];
    hw.into_iter().collect()
});

// Bilinen Protokol Anahtar Kelimeleri
static PROTOCOL_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let protos = [
        "SPI", "I2C", "UART", "CAN", "GPIO", "USB", "TCP", "UDP", "HTTP", "HTTPS",
        "REST", "GRPC", "WEBSOCKET", "MQTT", "COAP", "BLE", "WIFI", "LORA", "ZIGBEE",
        "TLS", "SSL", "SSH", "IPSEC", "MODBUS", "PROFIBUS", "ETHERNET"
    ];
    protos.into_iter().collect()
});

// Bilinen Kripto / Güvenlik Anahtar Kelimeleri
static CRYPTO_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let crypto = [
        "AES-256", "AES-128", "AES", "RSA-4096", "RSA-2048", "RSA", "ECC", "ECDSA",
        "SHA-256", "SHA-512", "SHA-3", "MD5", "HMAC", "PBKDF2", "CHACHA20", "POLY1305",
        "JWT", "OAUTH2", "ARGON2", "BCRYPT"
    ];
    crypto.into_iter().collect()
});

// Bilinen Yazılım & Bulut Anahtar Kelimeleri
static SOFTWARE_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let sw = [
        "KUBERNETES", "K8S", "DOCKER", "POSTGRESQL", "POSTGRES", "MYSQL", "MONGODB",
        "REDIS", "RABBITMQ", "KAFKA", "NGINX", "APACHE", "LINUX", "WINDOWS", "PYTORCH",
        "TENSORFLOW", "FASTAPI", "NODEJS", "REACT", "VUE", "TAILWIND", "RUST", "PYTHON"
    ];
    sw.into_iter().collect()
});

static QUANTUM_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let q = [
        "QUBIT", "QUBITS", "QISKIT", "CIRQ", "SHOR", "GROVER", "HAMILTONIAN", "TELEPORTATION",
        "SUPERCONDUCTING", "IONTRAP", "QUANTUM_GATE", "QUANTUM"
    ];
    q.into_iter().collect()
});

static BIO_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let bio = [
        "CRISPR", "CAS9", "ALPHAFOLD", "MRNA", "DNA", "RNA", "EXON", "INTRON", "CODON",
        "RIBOSOME", "GENOME", "GENOMICS", "PROTEIN", "BLAST"
    ];
    bio.into_iter().collect()
});

static AEROSPACE_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let aero = [
        "AVIONICS", "TELEMETRY", "IMU", "CANAEROSPACE", "ARINC429", "ARINC", "MIL-STD-1553",
        "GYROSCOPE", "THRUST", "RCS", "SATELLITE", "STARTRACKER"
    ];
    aero.into_iter().collect()
});

static AUTOMOTIVE_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let auto = [
        "AUTOSAR", "CAN_FD", "CANFD", "LIN", "FLEXRAY", "ECU", "BMS", "OBD2", "OBD",
        "OBD-II", "LIDAR", "ADAS", "RADAR"
    ];
    auto.into_iter().collect()
});

static FINANCE_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let fin = [
        "ORDERBOOK", "FIX", "VWAP", "ARBITRAGE", "MARKETMAKER", "HFT", "DERIVATIVE",
        "OPTION", "HEDGING", "ALGOTRADING"
    ];
    fin.into_iter().collect()
});

static ROBOTICS_KEYWORDS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let rob = [
        "ROS", "ROS2", "MICROROS", "MICRO-ROS", "DDS", "URDF", "SLAM", "KINEMATICS",
        "GAZEBO", "ACTUATOR", "SERVO"
    ];
    rob.into_iter().collect()
});

pub struct SemanticTripletExtractor;

impl SemanticTripletExtractor {
    // -----------------------------------------------------------------------------
    // 5. TÜRKÇE İSİM ÇEKİM EKLERİ TEMİZLEYİCİ (Stemmer / Lemmatizer)
    // -----------------------------------------------------------------------------
    pub fn strip_turkish_suffixes(word: &str) -> String {
        // Kesme işaretinden sonrasını at (Örn: "ESP32'yi" -> "ESP32", "PostgreSQL'in" -> "PostgreSQL")
        let base = if let Some((root, _)) = word.split_once('\'') {
            root
        } else if let Some((root, _)) = word.split_once('’') {
            root
        } else {
            word
        };

        let mut clean = base.to_string();
        let suffixes = [
            "sinde", "sında", "sinden", "sından", "leriyle", "larıyla", "lerin", "ların",
            "lerinin", "larının", "lerine", "larına", "den", "dan", "ten", "tan", "nin",
            "nın", "nun", "nün", "de", "da", "te", "ta", "ye", "ya", "ne", "na",
            "in", "ın", "un", "ün", "e", "a", "i", "ı", "u", "ü"
        ];

        let clean_lower = clean.to_lowercase();
        let agent_suffixes = ["ici", "ıcı", "ucu", "ücü", "maci", "macı", "men", "man", "ist", "tor", "tör"];
        if agent_suffixes.iter().any(|&asuf| clean_lower.ends_with(asuf)) {
            return clean;
        }

        for &suf in &suffixes {
            if clean_lower.ends_with(suf) && clean.len() > suf.len() + 3 {
                clean.truncate(clean.len() - suf.len());
                break;
            }
        }
        clean
    }

    // -----------------------------------------------------------------------------
    // 3. VARLIK TİPİ TESPİTİ (NER Tagging)
    // -----------------------------------------------------------------------------
    pub fn classify_entity(token: &str) -> EntityType {
        let upper = token.to_uppercase();

        // 1. IP Adresi Kontrolü
        if upper.parse::<Ipv4Addr>().is_ok() {
            return EntityType::IPAddress;
        }

        // 2. Güvenlik Zafiyeti (CVE-YYYY-NNNNN vb.)
        if upper.starts_with("CVE-") || upper.contains("EXPLOIT") || upper.contains("VULN") {
            return EntityType::Vulnerability;
        }

        // 3. Kriptografi & Şifreleme
        if CRYPTO_KEYWORDS.contains(upper.as_str()) || upper.starts_with("AES") || upper.starts_with("RSA") {
            return EntityType::Crypto;
        }

        // 4. Kuantum Bilişim
        if QUANTUM_KEYWORDS.contains(upper.as_str()) || upper.starts_with("QUBIT") {
            return EntityType::Quantum;
        }

        // 5. Biyoinformatik & Genetik
        if BIO_KEYWORDS.contains(upper.as_str()) || upper.starts_with("CRISPR") {
            return EntityType::Bio;
        }

        // 6. Havacılık & Aviyonik
        if AEROSPACE_KEYWORDS.contains(upper.as_str()) {
            return EntityType::Aerospace;
        }

        // 7. Otomotiv & Otonom Sürüş
        if AUTOMOTIVE_KEYWORDS.contains(upper.as_str()) {
            return EntityType::Automotive;
        }

        // 8. Finansal Mühendislik & HFT
        if FINANCE_KEYWORDS.contains(upper.as_str()) {
            return EntityType::Finance;
        }

        // 9. Robotik & Kontrol
        if ROBOTICS_KEYWORDS.contains(upper.as_str()) || upper.starts_with("ROS") {
            return EntityType::Robotics;
        }

        // 10. Protokol & Ağ
        if PROTOCOL_KEYWORDS.contains(upper.as_str()) {
            return EntityType::Protocol;
        }

        // 11. Donanım & Sensör
        if HARDWARE_KEYWORDS.contains(upper.as_str()) || upper.starts_with("NRF") || upper.starts_with("ESP") || upper.starts_with("STM") {
            return EntityType::Hardware;
        }

        // 12. Yazılım & Bulut
        if SOFTWARE_KEYWORDS.contains(upper.as_str()) {
            return EntityType::Software;
        }

        EntityType::Generic
    }

    // -----------------------------------------------------------------------------
    // 2. TÜRKÇE BİLEŞİK FİİLLER (Light Verbs) n-gram DEDEKTÖRÜ
    // -----------------------------------------------------------------------------
    pub fn detect_compound_predicate(tokens: &[&str]) -> Option<(String, usize, usize)> {
        let auxiliaries = [
            "etti", "etti.", "etti,", "yaptı", "yapti", "aldı", "aldi", "kıldı", "kildi",
            "oldu", "verdi", "geçti", "gecti", "buldu", "çalıştı", "calisti"
        ];

        if tokens.len() < 2 {
            return None;
        }

        for i in 0..tokens.len().saturating_sub(1) {
            let first = tokens[i].trim_matches(|c: char| !c.is_alphanumeric()).to_lowercase();
            let second = tokens[i + 1].trim_matches(|c: char| !c.is_alphanumeric()).to_lowercase();

            if auxiliaries.iter().any(|&aux| second == aux || second.contains(aux)) {
                let verb_norm = format!("{}_{}", first, second);
                return Some((verb_norm, i, i + 1));
            }
        }
        None
    }

    /// Tekil veya bileşik eylemi normalize eder
    fn normalize_verb(verb: &str) -> String {
        let v = verb.to_lowercase();
        let clean = v.trim_matches(|c: char| !c.is_alphanumeric());

        if clean.contains("test") {
            "test_etti".to_string()
        } else if clean.contains("analiz") {
            "analiz_etti".to_string()
        } else if clean.contains("bagla") || clean.contains("bağla") || clean.contains("connect") {
            "bagladi".to_string()
        } else if clean.contains("derle") || clean.contains("compile") || clean.contains("build") {
            "derledi".to_string()
        } else if clean.contains("calistir") || clean.contains("çalıştır") || clean.contains("run") {
            "calistirdi".to_string()
        } else if clean.contains("sifrele") || clean.contains("şifrele") || clean.contains("encrypt") {
            "sifreledi".to_string()
        } else if clean.contains("dagit") || clean.contains("dağıt") || clean.contains("deploy") {
            "dagitti".to_string()
        } else if clean.contains("kur") || clean.contains("install") {
            "kurdu".to_string()
        } else if clean.contains("onar") || clean.contains("düzelt") || clean.contains("fix") {
            "onardi".to_string()
        } else if clean.contains("egit") || clean.contains("eğit") || clean.contains("train") {
            "egitti".to_string()
        } else if clean.contains("dogrula") || clean.contains("doğrula") || clean.contains("verify") {
            "dogruladi".to_string()
        } else {
            clean.replace(" ", "_")
        }
    }

    /// Cümlenin fiil olup olmadığını tespit eder
    fn is_probable_verb(word: &str) -> bool {
        let w = word.to_lowercase();
        w.ends_with("ti") || w.ends_with("tı") || w.ends_with("tu") || w.ends_with("tü") ||
        w.ends_with("di") || w.ends_with("dı") || w.ends_with("du") || w.ends_with("dü") ||
        w.ends_with("miş") || w.ends_with("mış") || w.ends_with("yor") ||
        w.ends_with("ecek") || w.ends_with("acak") || w.ends_with("ed") || w.ends_with("ing")
    }

    /// Evrensel Metin Çözümleme Pipeline
    pub fn extract_triplets(text: &str) -> Vec<SemanticTriplet> {
        let mut triplets = Vec::new();
        if text.trim().is_empty() {
            return triplets;
        }

        let sentences: Vec<&str> = text
            .split(|c| c == '.' || c == '!' || c == '?' || c == ';' || c == '\n')
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .collect();

        for sentence in sentences {
            let raw_tokens: Vec<&str> = sentence.split_whitespace().collect();
            if raw_tokens.is_empty() {
                continue;
            }

            // 1. Türkçe Bileşik Eylemleri (Light Verbs) n-gram ile yakala
            let (predicate, verb_start, verb_end) = if let Some((comp_verb, start, end)) = Self::detect_compound_predicate(&raw_tokens) {
                (Self::normalize_verb(&comp_verb), Some(start), Some(end))
            } else {
                // Tekil eylem ara
                let mut pred = "islem_yapti".to_string();
                let mut v_idx = None;
                for (idx, &tok) in raw_tokens.iter().enumerate().rev() {
                    let clean = tok.trim_matches(|c: char| !c.is_alphanumeric());
                    if Self::is_probable_verb(clean) {
                        pred = Self::normalize_verb(clean);
                        v_idx = Some(idx);
                        break;
                    }
                }
                (pred, v_idx, v_idx)
            };

            // 2. Özne Tespiti (Cümlenin başındaki ilk anlamlı isim)
            let mut subject = String::new();
            let mut subject_idx = None;

            for (idx, &tok) in raw_tokens.iter().enumerate() {
                let clean = Self::strip_turkish_suffixes(tok.trim_matches(|c: char| !c.is_alphanumeric()));
                if clean.is_empty() {
                    continue;
                }
                let lower = clean.to_lowercase();
                if !STOPWORDS.contains(lower.as_str()) {
                    subject = clean;
                    subject_idx = Some(idx);
                    break;
                }
            }

            if subject.is_empty() {
                subject = "Sistem".to_string();
            }

            // 3. Nesneler ve Bağlamlar (Objects & Contexts) + NER ve Stemmer
            let mut objects = Vec::new();
            let mut contexts = Vec::new();

            for (idx, &tok) in raw_tokens.iter().enumerate() {
                // Özne ve eylem tokenlarını atla
                if Some(idx) == subject_idx {
                    continue;
                }
                if let (Some(vs), Some(ve)) = (verb_start, verb_end) {
                    if idx >= vs && idx <= ve {
                        continue;
                    }
                }

                let stemmed = Self::strip_turkish_suffixes(tok.trim_matches(|c: char| !c.is_alphanumeric()));
                if stemmed.is_empty() {
                    continue;
                }

                let lower = stemmed.to_lowercase();
                if STOPWORDS.contains(lower.as_str()) {
                    continue;
                }

                // NER Sınıflandırması
                let entity_type = Self::classify_entity(&stemmed);
                let typed_ent = TypedEntity::new(&stemmed, entity_type);

                if entity_type == EntityType::Protocol || Self::is_universal_context(tok, &stemmed) {
                    contexts.push(typed_ent);
                } else if objects.len() < 8 {
                    if !objects.iter().any(|o: &TypedEntity| o.name == typed_ent.name) {
                        objects.push(typed_ent);
                    }
                }
            }

            triplets.push(SemanticTriplet::new(&subject, &predicate, objects, contexts));
        }

        triplets
    }

    /// Evrensel Bağlam (Context / Environment) Tespiti
    /// Türkçe morfolojik bulunma/ayrılma ekleri (-da, -de, -ta, -te vb.) ve evrensel ortam anahtar kelimeleri
    fn is_universal_context(raw_tok: &str, clean_stem: &str) -> bool {
        let raw_low = raw_tok.to_lowercase();
        let clean_low = clean_stem.to_lowercase();

        // 1. Türkçe Morfolojik Bulunma ve Ayrılma Ekleri
        let locative = [
            "da", "de", "ta", "te", "dan", "den", "tan", "ten",
            "inda", "inde", "sinda", "sinde", "unda", "unde", "sunda", "sunde"
        ];
        if locative.iter().any(|sfx| raw_low.ends_with(sfx)) {
            return true;
        }

        // 2. Evrensel 12 Alanlı Ortam/Bağlam Belirteçleri
        const CONTEXT_DOMAINS: &[&str] = &[
            "laboratuvar", "lab", "atolye", "oda", "saha", "kart", "board", "pin", "port",
            "sunucu", "server", "kume", "cluster", "cloud", "bulut", "production", "prod", "staging", "dev",
            "ag", "network", "subnet", "dmz", "vpn", "intranet", "internet", "firewall", "honeypot", "sandbox",
            "kriyostat", "cryostat", "vakum", "kavite", "cavity", "lattice",
            "hucre", "cell", "doku", "tissue", "petri", "in_vitro", "in_vivo", "reaktor",
            "yorunge", "orbit", "uzay", "space", "atmosfer", "istasyon", "hangar", "uydu",
            "arac", "vehicle", "sasi", "chassis", "motor", "otoyol", "highway", "kabin",
            "borsa", "market", "piyasa", "exchange", "kasa", "cuzdan", "wallet", "banka", "bank",
            "fabrika", "factory", "konveyor", "arena", "simulasyon", "sim",
            "ev", "ofis", "sehir", "arsiv", "kutuphane", "masada", "ekranda", "ortam", "environment"
        ];

        CONTEXT_DOMAINS.iter().any(|&env| clean_low.contains(env) || raw_low.contains(env))
    }
}
