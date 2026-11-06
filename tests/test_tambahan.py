"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

import pytest
from crud.lexer import tokenize, TokenType, LexError
from crud.parser import parse_sql
from crud.pipeline import analyze_source

# ==========================================
# 1. TEST REGRESI FASE 1: LEXER
# ==========================================

def test_bug1_keyword_case_insensitive():
    """Bug 1: Keyword harus tidak peka huruf besar/kecil ('Select' -> KEYWORD SELECT)."""
    tokens = tokenize("Select")
    assert tokens[0].type == TokenType.KEYWORD
    assert tokens[0].value == "SELECT"


def test_bug2_maximal_munch():
    """Bug 2: Operator '<>' tidak boleh terpecah menjadi '<' dan '>'."""
    tokens = tokenize("a <> b")
    values = [t.value for t in tokens if t.type != TokenType.EOF]
    assert values == ["a", "<>", "b"]
    assert tokens[1].type == TokenType.OP


def test_bug3_escaped_string():
    """Bug 3: Kutip ganda '' di dalam string mewakili 1 karakter kutip."""
    tokens = tokenize("'O''Brien'")
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "O'Brien"


def test_t3_block_comment():
    """TODO T3: Komentar blok /* ... */ lintas baris diabaikan total."""
    tokens = tokenize("/* komentar\nlintas baris */\nSELECT")
    assert tokens[0].type == TokenType.KEYWORD
    assert tokens[0].line == 3


def test_t3_block_comment_unclosed():
    """TODO T3: Komentar blok yang tidak ditutup melempar LexError."""
    with pytest.raises(LexError):
        tokenize("/* komentar tidak ditutup")


# ==========================================
# 2. TEST KASUS TEPI (EDGE CASES)
# ==========================================

def test_edge_case_comment_with_stars():
    """Kasus Tepi 1: Komentar berisi karakter bintang di dalamnya."""
    tokens = tokenize("/* komentar *** bintang */ SELECT 1")
    assert tokens[0].type == TokenType.KEYWORD
    assert tokens[0].value == "SELECT"

    # ==========================================
# 3. TEST REGRESI FASE 2: PARSER
# ==========================================

def test_bug4_presedensi_and_or():
    """Bug 4: AND harus mengikat lebih kuat dari OR (spek 3.1)."""
    script = parse_sql("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3;")
    where = script.statements[0].where
    assert where.op == "OR"
    assert where.right.op == "AND"


def test_bug5_left_outer_join():
    """Bug 5: LEFT OUTER JOIN harus diterima, OUTER opsional (spek 3)."""
    script = parse_sql("SELECT a FROM t LEFT OUTER JOIN u ON t.id = u.id;")
    assert script.errors == []
    assert script.statements[0].joins[0].kind == "LEFT"


def test_bug6_error_recovery_satu_error_per_statement():
    """Bug 6: statement rusak menghasilkan 1 error, statement valid sesudahnya tetap diproses (spek 6)."""
    res = analyze_source("SELECT FROM x; SELECT id FROM y;")
    assert len(res.parse_errors) == 1
    assert len(res.statements) == 1


def test_t1_insert_select():
    """T1: INSERT ... SELECT harus bisa di-parse dan query-nya terisi."""
    script = parse_sql("INSERT INTO a (x) SELECT x FROM b;")
    assert script.errors == []
    assert script.statements[0].query is not None