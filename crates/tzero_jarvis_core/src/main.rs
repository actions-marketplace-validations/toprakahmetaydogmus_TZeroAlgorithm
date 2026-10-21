// -*- coding: utf-8 -*-
//! T-Zero Jarvis Autonomous Engine - Standalone Rust Executable
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.2.0

use std::env;
use std::time::Instant;
use tzero_jarvis_core::DynamicVirtualMemoryInjector;

fn main() {
    let args: Vec<String> = env::args().collect();
    let injector = DynamicVirtualMemoryInjector::new();

    if args.len() > 1 && (args[1] == "--benchmark" || args[1] == "-b") {
        println!("================================================================================");
        println!("   T-ZERO JARVIS CORE - RUST HIGH-SPEED NATIVE BENCHMARK (V4.2.0)");
        println!("   Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)");
        println!("================================================================================");

        let test_texts = [
            "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.",
            "Geliştirici ekibi Kubernetes kümesinde PostgreSQL veritabanını TLS 1.3 protokolüyle şifreleyerek devreye aldı.",
            "Araştırmacı PyTorch kütüphanesinde Transformer modelini 8x A100 GPU üzerinde FP16 formatında eğitti.",
            "Güvenlik uzmanı firewall arkasındaki NGINX sunucusuna SYN flood saldırısını analiz ederek zafiyeti doğruladı.",
            "Sistem yöneticisi Docker container loglarını ELK stack üzerine Elasticsearch portundan aktardı."
        ];

        let iterations = 10_000;
        println!("[*] {} iterasyon ile mikro-saniye gecikme ve verim testi başlatılıyor...", iterations);

        let start = Instant::now();
        let mut total_tokens_saved = 0;

        for _ in 0..iterations {
            for text in &test_texts {
                let res = injector.compress_text(text);
                total_tokens_saved += res.token_savings;
            }
        }

        let elapsed = start.elapsed();
        let total_ops = iterations * test_texts.len();
        let micros_per_op = elapsed.as_micros() as f64 / total_ops as f64;
        let ops_per_sec = (total_ops as f64 / elapsed.as_secs_f64()) as u64;

        println!("[+] Toplam İşlem: {} cümle sıkıştırma", total_ops);
        println!("[+] Toplam Süre: {:.3?}", elapsed);
        println!("[+] Hız / Verim: {} işlem / saniye", ops_per_sec);
        println!("[+] Ortalama İşlem Başına Gecikme: {:.2} µs (mikro-saniye)", micros_per_op);
        println!("[+] Toplam Tasarruf Edilen Token: {}", total_tokens_saved);
        println!("================================================================================");
        return;
    }

    let sample_text = if args.len() > 1 {
        args[1..].join(" ")
    } else {
        "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.".to_string()
    };

    let res = injector.compress_text(&sample_text);
    println!("--------------------------------------------------------------------------------");
    println!("Giriş: {}", res.original_text);
    println!("Çizge (Graph): {:?}", res.graph_representations);
    println!("Kompakt Kod: {:?}", res.compact_codes);
    println!("Sözlük ID: {:?}", res.codebook_ids);
    println!("Sanal Bellek Token'ı: {}", res.virtual_token_string);
    println!("Tasarruf: {} -> {} token (%{:.2} Azalma)", res.original_token_count, res.compressed_token_count, res.reduction_ratio_pct);
    println!("--------------------------------------------------------------------------------");
}
