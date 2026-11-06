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
from crud.resolver import Resolver
from crud.ast_nodes import ColumnRef, iter_nodes

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
# 2. TEST REGRESI FASE 2: PARSER
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

# ==========================================
# 4. TEST REGRESI FASE 4: ANALYZER
# ==========================================

from crud.parser import parse_sql
from crud.analyzer import analyze_statement

def test_bug9_subquery_in_update_is_read():
    """Bug 9: Subquery pada UPDATE (pada SET atau WHERE) harus selalu ditandai operasi R (Read)."""
    # (a) Subquery di WHERE: target U, subquery R
    ast_a = parse_sql("UPDATE pesanan SET a = 1 WHERE b IN (SELECT id FROM pelanggan);").statements[0]
    res_a = analyze_statement(ast_a)
    assert res_a["pesanan"] == {"U"}
    assert res_a["pelanggan"] == {"R"}

    # (b) Subquery di SET: target U, subquery R
    ast_b = parse_sql("UPDATE pelanggan SET level = (SELECT l FROM level_ref WHERE id = 1) WHERE id = 10;").statements[0]
    res_b = analyze_statement(ast_b)
    assert res_b["pelanggan"] == {"U"}
    assert res_b["level_ref"] == {"R"}

    # (c) UPDATE membaca tabel lain lewat subquery di WHERE
    ast_c = parse_sql("UPDATE pelanggan SET level = 'gold' WHERE id IN (SELECT pelanggan_id FROM pesanan WHERE total > 100);").statements[0]
    res_c = analyze_statement(ast_c)
    assert res_c["pelanggan"] == {"U"}
    assert res_c["pesanan"] == {"R"}

    # (d) INSERT ... SELECT: target C, sumber R
    ast_d = parse_sql("INSERT INTO arsip (id) SELECT id FROM pesanan;").statements[0]
    res_d = analyze_statement(ast_d)
    assert res_d["arsip"] == {"C"}
    assert res_d["pesanan"] == {"R"}

    # (e) DELETE dengan subquery: target D, subquery R
    ast_e = parse_sql("DELETE FROM pesanan WHERE pelanggan_id IN (SELECT id FROM pelanggan WHERE diblokir = 1);").statements[0]
    res_e = analyze_statement(ast_e)
    assert res_e["pesanan"] == {"D"}
    assert res_e["pelanggan"] == {"R"}

# ==========================================
# TEST KASUS TEPI (EDGE CASES)
# ==========================================

def test_edge_case_comment_with_stars():
    """Kasus Tepi 1: Komentar berisi karakter bintang di dalamnya."""
    tokens = tokenize("/* komentar *** bintang */ SELECT 1")
    assert tokens[0].type == TokenType.KEYWORD
    assert tokens[0].value == "SELECT"

def test_edge_not_between():
    """Kasus tepi: NOT BETWEEN, AND milik BETWEEN, bukan operator logika."""
    script = parse_sql("SELECT a FROM t WHERE a NOT BETWEEN 1 AND 5 AND b = 2;")
    assert script.errors == []
    assert script.statements[0].where.op == "AND"

def test_edge_is_not_null():
    """Kasus tepi: IS NOT NULL harus diterima."""
    assert parse_sql("SELECT a FROM t WHERE a IS NOT NULL;").errors == []

def test_edge_titik_koma_ganda():
    """Kasus tepi: ';;' tidak boleh menghasilkan error."""
    script = parse_sql(";;SELECT a FROM t;;")
    assert script.errors == []
    assert len(script.statements) == 1

def test_edge_perbandingan_tidak_berantai():
    """Kasus tepi: a = 1 = 2 harus ditolak (spek 3.1, tidak berantai)."""
    assert len(parse_sql("SELECT a FROM t WHERE a = 1 = 2;").errors) >= 1

    # ==========================================
# 4. TEST REGRESI FASE 3: RESOLVER
# ==========================================

def _resolve(sql):
    script = parse_sql(sql)
    diags = Resolver().resolve_script(script)
    return script, diags


def _cols(script):
    return [n for n in iter_nodes(script) if isinstance(n, ColumnRef)]


def test_bug7_alias_shadowing():
    """Bug 7: alias subquery menutupi alias luar (spek 4.3, cari dari scope terdalam)."""
    script, _ = _resolve("SELECT x.id FROM a x WHERE x.id IN (SELECT x.k FROM b x);")
    hasil = {c.name: c.resolved for c in _cols(script)}
    assert hasil["id"] == "a"
    assert hasil["k"] == "b"


def test_bug8_scope_delete_tidak_bocor():
    """Bug 8: alias dari DELETE tidak boleh terlihat di statement berikutnya (spek 4.5)."""
    script, diags = _resolve("DELETE FROM sesi s WHERE s.a < 1; SELECT s.id FROM pengguna u;")
    assert any(d.level == "error" and "'s'" in d.message for d in diags)


def test_t2_kolom_tanpa_qualifier_satu_tabel():
    """T2: kolom tanpa qualifier di scope dengan satu tabel di-resolve ke tabel itu (spek 4.3)."""
    script, _ = _resolve("SELECT nama FROM pelanggan WHERE aktif = 1;")
    assert {c.resolved for c in _cols(script)} == {"pelanggan"}


def test_t2_kolom_tanpa_qualifier_dua_tabel_ambigu():
    """T2: dua tabel di scope terdalam -> warning 'ambigu', resolved tetap None (spek 4.3)."""
    script, diags = _resolve("SELECT nama FROM pelanggan p, pesanan o;")
    assert {c.resolved for c in _cols(script)} == {None}
    assert any(d.level == "warning" and "ambigu" in d.message for d in diags)