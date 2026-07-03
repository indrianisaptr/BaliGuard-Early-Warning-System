# Baseline Evaluasi Model — BaliGuard Crisis Classification

**Status:** Baseline (sebelum retraining)
**Tanggal dokumentasi:** 2026-07-03

---

## 1. Ringkasan Model

Model klasifikasi crisis level pada sistem BaliGuard terdiri dari dua komponen utama:

- **Random Forest Classifier** — memprediksi `rf_predicted_level` (AMAN / WASPADA / SIAGA / KRISIS) beserta probabilitas per kelas (`prob_aman`, `prob_waspada`, `prob_siaga`, `prob_krisis`).
- **Isolation Forest** — mendeteksi anomali (`iso_anomaly`, `iso_score`) sebagai sinyal pendukung di luar klasifikasi crisis level.

Kedua model di-load dari artefak yang tersimpan (`model_random_forest.pkl`, `model_isolation_forest.pkl`, `scaler.pkl`, `label_encoder.pkl`) dan dijalankan melalui inference pipeline (`update_pipeline.py`) tanpa proses training ulang.

## 2. Ringkasan Pipeline

Kondisi pipeline yang telah tervalidasi pada saat baseline ini diambil:

- `update_pipeline.py` sudah sinkron dengan notebook training (NB05).
- Inference menggunakan **19 fitur** yang sama dengan training.
- External engineered features telah berhasil di-*merge* ke dataset utama.
- Seluruh **208 bulan** dalam dataset berhasil diprediksi (tidak ada baris yang gagal/terlewat).
- Tidak ada lagi fallback rule-based yang aktif — seluruh prediksi berasal dari model terlatih.
- Probabilitas kelas pada setiap baris sudah berjumlah tepat 1.
- Pipeline berhasil mengirimkan hasil prediksi ke Supabase.

## 3. Ringkasan Preprocessing

Preprocessing pada tahap inference mengikuti alur yang sama dengan yang digunakan pada notebook training, tanpa modifikasi:

- Fitur numerik telah melalui proses imputasi (ffill → bfill → median) sebagaimana dilakukan pada notebook training sebelum standardisasi.
- Standardisasi fitur menggunakan `StandardScaler` yang sama (artefak `scaler.pkl`) dengan yang digunakan saat training.
- Tidak ada perubahan preprocessing, model, maupun notebook yang dilakukan dalam proses pembuatan dokumen baseline ini.

## 4. Jumlah Fitur dan Jumlah Data

| Item                      | Nilai |
| ------------------------- | ----- |
| Jumlah fitur (inference)  | 19    |
| Jumlah data (baris/bulan) | 208   |

## 5. Distribusi Ground Truth

| Crisis Level    | Jumlah        |
| --------------- | ------------- |
| AMAN            | 38            |
| WASPADA         | 117           |
| SIAGA           | 40            |
| KRISIS          | 13            |
| **Total** | **208** |

## 6. Distribusi Prediksi

| Crisis Level    | Jumlah        |
| --------------- | ------------- |
| AMAN            | 39            |
| WASPADA         | 114           |
| SIAGA           | 41            |
| KRISIS          | 14            |
| **Total** | **208** |

## 7. Classification Report

| Kelas   | Precision | Recall | F1-score | Support |
| ------- | --------- | ------ | -------- | ------- |
| AMAN    | 0.9231    | 0.9474 | 0.9351   | 38      |
| KRISIS  | 0.9286    | 1.0000 | 0.9630   | 13      |
| SIAGA   | 0.9268    | 0.9500 | 0.9383   | 40      |
| WASPADA | 0.9737    | 0.9487 | 0.9610   | 117     |

**Accuracy:** 0.9519 (208 data)

**Macro Average**

- Precision: 0.9380
- Recall: 0.9615
- F1-score: 0.9493

**Weighted Average**

- Precision: 0.9526
- Recall: 0.9519
- F1-score: 0.9520

## 8. Ringkasan Confidence

| Statistik    | Nilai    |
| ------------ | -------- |
| Count        | 208      |
| Mean         | 0.759724 |
| Std          | 0.135078 |
| Min          | 0.386930 |
| 25%          | 0.666665 |
| 50% (Median) | 0.788765 |
| 75%          | 0.877266 |
| Max          | 0.961394 |

## 9. Ringkasan Probability

- Seluruh probabilitas kelas pada setiap baris sudah valid, dengan jumlah probabilitas per baris tepat 1.
- Tidak ditemukan nilai NaN pada kolom `rf_predicted_level`.

## 10. Interpretasi Hasil

- Model menunjukkan performa klasifikasi yang tinggi pada seluruh kelas, dengan F1-score di atas 0.93 untuk masing-masing dari empat kelas crisis level.
- Recall tertinggi terdapat pada kelas **KRISIS** (1.0000), menunjukkan model tidak melewatkan satu pun kasus krisis pada data yang dievaluasi.
- Distribusi prediksi (39/114/41/14) mendekati distribusi ground truth (38/117/40/13), dengan selisih kecil pada tiap kelas.
- Rata-rata confidence prediksi berada di angka 0.76 dengan sebaran (std) 0.135, serta nilai minimum confidence 0.387 — mengindikasikan sebagian kecil prediksi memiliki tingkat keyakinan model yang lebih rendah dibanding mayoritas.
- **Catatan penting:** metrik pada bagian ini (accuracy 0.9519, F1 macro 0.9493) dihasilkan dari evaluasi terhadap seluruh 208 baris dataset yang sama dengan yang diproses oleh pipeline inference saat ini. Dokumen ini tidak menyatakan apakah evaluasi tersebut dilakukan pada data yang sama dengan data training model (in-sample) atau pada split terpisah, karena informasi tersebut tidak disertakan dalam data yang diberikan. Metrik pada dokumen ini merupakan evaluasi terhadap output pipeline inference saat ini. Metrik ini memiliki tujuan yang berbeda dengan hasil evaluasi TimeSeriesSplit pada notebook training, sehingga keduanya tidak sebaiknya dibandingkan secara langsung tanpa mempertimbangkan skenario evaluasi yang digunakan.

## 11. Kesimpulan Model Saat Ini

Model saat ini berhasil memprediksi seluruh 208 bulan data tanpa fallback rule-based, dengan probabilitas kelas yang valid dan tanpa nilai kosong pada hasil prediksi. Berdasarkan metrik yang diberikan, model menunjukkan tingkat akurasi dan F1-score yang tinggi pada evaluasi yang dilakukan. Dokumen ini mencatat kondisi model dan pipeline apa adanya, sebagai titik acuan (baseline) sebelum proses retraining dilakukan.

---

## 12. Baseline for Future Retraining

Dokumen ini ditetapkan sebagai **baseline resmi** kondisi model, pipeline, dan hasil evaluasi sebelum proses retraining dilakukan. Seluruh angka pada dokumen ini — termasuk distribusi ground truth, distribusi prediksi, classification report (precision, recall, F1-score per kelas, macro average, weighted average), ringkasan confidence, dan ringkasan probability — dicatat sebagaimana adanya pada saat pengambilan data, tanpa perubahan pada model, pipeline, notebook, maupun preprocessing.

Setelah proses retraining dilakukan, seluruh metrik pada model hasil retraining harus dibandingkan langsung terhadap metrik pada dokumen ini menggunakan struktur evaluasi yang sama, sehingga:

- Perubahan performa (accuracy, precision, recall, F1-score per kelas, macro/weighted average) dapat diukur secara objektif dan dapat dilacak.
- Perubahan pada distribusi prediksi terhadap ground truth dapat diidentifikasi per kelas.
- Perubahan pada karakteristik confidence dan validitas probability dapat dipantau untuk memastikan tidak terjadi regresi kualitas model.

Dokumen ini tidak boleh diubah setelah retraining dilakukan; dokumen evaluasi baru untuk model hasil retraining sebaiknya dibuat secara terpisah agar perbandingan tetap objektif dan dapat diaudit.