// -*- coding: utf-8 -*-
//! T-ZERO RUST NATIVE CAUSAL & TEMPORAL GRAPH (4D GRAPH)
//! Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
//! Version: 4.4.0

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CausalRelation {
    Causes,
    TriggeredBy,
    Fixes,
    Resolves,
    Mitigates,
    FailsWith,
    Precedes,
    Follows,
}

impl CausalRelation {
    pub fn as_str(&self) -> &'static str {
        match self {
            CausalRelation::Causes => "causes",
            CausalRelation::TriggeredBy => "triggered_by",
            CausalRelation::Fixes => "fixes",
            CausalRelation::Resolves => "resolves",
            CausalRelation::Mitigates => "mitigates",
            CausalRelation::FailsWith => "fails_with",
            CausalRelation::Precedes => "precedes",
            CausalRelation::Follows => "follows",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CausalEdge {
    pub source_id: String,
    pub target_id: String,
    pub relation: CausalRelation,
    pub weight: f64,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CausalNode {
    pub node_id: String,
    pub label: String,
    pub entity_type: String,
    pub triplet_code: Option<u32>,
    pub timestamp: u64,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct CausalTemporalGraph {
    pub nodes: HashMap<String, CausalNode>,
    pub outgoing: HashMap<String, Vec<CausalEdge>>,
    pub incoming: HashMap<String, Vec<CausalEdge>>,
    pub timeline: Vec<String>,
}

impl CausalTemporalGraph {
    pub fn new() -> Self {
        Self::default()
    }

    fn current_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0)
    }

    pub fn add_node(&mut self, node_id: &str, label: &str, entity_type: &str, triplet_code: Option<u32>) {
        let ts = Self::current_timestamp();
        let node = CausalNode {
            node_id: node_id.to_string(),
            label: label.to_string(),
            entity_type: entity_type.to_string(),
            triplet_code,
            timestamp: ts,
        };
        self.nodes.insert(node_id.to_string(), node);
        self.outgoing.entry(node_id.to_string()).or_default();
        self.incoming.entry(node_id.to_string()).or_default();
        self.timeline.push(node_id.to_string());
    }

    pub fn add_edge(&mut self, source_id: &str, target_id: &str, relation: CausalRelation, weight: f64) {
        if !self.nodes.contains_key(source_id) {
            self.add_node(source_id, source_id, "GENERIC", None);
        }
        if !self.nodes.contains_key(target_id) {
            self.add_node(target_id, target_id, "GENERIC", None);
        }

        let edge = CausalEdge {
            source_id: source_id.to_string(),
            target_id: target_id.to_string(),
            relation,
            weight,
            timestamp: Self::current_timestamp(),
        };

        self.outgoing.entry(source_id.to_string()).or_default().push(edge.clone());
        self.incoming.entry(target_id.to_string()).or_default().push(edge);
    }

    pub fn get_root_causes(&self, target_node_id: &str, max_depth: usize) -> Vec<String> {
        let mut root_causes = Vec::new();
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        queue.push_back((target_node_id.to_string(), 0));

        while let Some((curr_id, depth)) = queue.pop_front() {
            if depth >= max_depth || visited.contains(&curr_id) {
                continue;
            }
            visited.insert(curr_id.clone());

            let incoming = self.incoming.get(&curr_id).cloned().unwrap_or_default();
            let causal_incoming: Vec<_> = incoming
                .into_iter()
                .filter(|e| matches!(e.relation, CausalRelation::Causes | CausalRelation::Precedes | CausalRelation::TriggeredBy))
                .collect();

            if causal_incoming.is_empty() && depth > 0 {
                root_causes.push(curr_id);
            } else {
                for edge in causal_incoming {
                    queue.push_back((edge.source_id, depth + 1));
                }
            }
        }

        root_causes
    }

    pub fn compute_rollback_order(&self, target_node_id: &str) -> Vec<String> {
        let mut rollback = Vec::new();
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        queue.push_back(target_node_id.to_string());

        while let Some(curr_id) = queue.pop_front() {
            if visited.contains(&curr_id) {
                continue;
            }
            visited.insert(curr_id.clone());
            rollback.push(curr_id.clone());

            if let Some(edges) = self.outgoing.get(&curr_id) {
                for edge in edges {
                    queue.push_back(edge.target_id.clone());
                }
            }
        }

        rollback.reverse();
        rollback
    }
}
