"""
Tests for T-Zero Polyglot Signature Extractor and Token Reducer.
Validates zero-cost AST/regex signature extraction across TypeScript, Go, Rust, Java, C#, and C++.
"""

import unittest
from tzero_v3 import PolyglotSignatureExtractor, TokenReducer


class TestPolyglotSignatureExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = PolyglotSignatureExtractor()

    def test_typescript_extraction(self):
        ts_code = """
import { Injectable, Logger } from '@nestjs/common';
import * as fs from 'fs';

export interface UserSession {
    id: string;
    token: string;
    expiresAt: Date;
}

export type Role = 'ADMIN' | 'USER' | 'GUEST';

@Injectable()
export class AuthService {
    private readonly logger = new Logger(AuthService.name);

    constructor(private readonly userRepo: UserRepository) {
        this.logger.log('AuthService initialized');
    }

    async validateToken(token: string): Promise<UserSession | null> {
        let decoded = null;
        for (let i = 0; i < 100; i++) {
            decoded = doHeavyWork(token, i);
        }
        return decoded;
    }

    public static hashPassword(raw: string): string {
        return "hashed_" + raw;
    }
}
"""
        result = self.extractor.extract("service.ts", ts_code)
        self.assertIn("export interface UserSession", result)
        self.assertIn("export type Role", result)
        self.assertIn("export class AuthService", result)
        self.assertIn("async validateToken", result)
        self.assertIn("hashPassword", result)
        # Verify internal implementation loops are pruned
        self.assertNotIn("for (let i = 0; i < 100; i++)", result)

    def test_go_extraction(self):
        go_code = """
package worker

import (
    "context"
    "fmt"
    "time"
)

type WorkerConfig struct {
    MaxRetries int
    Timeout    time.Duration
}

type Processor interface {
    Process(ctx context.Context, data []byte) error
}

func NewWorker(cfg WorkerConfig) *Worker {
    return &Worker{cfg: cfg}
}

func (w *Worker) Start(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            time.Sleep(100 * time.Millisecond)
        }
    }
}
"""
        result = self.extractor.extract("worker.go", go_code)
        self.assertIn("package worker", result)
        self.assertIn("type WorkerConfig struct", result)
        self.assertIn("type Processor interface", result)
        self.assertIn("func NewWorker", result)
        self.assertIn("func (w *Worker) Start", result)
        self.assertNotIn("time.Sleep(100 * time.Millisecond)", result)

    def test_rust_extraction(self):
        rust_code = """
use std::sync::Arc;
use std::collections::HashMap;

pub struct CacheManager<T> {
    store: Arc<HashMap<String, T>>,
    ttl: u64,
}

pub trait Cacheable {
    fn key(&self) -> String;
}

impl<T> CacheManager<T> {
    pub fn new(ttl: u64) -> Self {
        Self {
            store: Arc::new(HashMap::new()),
            ttl,
        }
    }

    pub async fn get(&self, key: &str) -> Option<T> {
        // internal lookup
        let found = self.store.get(key);
        found.cloned()
    }
}
"""
        result = self.extractor.extract("cache.rs", rust_code)
        self.assertIn("pub struct CacheManager", result)
        self.assertIn("pub trait Cacheable", result)
        self.assertIn("impl<T> CacheManager", result)
        self.assertIn("pub fn new", result)
        self.assertIn("pub async fn get", result)
        self.assertNotIn("let found = self.store.get(key);", result)

    def test_java_extraction(self):
        java_code = """
package com.tzero.security;

import java.util.List;
import java.util.Map;

public class SecurityAuditor implements Auditor {
    private final String secretKey;

    public SecurityAuditor(String secretKey) {
        this.secretKey = secretKey;
    }

    @Override
    public boolean auditRequest(String payload) {
        int hash = payload.hashCode();
        return hash > 0;
    }

    protected void cleanUp() {
        System.out.println("Cleaning up");
    }
}
"""
        result = self.extractor.extract("SecurityAuditor.java", java_code)
        self.assertIn("package com.tzero.security;", result)
        self.assertIn("public class SecurityAuditor", result)
        self.assertIn("public SecurityAuditor", result)
        self.assertIn("public boolean auditRequest", result)
        self.assertNotIn("int hash = payload.hashCode();", result)

    def test_csharp_extraction(self):
        csharp_code = """
using System;
using System.Threading.Tasks;

namespace TZero.Engine
{
    public interface ITokenOptimizer
    {
        Task<int> OptimizeAsync(string code);
    }

    public class TokenOptimizer : ITokenOptimizer
    {
        public async Task<int> OptimizeAsync(string code)
        {
            var tokens = code.Split(' ');
            await Task.Delay(10);
            return tokens.Length;
        }
    }
}
"""
        result = self.extractor.extract("TokenOptimizer.cs", csharp_code)
        self.assertIn("namespace TZero.Engine", result)
        self.assertIn("public interface ITokenOptimizer", result)
        self.assertIn("public class TokenOptimizer", result)
        self.assertIn("public async Task<int> OptimizeAsync", result)
        self.assertNotIn("var tokens = code.Split(' ');", result)

    def test_cpp_extraction(self):
        cpp_code = """
#include <iostream>
#include <vector>
#include <string>

namespace TZero {
    class Lexer {
    public:
        Lexer(const std::string& input);
        std::vector<std::string> tokenize();
    private:
        std::string source;
    };
}
"""
        result = self.extractor.extract("lexer.hpp", cpp_code)
        self.assertIn("#include <iostream>", result)
        self.assertIn("class Lexer", result)
        self.assertIn("tokenize()", result)


class TestTokenReducerPolyglot(unittest.TestCase):
    def test_reduce_polyglot_savings(self):
        long_ts = """
import { Controller, Get, Post, Body, Param } from '@nestjs/common';

export interface DataPayload {
    id: number;
    value: string;
}

@Controller('data')
export class DataController {
    @Get(':id')
    async getData(@Param('id') id: string): Promise<DataPayload> {
        // Very long processing
""" + "\n".join([f"        const x_{i} = {i} * 42; console.log(x_{i});" for i in range(150)]) + """
        return { id: 1, value: "test" };
    }

    @Post()
    createData(@Body() payload: DataPayload): boolean {
        return true;
    }
}
"""
        reduced, savings = TokenReducer.reduce_content("controller.ts", long_ts)
        self.assertGreater(savings, 60.0)
        self.assertIn("export class DataController", reduced)
        self.assertIn("async getData", reduced)
        self.assertNotIn("const x_50", reduced)


if __name__ == '__main__':
    unittest.main()
