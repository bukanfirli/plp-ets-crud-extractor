

# Laporan TODO

| TODO T1: Penanganan Statement INSERT ... SELECT |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | Menjalankan parser pada input query INSERT INTO a (x) SELECT x FROM b; melempar error ParseError: INSERT ... SELECT belum didukung.Menurut SPESIFIKASI.md bagian 3, aturan grammar insert\_stmt harus mendukung sumber data berupa klausa VALUES maupun subquery select\_stmt. Selain itu, menurut SPESIFIKASI.md bagian 5, ekstraksi matriks CRUD untuk INSERT ... SELECT harus mencatat tabel target (a) sebagai operasi Create (C) dan tabel sumber (b) sebagai operasi Read (R). |
| **Reproduksi Minimal** | INSERT INTO a (x) SELECT x FROM b; Hasil kode lama: ParseError, "INSERT ... SELECT belum didukung". Seharusnya berhasil di-parse, a bernilai C dan b bernilai R. |
| **Akar Masalah** | Cabang SELECT di fungsi \_insert sengaja diisi raise ParseError, jadi fitur ini memang belum ada. Pada recursive descent (Bab 6), satu aturan grammar dipetakan ke satu fungsi dan boleh dipanggil ulang dari aturan lain. Karena grammar insert\_stmt memakai select\_stmt yang sama, \_insert cukup memanggil \_select() yang sudah ada. |
| **Perbaikan** | Pada fungsi \_insert() di file crud/parser.py, cabang pengecekan TokenType.KEYWORD bernilai 'SELECT' diubah dengan memanggil method self.\_select(). Hasil kembalian AST dari \_select() dimasukkan sebagai parameter query pada konstruktor node AST Insert(table\_name, columns, values=\[\], query=select\_node) |
| **Alternatif Ditolak** | Membuat fungsi pemrosesan SELECT khusus di dalam \_insert(). Ditolak karena melanggar prinsip modularitas Recursive Descent Parsing, di mana satu aturan grammar dipetakan ke satu fungsi, sehingga \_select() yang sudah ada seharusnya dipanggil ulang. Dengan begitu penguraian klausa SELECT tetap konsisten di semua tempat, termasuk di subquery dan INSERT ... SELECT, dan perubahan aturan SELECT di masa depan cukup dilakukan di satu fungsi. |
| **Test Regresi** | test\_t1\_insert\_select |
| **Peran AI** | AI membantu mengidentifikasi pemanggilan fungsi self.\_select() di dalam fungsi \_insert() pada crud/parser.py. Verifikasi dilakukan dengan memastikan pengujian test\_t1\_insert\_select berubah dari MERAH (ParseError) menjadi HIJAU (PASSED) dan seluruh 12 pengujian pada tests/test\_parser.py bernilai PASSED. |

| TODO T2: Kolom tanpa qualifier tidak di-resolve |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | SELECT nama FROM pelanggan WHERE aktif \= 1 menghasilkan resolved \= None untuk nama dan aktif. Pada audit.sql baris 20, kolom status, pelanggan\_id, id, dan diblokir tidak punya tabel hasil resolusi. Menurut SPESIFIKASI.md bagian 4.3, satu tabel di scope terdalam berarti kolom di-resolve ke tabel itu, lebih dari satu tabel berarti warning “ambigu tanpa skema” dengan resolved tetap None, dan tanpa tabel berarti warning. |
| **Reproduksi Minimal** | SELECT nama FROM pelanggan WHERE aktif \= 1; |
| **Akar Masalah** | Cabang kolom tanpa qualifier di \_column hanya berisi pass, jadi fitur ini belum diimplementasikan (ditandai TODO(T2)) dan bukan salah logika. Aturan scope pada Bab 11 menyatakan kolom tanpa qualifier hanya dicari di scope terdalam. |
| **Perbaikan** | Pada file crud/resolver.py, fungsi \_column diisi pada bagian TODO(T2). Fungsi hanya melihat scope terdalam. Jika ada tepat satu tabel di scope itu, col.resolved diisi dengan nama tabel tersebut. Jika ada lebih dari satu tabel, dibuat warning “kolom ‘nama’ ambigu tanpa skema” dan resolved tetap None. Jika scope kosong atau bernilai None (kasus INSERT ... VALUES yang tidak membuat scope), dibuat warning dan resolved tetap None. |
| **Alternatif Ditolak** | Mencari ke scope induk (scope luar) bila scope terdalam kosong atau tidak menemukan tabel. Alternatif ini ditolak karena Melanggar SPESIFIKASI.md bagian 4.3 yang menyatakan kolom tanpa qualifier hanya melihat scope terdalam. Selain itu, cara ini bisa me-resolve kolom di dalam subquery ke tabel di query luar secara keliru, padahal tanpa skema database tidak ada dasar untuk menyimpulkan kolom itu milik tabel luar. |
| **Test Regresi** | test\_t2\_kolom\_tanpa\_qualifier\_satu\_tabel dan test\_t2\_kolom\_tanpa\_qualifier\_dua\_tabel\_ambigu |
| **Peran AI** | AI menyarankan struktur tiga cabang dan pengecekan self.scope is None agar INSERT ... VALUES tidak crash. Test dijalankan merah lebih dulu, lalu hijau, test lama test\_kolom\_tanpa\_qualifier\_satu\_tabel ikut hijau, dan seluruh suite lulus. |

| TODO T3: Komentar Blok Lintas Baris (Block Comment) |  |
| :---- | :---- |
| **Ditemukan oleh:** Bimo Surya Anggara **Diperbaiki oleh:** Firliana Febrina |  |
| **Gejala** | Menjalankan lexer pada input yang memiliki komentar blok “/\* ... \*/” melempar error “LexError: Baris 1, kolom 1: komentar blok belum didukung”. Menurut SPESIFIKASI.md bagian 2.3, komentar blok harus diabaikan dan tidak boleh menghasilkan token. |
| **Reproduksi Minimal** | /\* komentar \*/ SELECT 1;  Hasil kode lama: LexError, "Baris 1, kolom 1: komentar blok belum didukung". Seharusnya komentar diabaikan dan tidak menghasilkan token.  |
| **Akar Masalah** | Fungsi \_scan\_token pada crud/lexer.py cabang ch \== "/" dan \_peek() \== "\*" sengaja dipasang raise LexError sementara oleh pembuat boilerplate. |
| **Perbaikan** | Mengganti raise LexError dengan perulangan while untuk mengonsumsi seluruh karakter komentar hingga menemukan pasangan penutup \*/. Jika input habis (\_at\_end()) sebelum menemukan penutup, lexer akan melempar LexError("komentar blok tidak ditutup") |
| **Alternatif Ditolak** | Menggunakan regex untuk menghapus komentar. Ditolak karena melanggar pola Single Pass Scanner berbasis penunjuk posisi di crud/lexer.py. |
| **Test Regresi** | test\_t3\_block\_comment  test\_t3\_block\_comment\_unclosed  |
| **Peran AI** | AI memberikan struktur perulangan pencarian token penutup \*/. Diverifikasi lewat pengujian Pytest hingga berstatus PASSED. |

# 

# Laporan Bug

| BUG 1: Keyword Peka Huruf Besar/Kecil (Case-Sensitive Keyword) |  |
| :---- | :---- |
| **Ditemukan oleh:** Bimo Surya Anggara **Diperbaiki oleh:** Firliana Febrina |  |
| **Gejala** | Ketika mengeksekusi tokenize(“Select”), lexer mengembalikan token bertipe TokenType.IDENT dengan nilai ‘Select’, padahal menurut SPESIFIKASI.md bagian 2.2, keyword bersifat tidak peka huruf besar/kecil (case-insensitive) dan nilainya harus selalu dinormalisasi ke huruf besar (KEYWORD dengan nilai ‘SELECT’). |
| **Reproduksi Minimal** | Select a FROM t; Hasil kode lama: kata "Select" dibaca IDENT, bukan KEYWORD. Seharusnya KEYWORD bernilai SELECT. |
| **Akar Masalah** | Fungsi \_word di crud/lexer.py mengecek teks identifier mentah langsung ke kamus KEYWORDS. Karena string 'Select' mengandung huruf kapital di awal, pencocokan dengan string serba huruf besar di kamus KEYWORDS gagal, sehingga kata tersebut keliru diidentifikasi sebagai nama variabel/kolom biasa (IDENT). |
| **Perbaikan** | Pada fungsi \_word, teks yang dibaca dinormalisasi lebih dulu menggunakan .upper(). Teks hasil konversi dicocokkan ke kamus KEYWORDS. Jika cocok, token dibuat berjenis TokenType.KEYWORD dengan nilai huruf besar tersebut. Jika tidak cocok, kata tetap menjadi TokenType.IDENT. |
| **Alternatif Ditolak** | Mengubah seluruh isi kamus KEYWORDS untuk mencakup kombinasi huruf besar-kecil. Ditolak karena tidak efisien dan melanggar struktur konstanta KEYWORDS di crud/lexer.py |
| **Test Regresi** | test\_bug1\_keyword\_case\_insensitive |
| **Peran AI** | AI membantu menunjuk bahwa pencocokan ke KEYWORDS di fungsi \_word dilakukan pada teks mentah tanpa normalisasi huruf. Diverifikasi dengan pytest: test\_bug1\_keyword\_case\_insensitive berubah dari merah menjadi hijau dan test lexer lama tetap lulus. |

| BUG 2: Operator Pertidaksamaan \<\> Terpecah (Maximal Munch Violation) |  |
| :---- | :---- |
| **Ditemukan oleh:** Bimo Surya Anggara **Diperbaiki oleh:** Firliana Febrina |  |
| **Gejala** | Menjalankan lexer pada ekspresi a \<\> b memecah operator menjadi dua token terpisah: \< dan \>, sehingga menyebabkan ParseError pada parser. Menurut SPESIFIKASI.md bagian 2.5 (maximal munch), \<\> harus dibaca sebagai satu token operator OP. |
| **Reproduksi Minimal** | SELECT a FROM t WHERE a \<\> b;  Hasil kode lama: "\<\>" terpecah menjadi "\<" dan "\>", lalu ParseError "diharapkan ekspresi, ditemukan '\>'". Seharusnya satu token OP "\<\>".  |
| **Akar Masalah** | Cabang penanganan ch \== "\<" pada fungsi \_scan\_token di crud/lexer.py hanya mengecek self.\_match("=") untuk operator \<=, tanpa mengecek kemungkinan karakter \> untuk operator \<\>. |
| **Perbaikan** | Menambahkan cabang elif self.\_match(“\>”): op \= “\<\>” pada cabang ch \== “\<” agar lexer mengenali operator \<\> sebagai satu token. |
| **Alternatif Ditolak** | Membiarkan lexer menghasilkan 2 token dan menggabungkannya di Parser. Ditolak karena melanggar aturan pembagian tugas antara Lexer dan Parser. |
| **Test Regresi** | test\_bug2\_maximal\_munch |
| **Peran AI** | AI menunjukkan percabangan \_match yang hilang. Diverifikasi dengan pengujian Pytest. |

| BUG 3: Escape Quote Tunggal dalam String (Escaped Single Quote) |  |
| :---- | :---- |
| **Ditemukan oleh:** Bimo Surya Anggara **Diperbaiki oleh:** Firliana Febrina |  |
| **Gejala** | Menjalankan lexer pada string SQL ‘O’’Brien’ menghentikan pembacaan string saat menemukan karakter ‘ kedua, menghasilkan string ‘O’ dan melempar error sintaksis pada kata sisa Brien’. Menurut SPESIFIKASI.md bagian 2.4, dua karakter kutip tunggal berdampingan (‘’) di dalam literal string mewakili satu karakter kutip tunggal ‘. |
| **Reproduksi Minimal** | SELECT a FROM t WHERE n \= 'O''Brien';  Hasil kode lama: string berhenti di kutip kedua, nilainya 'O' dan sisa "Brien'" memicu error. Seharusnya satu token STRING bernilai O'Brien.  |
| **Akar Masalah** | Fungsi \_string pada crud/lexer.py menganggap setiap karakter ' yang ditemukan sebagai tanda berakhirnya string tanpa mengintip (peek) karakter berikutnya. |
| **Perbaikan** | Pada fungsi \_string, ketika karakter ' ditemukan, dipanggil self.\_match("'"). Jika bernilai True, satu karakter ' ditambahkan ke dalam nilai string dan pembacaan dilanjutkan. Jika False, string dianggap selesai. |
| **Alternatif Ditolak** | Menggunakan escape backslash \\'. Ditolak karena spesifikasi SQL standar menggunakan ''. |
| **Test Regresi** | test\_bug3\_escaped\_string |
| **Peran AI** | AI memberikan logika pengintipan \_match("'"). Diverifikasi lewat Pytest. |

| BUG 4: Presedensi Operator Logika AND/OR (Operator Precedence) |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | Ketika mengeksekusi ekspresi logika a \= 1 OR b \= 2 AND c \= 3, parser menghasilkan pohon AST dengan simpul utama (root) berupa AND, yang setara dengan bentuk (a \= 1 OR b \= 2\) AND c \= 3\. Pada file audit.sql baris 2, bentuk pohon ekspresi WHERE juga terasosiasi secara keliru. Menurut SPESIFIKASI.md bagian 3.1, operator OR berada pada presedensi Tingkat 1 dan AND pada Tingkat 2, sehingga operator AND harus mengikat operand-nya lebih kuat.   |
| **Reproduksi Minimal** | SELECT a FROM t WHERE a \= 1 OR b \= 2 AND c \= 3; Hasil kode lama: akar pohon AND, yaitu (a \= 1 OR b \= 2\) AND c \= 3\. Seharusnya akar OR, yaitu a \= 1 OR (b \= 2 AND c \= 3). |
| **Akar Masalah** | Satu fungsi (\_logical) dipakai untuk dua tingkat presedensi sekaligus, sehingga OR dan AND diproses dalam satu loop dari kiri ke kanan. Pada recursive descent (Bab 6), presedensi dibentuk oleh urutan pemanggilan fungsi: tingkat yang lebih rendah memanggil tingkat yang lebih tinggi untuk mengambil operandnya. Karena tidak dipisah, AND tidak pernah mengikat operandnya lebih dulu daripada OR. |
| **Perbaikan** | Memecah fungsi \_logical di crud/parser.py menjadi dua fungsi terpisah: Fungsi \_or() yang memanggil \_and() untuk mengambil operand-nya. Fungsi \_and() yang memanggil \_not() untuk mengambil operand-nya. Fungsi utama \_expr() sekarang memanggil \_or(). |
| **Alternatif Ditolak** | Mengubah prioritas secara manual di dalam loop dengan pengondisian manual. Ditolak karena melanggar arsitektur Recursive Descent Parsing yang bergantung pada tumpukan pemanggilan fungsi (call stack). |
| **Test Regresi** | test\_bug4\_presedensi\_and\_or |
| **Peran AI** | AI membantu merestrukturisasi pembagian fungsi \_or dan \_and sesuai Bab 6 Crafting Interpreters. Verifikasi dilakukan dengan memastikan pengujian test\_bug4\_presedensi\_and\_or berstatus PASSED dan seluruh 12 pengujian pada tests/test\_parser.py bernilai PASSED. |

| BUG 5: Klausa LEFT OUTER JOIN Terurai Salah (Optional Keyword OUTER) |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | Menjalankan parser pada query yang menggunakan kata kunci opsional LEFT OUTER JOIN melempar error ParseError: diharapkan JOIN, ditemukan ‘OUTER’. Menurut SPESIFIKASI.md bagian 3, aturan grammar untuk gabungan tabel adalah join \= \[ “INNER” \| “LEFT” \[ “OUTER” \] \] “JOIN” ..., di mana kata OUTER bersifat opsional setelah LEFT. |
| **Reproduksi Minimal** | SELECT a FROM t LEFT OUTER JOIN u ON t.id \= u.id; Hasil kode lama: ParseError, "diharapkan JOIN, ditemukan 'OUTER'". Seharusnya berhasil di-parse dengan jenis join LEFT. |
| **Akar Masalah** | Setelah LEFT, fungsi \_join langsung menuntut JOIN dengan \_expect\_kw, padahal grammar menandai OUTER sebagai bagian opsional. Di recursive descent, bagian opsional \[ ... \] dipetakan ke pemeriksaan yang boleh gagal (\_match\_kw), bukan ke pemeriksaan wajib (\_expect\_kw) yang melempar error. |
| **Perbaikan** | Pada fungsi \_join di crud/parser.py, ditambahkan pemeriksaan opsional self.\_match\_kw("OUTER") setelah kata kunci LEFT terdeteksi, sebelum memvalidasi kata kunci utama JOIN. |
| **Alternatif Ditolak** | Memasukkan LEFT OUTER sebagai satu kesatuan token baru di Lexer. Ditolak karena LEFT dan OUTER adalah dua token KEYWORD terpisah yang penanganannya merupakan tanggung jawab Parser. |
| **Test Regresi** | test\_bug5\_left\_outer\_join |
| **Peran AI** | AI membantu mengidentifikasi posisi penyelipan self.\_match\_kw("OUTER") di fungsi \_join. Diverifikasi dengan mengecek status Pytest berubah dari MERAH menjadi HIJAU. |

| BUG 6: Pemulihan Panic Mode Error Recovery Membuang Semua Token (\_synchronize) |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | Ketika parser menemukan satu kesalahan sintaksis pada suatu statement (misalnya SELECT FROM x; SELECT id FROM y;), parser mengembalikan 0 statement yang berhasil di-parse. Seluruh perintah SQL yang valid di bawahnya ikut terbuang. Menurut SPESIFIKASI.md bagian 6, parser harus melakukan panic mode error recovery: setelah error, token dibuang sampai dan termasuk ; berikutnya, lalu parsing dilanjutkan ke statement setelahnya. |
| **Reproduksi Minimal** | SELECT FROM x; SELECT id FROM y; Hasil kode lama: 1 error (benar), tetapi 0 statement berhasil di-parse. Seharusnya statement kedua tetap diproses (1 statement). |
| **Akar Masalah** | \_synchronize membuang token sampai akhir file. Tujuan panic mode (Bab 6\) adalah membuang token hanya sampai titik sinkronisasi yang aman, yaitu ; sebagai batas statement. Karena titik berhenti dipasang di akhir input, statement valid sesudah error ikut terbuang. |
| **Perbaikan** | Mengubah perulangan pada fungsi \_synchronize di crud/parser.py agar berhenti tepat setelah token TokenType.SEMICOLON dikonsumsi. |
| **Alternatif Ditolak** | Menghentikan parser total (fail-fast) tanpa recovery. Ditolak karena melanggar SPESIFIKASI.md bagian 6 dan menyebabkan analisis file campuran\_error.sql gagal mengekstrak statement lainnya yang valid. |
| **Test Regresi** | test\_bug6\_error\_recovery\_satu\_error\_per\_statement |
| **Peran AI** | AI membantu mengidentifikasi kondisi henti loop pada fungsi \_synchronize di crud/parser.py. Diverifikasi dengan memastikan pengujian test\_bug6\_error\_recovery\_satu\_error\_per\_statement berstatus PASSED dan statement valid setelah error pada campuran\_error.sql berhasil diekstrak. |

| BUG 7: Alias Bayangan (Shadowing) Salah |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | Pada audit.sql baris 12, kolom x.pelanggan\_id dan x.total di dalam subquery ter-resolve ke tabel pelanggan, padahal seharusnya pesanan. Menurut SPESIFIKASI.md bagian 4.3, qualifier dicari dari scope terdalam ke luar dan yang pertama ditemukan dipakai, sehingga alias di subquery menutupi alias yang sama di luar. |
| **Reproduksi Minimal** | SELECT x.id FROM a x WHERE x.id IN (SELECT x.k FROM b x); Hasil kode lama: x.k ter-resolve ke a. Seharusnya b. |
| **Akar Masalah** | \_lookup mengumpulkan scope dari yang terdalam, lalu membaliknya dengan reversed, sehingga pencarian justru mulai dari scope terluar. Pada Bab 11, nama dicari dari scope terdalam ke luar dan berhenti di entri pertama. Karena urutannya terbalik, nama di scope luar selalu menang dan shadowing tidak pernah terjadi. |
| **Perbaikan** | File crud/resolver.py, fungsi \_lookup. Fungsi kini berjalan dari self.scope mengikuti parent sampai nama ditemukan. |
| **Alternatif Ditolak** | Tetap membangun daftar scope lalu hanya menghapus reversed. Ditolak karena membuat daftar menjadi tidak perlu, sebab pencarian berhenti di entri pertama yang ditemukan. |
| **Test Regresi** | test\_bug7\_alias\_shadowing |
| **Peran AI** | AI membantu menunjukkan bahwa reversed(chain) menjadi sumber salah urutan dan membantu menyusun test regresi. Test dijalankan merah lebih dulu (assert ‘a’ \== ‘b’), lalu hijau setelah perbaikan, dan seluruh test lain tetap lulus (49 passed). |

| BUG 8: Scope DELETE Bocor ke Statement Berikutnya |  |
| :---- | :---- |
| **Ditemukan oleh:** Firliana Febrina **Diperbaiki oleh:** Bimo Surya Anggara |  |
| **Gejala** | Pada audit.sql baris 18, s.id di SELECT ... FROM pengguna u ter-resolve ke tabel sesi, padahal alias s hanya dideklarasikan di DELETE FROM sesi s pada baris 16\. Menurut SPESIFIKASI.md bagian 4.5, alias dari statement sebelumnya tidak boleh terlihat. Seharusnya muncul error “alias ‘s’ tidak terdefinisi”. |
| **Reproduksi Minimal** | DELETE FROM sesi s WHERE s.a \< 1; SELECT s.id FROM pengguna u; |
| **Akar Masalah** | \_delete membuka scope baru dengan \_push() tetapi tidak pernah menutupnya dengan \_pop(). Pada Bab 11, beginScope harus berpasangan dengan endScope. Scope DELETE tersisa, sehingga statement berikutnya masih melihat alias s. \_select dan \_update sudah berpasangan dengan benar. |
| **Perbaikan** | File crud/resolver.py, fungsi \_delete: menambahkan self.\_pop() di akhir. |
| **Alternatif Ditolak** | Mereset self.scope menjadi None di resolve\_statement. Ditolak karena hanya menutupi gejala, tidak memperbaiki push dan pop yang tidak seimbang, dan bisa menyembunyikan bug serupa di kemudian hari. |
| **Test Regresi** | test\_bug8\_scope\_delete\_tidak\_bocor  |
| **Peran AI** | AI membantu membandingkan \_delete dengan \_update sehingga \_pop yang hilang ketahuan. Test dijalankan merah lebih dulu (tidak ada error alias ‘s’), lalu hijau setelah perbaikan, dan seluruh test lulus. |

| BUG 9: Subquery pada UPDATE Ditandai Operasi U (Update) |  |
| :---- | :---- |
| **Ditemukan oleh:** Bimo Surya Anggara **Diperbaiki oleh:** Firliana Febrina |  |
| **Gejala** | Pada UPDATE, tabel yang hanya dibaca lewat subquery ikut ditandai U. Contoh: UPDATE pelanggan SET level \= ‘gold’ WHERE id IN (SELECT pelanggan\_id FROM pesanan); menghasilkan pesanan bernilai {‘U’}, seharusnya {‘R’}. Pada data sampel, test\_matrix\_laporan\_penjualan menghasilkan pesanan: RUD, seharusnya RD. Menurut SPESIFIKASI.md bagian 5, pada UPDATE hanya tabel target yang bernilai U, sedangkan tabel lain (subquery di SET maupun WHERE) bernilai R. Membaca tabel lewat subquery selalu R, apa pun jenis statement luarnya. |
| **Reproduksi Minimal** | UPDATE pelanggan SET level \= 'gold' WHERE id IN (SELECT pelanggan\_id FROM pesanan); Hasil kode lama: pesanan bernilai {U}. Seharusnya pelanggan {U} dan pesanan {R}. |
| **Akar Masalah** | Di cabang UPDATE pada analyze\_statement, bagian SET dan WHERE ditelusuri dengan operasi “U”, padahal bagian itu hanya membaca data. Akibatnya tabel di dalam subquery ikut dicap “U”, padahal menurut aturan CRUD subquery selalu “R”. Hanya tabel target UPDATE yang boleh “U”. |
| **Perbaikan** | Perubahan dilakukan pada file crud/analyzer.py, fungsi analyze\_statement(), cabang ast.Update. Pemanggilan \_collect() untuk assignment.value (klausa SET) dan stmt.where diubah dari “U” menjadi “R” karena keduanya hanya membaca data. Tabel target UPDATE tetap ditandai “U” lewat usage\[stmt.table.name\].add(“U”). |
| **Alternatif Ditolak** | memfilter atau mengubah huruf operasi di level penulisan CSV/CLI. Ditolak karena klasifikasi dan penandaan operasi tabel harus ditangani tepat di modul Analyzer. Perbaikan di lapisan keluaran hanya menyembunyikan gejala, sementara hasil analyze\_statement() yang dipakai API publik dan test tersembunyi tetap salah. |
| **Test Regresi** | test\_bug9\_subquery\_in\_update\_is\_read di tests/test\_tambahan.py. |
| **Peran AI** | AI membantu menemukan penyebab kesalahan, yaitu operasi "U" pada pemanggilan \_collect() di bagian ast.Update ikut terbawa ke subquery. Setelah diperbaiki, dilakukan pengujian untuk memastikan test\_bug9\_subquery\_in\_update\_is\_read berstatus PASSED dan seluruh test Pytest berhasil tanpa error. Hasil pada detail\_sesudah.csv juga dibandingkan dengan hasil sebelumnya untuk memastikan hanya tabel subquery yang berubah dari "U" menjadi "R". |

