# Laporan Akhir

## 1. Hasil Evaluasi

Dievaluasi: `audit.sql`, `campuran_error.sql`, `laporan_penjualan.sql`, `pemeliharaan.sql` (27 triple)

| Metode | Precision | Recall | F1   |
|--------|-----------|--------|------|
| parser | 1.00      | 1.00   | 1.00 |
| regex  | 0.65      | 0.81   | 0.72 |

### [regex]

**Salah ditemukan (FP):**

- `('audit.sql', 16, 'sesi', 'R')`
- `('campuran_error.sql', 4, 'pesanan', 'R')`
- `('campuran_error.sql', 8, 'keranjang', 'R')`
- `('laporan_penjualan.sql', 2, 'pelanggan', 'D')`
- `('laporan_penjualan.sql', 2, 'pelanggan', 'R')`
- `('laporan_penjualan.sql', 2, 'pesanan', 'R')`
- `('laporan_penjualan.sql', 2, 'rahasia', 'R')`
- `('laporan_penjualan.sql', 15, 'pesanan', 'R')`
- `('pemeliharaan.sql', 2, 'crm.alamat', 'R')`
- `('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')`
- `('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')`
- `('pemeliharaan.sql', 15, 'crm.alamat', 'R')`

**Terlewat (FN):**

- `('audit.sql', 2, 'pesanan', 'R')`
- `('laporan_penjualan.sql', 3, 'pelanggan', 'R')`
- `('laporan_penjualan.sql', 3, 'pesanan', 'R')`
- `('pemeliharaan.sql', 3, 'crm.alamat', 'R')`
- `('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')`

---

## 2. Tiga Kasus di Mana Regex Salah

### 1. Kesalahan Klausa `DELETE FROM` Dibaca sebagai Operasi Read (R)

**a. SQL:**

```sql
DELETE FROM keranjang WHERE dibuat < :batas;   -- campuran_error.sql baris 8
DELETE FROM pesanan WHERE tanggal < :batas;    -- laporan_penjualan.sql baris 15
```

**b. Kesalahan Regex:** Regex menghasilkan False Positive (FP) `(8, keranjang, R)` dan `(15, pesanan, R)`. Pola regex mencocokkan kata kunci `FROM` sebagai awal ekspresi pembacaan data (R).

**c. Mengapa Parser Benar:** Sesuai konsep Parsing (Bab 5-6), `DELETE FROM <tabel>` adalah satu aturan grammar utuh (`delete_stmt`). Kata kunci `FROM` merupakan bagian sintaksis wajib dari perintah `DELETE`, bukan penanda pembacaan data. Spesifikasi Bagian 5 menetapkan tabel target `DELETE` hanya diberi label **D**.

### 2. Kesalahan Statement Berformat Error Tetap Diproses oleh Regex

**a. SQL:**

```sql
SELECT id nama, FROM pesanan;   -- campuran_error.sql baris 4
```

**b. Kesalahan Regex:** Regex tetap mengekstrak `(4, pesanan, R)` sebagai False Positive (FP) meskipun query tersebut cacat sintaksis (koma gantung sebelum `FROM`).

**c. Mengapa Parser Benar:** Parser melakukan pengecekan grammar dan struktur token (Bab 6). Saat menemukan koma gantung tanpa kolom lanjutan, Parser melempar `ParseError`, menghentikan parsing statement tersebut, dan menjalankan Error Recovery (Panic Mode `_synchronize`) hingga titik koma `;`. Regex tidak memiliki pemahaman validasi sintaksis.

### 3. Kesalahan Kata di Dalam Komentar dan String Literal Terikut Sebagai Tabel

**a. SQL:** `laporan_penjualan.sql` baris 1-3 (`-- DELETE FROM pelanggan` dan `'FROM rahasia'`).

**b. Kesalahan Regex:** Regex membaca `pelanggan` di dalam komentar sebagai D & R, serta `'rahasia'` di dalam string sebagai tabel R.

**c. Mengapa Parser Benar:** Sesuai konsep Lexing/Scanning (Bab 4), Lexer membuang seluruh isi komentar sehingga tidak menghasilkan token. Selain itu, teks dalam kutip tunggal dibungkus menjadi satu token `STRING` utuh. Parser hanya memproses token `IDENT` pada posisi grammar yang valid.

---

## 3. Batas Pendekatan Kami

### 1. Fitur di Luar Grammar (CTE / WITH dan UNION)

**a. Contoh SQL:**

```sql
WITH pesanan_baru AS (SELECT * FROM pesanan)
SELECT * FROM pesanan_baru;
```

atau

```sql
SELECT id FROM a UNION SELECT id FROM b;
```

**b. Akibat pada CRUD Matrix:** Statement mengalami `ParseError` dan dibuang seluruhnya, menyebabkan tabel `a`, `b`, maupun `pesanan` hilang dari matrix (`matrix={}`).

**c. Informasi yang Dibutuhkan:** Perluasan aturan grammar parser untuk mendukung klausa `WITH` dan `UNION`, serta pembaruan pada Resolver agar mengenali CTE sebagai nama tabel sementara (*temporary scope alias*).

### 2. Sintaksis Asing Menghentikan Seluruh Berkas (LexError)

**a. Contoh SQL:**

```sql
SELECT "nama" FROM a; DELETE FROM b;
```

(Quoted identifier menggunakan petik ganda.)

**b. Akibat pada CRUD Matrix:** Lexer melempar `LexError` pada baris pertama. Akibatnya, seluruh pemrosesan file berhenti dan statement valid di bawahnya (`DELETE FROM b`) ikut hilang.

**c. Informasi yang Dibutuhkan:** Penambahan penanganan Quoted Identifier (`"..."` atau `[...]`) pada Lexer atau pembuatan mekanisme error recovery di tingkat Lexer agar kesalahan tokenisasi tidak menggagalkan seluruh berkas.

### 3. Resolusi Kolom Ambigu Tanpa Skema Database

**a. Contoh SQL:**

```sql
SELECT nama FROM pelanggan, pengguna;
```

**b. Akibat pada CRUD Matrix:** Kolom `nama` tidak dapat dikaitkan secara pasti ke tabel `pelanggan` atau `pengguna`. Resolver hanya mengeluarkan warning `kolom 'nama' ambigu tanpa skema` dan `resolved` tetap `None`.

**c. Informasi yang Dibutuhkan:** Metadata skema database riil (Database Catalog / DDL) untuk mengetahui daftar kolom dari masing-masing tabel secara pasti.

---

## 4. Pembagian Kerja

### Firliana Febrina

Memperbaiki kode pada modul Lexer (`crud/lexer.py`) dan Analyzer (`crud/analyzer.py`), menulis test regresi untuk Bug 1, 2, 3, 9, TODO T3, serta menambahkan 1 test kasus tepi di `tests/test_tambahan.py`. Selain itu bertugas melakukan audit pelacakan bug pada modul Parser dan Resolver, juga merancang laporan akhir.

### Bimo Surya Anggara

Memperbaiki kode pada modul Parser (`crud/parser.py`) dan Resolver (`crud/resolver.py`), menulis test regresi untuk Bug 4, 5, 6, 7, 8, TODO T1 & T2, serta menambahkan 4 test kasus tepi lainnya di `tests/test_tambahan.py`. Selain itu bertugas melakukan audit pelacakan bug pada modul Lexer dan Analyzer, juga merancang kartu desain.

### Bagaimana Memastikan Keduanya Memahami Seluruh Kode

Kami tidak mengerjakan modul secara terpisah. Setiap bug dikerjakan lintas anggota: satu orang menemukan dan melacak bug, orang lainnya memperbaikinya. Bimo menemukan bug di modul Lexer dan Analyzer yang kemudian diperbaiki oleh Firli, sedangkan Firli menemukan bug di modul Parser dan Resolver yang kemudian diperbaiki oleh Bimo. Dengan pola ini, masing-masing dari kami bersentuhan dengan keempat modul, yaitu sebagai pencari bug di satu sisi dan sebagai pemperbaik di sisi lain. Terakhir, label ground truth disusun bersama berdasarkan `SPESIFIKASI.md`, bukan dari output tool.
