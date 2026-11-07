# Kartu desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi AND/OR dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword SELECT berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Presedensi AND/OR dinyatakan lewat urutan pemanggilan fungsi: `_expr` memanggil `_or`, `_or` memanggil `_and`, `_and` memanggil `_not`. | Tetap memakai satu fungsi `_logical` untuk OR dan AND, dengan mengatur prioritas secara manual lewat pengondisian di dalam loop. | Satu tingkat grammar dipetakan ke satu fungsi (Bab 6), sehingga mudah dicocokkan dengan SPESIFIKASI 3.1. Satu fungsi untuk dua tingkat adalah akar bug 4. |
| 2 | Error recovery memakai panic mode. `_synchronize` membuang token sampai dan termasuk `;` berikutnya, lalu parser lanjut ke statement setelahnya. | Menghentikan parser total tanpa recovery (fail-fast). | Titik koma adalah pembatas antar-statement, jadi titik sinkronisasi paling aman (Bab 6). Kode lama membuang token sampai EOF sehingga statement valid sesudah error ikut terbuang (Bug 6). Fail-fast ditolak karena melanggar SPESIFIKASI bagian 6 dan membuat analisis `campuran_error.sql` gagal mengekstrak statement lain yang valid. |
| 3 | Qualifier dicari dari scope terdalam ke luar dengan berjalan dari `self.scope` mengikuti `parent` sampai entri pertama ditemukan. Alias subquery menutupi alias luar (shadowing), dan subquery tetap bisa merujuk alias luar (correlated). | Tetap membangun daftar scope lalu hanya menghapus `reversed`. | Resolusi nama berjalan dari scope terdalam ke luar dan berhenti di entri pertama (Bab 11), sesuai SPESIFIKASI 4.3. Kode lama membalik urutan dengan `reversed` sehingga scope luar selalu menang dan shadowing tidak pernah terjadi (Bug 7). Alternatif ditolak karena membuat daftar menjadi tidak perlu, sebab pencarian berhenti di entri pertama yang ditemukan. |
| 4 | Kolom tanpa qualifier hanya dilihat di scope terdalam. Satu tabel: di-resolve ke tabel itu. Lebih dari satu tabel: warning “ambigu tanpa skema” dan `resolved` tetap `None`. Tanpa tabel: warning. Kelemahannya, kolom di subquery yang sebenarnya milik tabel luar tidak ter-resolve. | Mencari ke scope induk bila scope terdalam kosong atau tidak menemukan tabel. | Alternatif itu melanggar SPESIFIKASI 4.3. Tanpa skema database tidak ada dasar untuk menyimpulkan kolom itu milik tabel luar, jadi lebih aman memberi `None` dan warning daripada menebak. Pengecekan `self.scope is None` ditambahkan agar `INSERT ... VALUES` yang tidak membuat scope tidak crash. |
| 5 | `INSERT ... SELECT` ditangani dengan memanggil kembali `self._select()` di dalam `_insert()`. Hasilnya dimasukkan ke node `Insert(table_name, columns, values=[], query=select_node)`. | Membuat fungsi pemrosesan SELECT khusus di dalam `_insert()`. | Satu aturan grammar dipetakan ke satu fungsi (Bab 6), jadi `_select()` yang sudah ada dipakai ulang agar penguraian SELECT konsisten di semua tempat. Hasilnya tabel target bernilai C dan tabel sumber bernilai R, sesuai SPESIFIKASI bagian 5. |
