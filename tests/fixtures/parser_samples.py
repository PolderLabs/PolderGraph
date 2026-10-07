"""Parser fixtures: one representative sample per strongly supported language.

Each sample exercises nested declarations, imports/re-exports, aliases,
methods/calls and inheritance, so adapter coverage is reviewable.
"""

from __future__ import annotations

PYTHON = b'''"""Module docstring."""

import os
from typing import List
from mylib import Helper as H, thing
from . import sibling
from .relative import other as rel


@decorator
class BaseThing:
    """A base."""


class AuthService(BaseThing):
    """Validate sessions."""

    def validate_session(self, token: str, repo: "Repo") -> Session:
        """Validate one session token."""
        user = repo.find(token)
        return Session(user)

    def _private_helper(self) -> None:
        helper.process(1)


def top_level(x: int) -> List[str]:
    """Top level."""
    return [str(x)]
'''

TYPESCRIPT = b'''import { Helper as H } from "./helper";
import type { Config } from "./config";
export * from "./reexport";

export interface Shape {
  area(): number;
}

export type Alias = Shape | null;

export enum Color { Red, Green }

export class Widget implements Shape {
  private name: string;

  constructor(name: string) {
    this.name = name;
  }

  area(): number {
    return compute(this.name);
  }
}

export function helper(x: number): Shape {
  const w = new Widget("a");
  return w.area() > 0 ? w : null;
}

export const arrow = (a: string): string => a.trim();
'''

JAVASCRIPT = b'''import defaultExport, { named as alias } from "./mod";
export * from "./all";

export class Service extends BaseService {
  constructor(repo) {
    super(repo);
  }

  run(input) {
    return helper.process(input);
  }
}

export function helper(x) {
  return new Service(x).run();
}

export const arrow = (a) => a.trim();

const inner = function named(a) { return a; };
'''

RUST = b'''use std::collections::HashMap;
use crate::auth::Validator as V;
pub use crate::auth::Token;

pub struct Server {
    pub name: String,
}

pub trait Handler {
    fn handle(&self) -> u32;
}

impl Handler for Server {
    fn handle(&self) -> u32 {
        self.name.len() as u32
    }
}

pub fn build(name: String) -> Server {
    Server { name }
}

#[test]
fn test_build() {
    let s = build("x".to_string());
    assert_eq!(s.handle(), 1);
}
'''

GO = b'''package auth

import (
    "fmt"
    alias "example.com/x"
)

type Server struct {
    Name string
}

type Handler interface {
    Handle() error
}

func (s *Server) Handle() error {
    return fmt.Errorf("x")
}

func Build(name string) (*Server, error) {
    return &Server{Name: name}, nil
}

func TestBuild(t *testing.T) {}
'''

JAVA = b'''package com.example.auth;

import java.util.List;
import static com.example.Util.helper;

/** Service docs. */
public class AuthService extends BaseService implements Handler {
    private String name;

    public AuthService(String name) {
        this.name = name;
    }

    public Session validate(String token) throws Exception {
        return repository.find(token);
    }

    interface Inner {}
}

enum Color { RED, GREEN }

interface Handler {
    void handle();
}
'''

C = b'''#include <stdio.h>
#include "local.h"

struct Point {
    int x;
    int y;
};

typedef struct Point PointT;

enum Color { RED, GREEN };

static int helper(int x) {
    return compute(x);
}

int main(int argc, char **argv) {
    Point p;
    return helper(argc);
}
'''

CPP = b'''#include <string>
#include "widget.h"

namespace app {

class Widget : public Base {
public:
    Widget(int x);
    virtual int area() const;
};

int Widget::area() const {
    return compute(width);
}

struct Config { int w; };

template <typename T>
T identity(T value) {
    return value;
}

}  // namespace app
'''

CSHARP = b'''using System;
using Alias = System.Collections.Generic.List<int>;
using System.Text;

namespace App.Auth {
    public interface IHandler {
        void Handle();
    }

    public class AuthService : BaseService, IHandler {
        private string name;
        public string Name { get; set; }

        public AuthService(string name) {
            this.name = name;
        }

        public Session Validate(string token) {
            return repository.Find(token);
        }

        public void Handle() {}
    }

    public enum Color { Red, Green }
}
'''

KOTLIN = b'''package com.example.auth

import kotlin.math.abs
import com.example.Util as Helper

interface Handler {
    fun handle()
}

class AuthService(private val repo: Repo) : BaseService(), Handler {
    private val name: String = "x"

    override fun handle() {
        repo.find(name)
    }

    fun validate(token: String): Session = repo.find(token)
}

data class Config(val width: Int)
'''

SWIFT = b'''import Foundation
import UIKit

protocol Handler {
    func handle()
}

class AuthService: BaseService, Handler {
    private let name: String

    init(name: String) {
        self.name = name
    }

    func validate(token: String) -> Session {
        return repository.find(token)
    }

    func handle() {}
}

struct Config {
    let width: Int
}

enum Color {
    case red
    case green
}
'''

MARKDOWN = b"""# Title

Intro paragraph describing the module.

## Installation

Run the installer:

```bash
pip install thing
```

### Notes

More details here.

## Usage

Call the entry point.
"""

SAMPLES: dict[str, tuple[str, bytes]] = {
    "python": ("auth.py", PYTHON),
    "typescript": ("widget.ts", TYPESCRIPT),
    "tsx": ("app.tsx", TYPESCRIPT),
    "javascript": ("service.js", JAVASCRIPT),
    "jsx": ("app.jsx", JAVASCRIPT),
    "rust": ("lib.rs", RUST),
    "go": ("server.go", GO),
    "java": ("AuthService.java", JAVA),
    "c": ("main.c", C),
    "cpp": ("widget.cpp", CPP),
    "csharp": ("AuthService.cs", CSHARP),
    "kotlin": ("AuthService.kt", KOTLIN),
    "swift": ("AuthService.swift", SWIFT),
    "markdown": ("README.md", MARKDOWN),
}