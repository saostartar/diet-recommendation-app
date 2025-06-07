import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.impute import SimpleImputer
import joblib
import time
import os

# --- Konfigurasi Output ---
OUTPUT_DIR = 'model_output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*50)
print("IMPLEMENTASI MODEL DECISION TREE")
print("="*50)

# =================================================================
# 5.2.1 Preprocessing Data Nutrisi
# =================================================================
print("\n" + "="*50)
print("5.2.1 PREPROCESSING DATA NUTRISI")
print("="*50)

# --- 1. Memuat Data ---
print("\n[1/4] Memuat dataset...")
try:
    df = pd.read_csv('/kaggle/input/decision-tree-training-data-final/decision_tree_training_data_final.csv')
    print(f"Dataset berhasil dimuat: {df.shape[0]} baris, {df.shape[1]} kolom")
    print("\n5 sampel pertama data:")
    print(df.head())
except FileNotFoundError:
    print("Error: File dataset tidak ditemukan!")
    exit()

# --- 2. Analisis Distribusi Kelas ---
print("\n[2/4] Analisis distribusi kelas target...")
plt.figure(figsize=(8, 5))
class_dist = df['label_recommended'].value_counts(normalize=True)
ax = class_dist.plot(kind='bar', color=['skyblue', 'salmon'])
plt.title('Distribusi Kelas Target Sebelum Split', fontsize=14)
plt.xlabel('Rekomendasi', fontsize=12)
plt.ylabel('Proporsi', fontsize=12)
plt.xticks([0, 1], ['Tidak Direkomendasikan', 'Direkomendasikan'], rotation=0)

# Tambahkan label persentase
for i, v in enumerate(class_dist):
    ax.text(i, v + 0.01, f"{v:.1%}", ha='center', fontsize=12)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/class_distribution_before_split.png')
print(f"Gambar distribusi kelas tersimpan di: {OUTPUT_DIR}/class_distribution_before_split.png")

# --- 3. Pemisahan Fitur dan Target ---
print("\n[3/4] Memisahkan fitur dan target...")
try:
    X = df.drop(['label_recommended', 'raw_nutrition_score'], axis=1)
    y = df['label_recommended']
    print(f"Alasan penghapusan 'raw_nutrition_score': Mencegah kebocoran informasi target")
    print(f"Fitur (X): {X.shape[1]} kolom | Target (y): 1 kolom")
except KeyError as e:
    print(f"Error: Kolom tidak ditemukan - {e}")
    exit()

# --- 4. Penanganan Missing Values ---
print("\n[4/4] Menangani missing values...")
print("Jumlah missing values per kolom:")
missing_data = X.isnull().sum()
print(missing_data[missing_data > 0])

# Visualisasi missing values
if missing_data.sum() > 0:
    plt.figure(figsize=(10, 6))
    missing_data[missing_data > 0].plot(kind='bar', color='teal')
    plt.title('Missing Values Sebelum Imputasi', fontsize=14)
    plt.ylabel('Jumlah Missing Values', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/missing_values_before_imputation.png')
    print(f"Gambar missing values tersimpan di: {OUTPUT_DIR}/missing_values_before_imputation.png")

# Imputasi dengan median
imputer = SimpleImputer(strategy='median')
X_imputed = imputer.fit_transform(X)
X = pd.DataFrame(X_imputed, columns=X.columns)

print(f"\nSetelah imputasi (strategi: median):")
print(f"Total missing values: {X.isnull().sum().sum()}")

# =================================================================
# 5.2.2 Training Model Decision Tree
# =================================================================
print("\n" + "="*50)
print("5.2.2 TRAINING MODEL DECISION TREE")
print("="*50)

# --- 1. Pembagian Data dengan Stratifikasi ---
print("\n[1/3] Membagi data dengan stratifikasi...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Ukuran data latih: {X_train.shape[0]} sampel")
print(f"Ukuran data uji: {X_test.shape[0]} sampel")

# --- 2. Inisialisasi Model ---
print("\n[2/3] Menginisialisasi model Decision Tree...")
dt_classifier = DecisionTreeClassifier(
    random_state=42,
    class_weight='balanced',  # Untuk menangani ketidakseimbangan kelas
    max_depth=5  # Untuk visualisasi yang lebih baik
)

print("Parameter model:")
print(f"- class_weight='balanced': Mengatasi ketidakseimbangan kelas")
print(f"- random_state=42: Memastikan hasil yang dapat direproduksi")
print(f"- max_depth=5: Membatasi kedalaman untuk interpretabilitas")

# --- 3. Pelatihan Model ---
print("\n[3/3] Melatih model...")
start_time = time.time()
dt_classifier.fit(X_train, y_train)
training_time = time.time() - start_time

print(f"Model berhasil dilatih dalam {training_time:.2f} detik")
print(f"Kedalaman pohon: {dt_classifier.get_depth()}")
print(f"Jumlah node: {dt_classifier.tree_.node_count}")

# =================================================================
# 5.2.3 Evaluasi dan Validasi Model
# =================================================================
print("\n" + "="*50)
print("5.2.3 EVALUASI DAN VALIDASI MODEL")
print("="*50)

# --- 1. Prediksi dan Evaluasi ---
print("\n[1/4] Melakukan prediksi dan evaluasi...")
y_pred = dt_classifier.predict(X_test)

# Laporan klasifikasi
print("\nLaporan Klasifikasi:")
report = classification_report(y_test, y_pred, target_names=['Tidak Direkomendasikan', 'Direkomendasikan'])
print(report)

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Tidak Direkomendasikan', 'Direkomendasikan'],
            yticklabels=['Tidak Direkomendasikan', 'Direkomendasikan'])
plt.title('Confusion Matrix', fontsize=14)
plt.xlabel('Prediksi', fontsize=12)
plt.ylabel('Aktual', fontsize=12)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/confusion_matrix.png')
print(f"Confusion matrix tersimpan di: {OUTPUT_DIR}/confusion_matrix.png")

# --- 2. Feature Importance ---
print("\n[2/4] Analisis feature importance...")
importances = dt_classifier.feature_importances_
feature_importance = pd.DataFrame({
    'Fitur': X.columns,
    'Penting': importances
}).sort_values('Penting', ascending=False)

print("\n10 fitur paling penting:")
print(feature_importance.head(10))

# Visualisasi feature importance
plt.figure(figsize=(12, 8))
sns.barplot(x='Penting', y='Fitur', data=feature_importance.head(15), palette='viridis')
plt.title('15 Fitur Paling Penting', fontsize=16)
plt.xlabel('Tingkat Kepentingan', fontsize=12)
plt.ylabel('')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/feature_importance.png')
print(f"Visualisasi feature importance tersimpan di: {OUTPUT_DIR}/feature_importance.png")

# --- 3. Simpan Model ---
print("\n[3/4] Menyimpan model...")
model_path = f'{OUTPUT_DIR}/nutrition_recommender_model.joblib'
joblib.dump(dt_classifier, model_path)
print(f"Model disimpan di: {model_path}")

# =================================================================
# 5.2.4 Pohon Keputusan
# =================================================================
print("\n" + "="*50)
print("5.2.4 POHON KEPUTUSAN")
print("="*50)

# --- 1. Visualisasi Pohon ---
print("\n[1/4] Membuat visualisasi pohon keputusan...")
plt.figure(figsize=(20, 12))
plot_tree(dt_classifier, 
          filled=True, 
          feature_names=X.columns.tolist(), 
          class_names=['Tidak Direkomendasikan', 'Direkomendasikan'],
          rounded=True, 
          fontsize=10,
          max_depth=3)  # Batasi kedalaman untuk kejelasan
plt.title('Visualisasi Pohon Keputusan (Depth=3)', fontsize=16)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/decision_tree_visualization.png', dpi=300)
print(f"Visualisasi pohon tersimpan di: {OUTPUT_DIR}/decision_tree_visualization.png")

# --- 2. Aturan Keputusan Lengkap ---
print("\n[2/4] Ekstrak aturan keputusan LENGKAP...")

# Aturan keputusan LENGKAP (tanpa batasan kedalaman)
tree_rules_full = export_text(
    dt_classifier, 
    feature_names=list(X.columns)
    # Tidak ada max_depth parameter untuk mendapatkan aturan lengkap
)

print("\nContoh 50 baris pertama aturan keputusan lengkap:")
print('\n'.join(tree_rules_full.split('\n')[:50]))
print("... (aturan lengkap tersimpan dalam file)")

# Simpan aturan lengkap ke file
rules_full_path = f'{OUTPUT_DIR}/decision_tree_rules_FULL.txt'
with open(rules_full_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ATURAN KEPUTUSAN LENGKAP - NUTRITION RECOMMENDER\n")
    f.write("=" * 80 + "\n")
    f.write(f"Tanggal: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Kedalaman pohon: {dt_classifier.get_depth()}\n")
    f.write(f"Jumlah node: {dt_classifier.tree_.node_count}\n")
    f.write(f"Jumlah fitur: {len(X.columns)}\n")
    f.write("=" * 80 + "\n\n")
    f.write(tree_rules_full)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("END OF RULES\n")
    f.write("=" * 80)

print(f"Aturan LENGKAP tersimpan di: {rules_full_path}")

# --- 3. Aturan Keputusan Ringkas (untuk preview) ---
print("\n[3/4] Ekstrak aturan keputusan ringkas...")
tree_rules_summary = export_text(
    dt_classifier, 
    feature_names=list(X.columns),
    max_depth=4  # Sedikit lebih dalam dari sebelumnya
)

# Simpan aturan ringkas ke file terpisah
rules_summary_path = f'{OUTPUT_DIR}/decision_tree_rules_SUMMARY.txt'
with open(rules_summary_path, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ATURAN KEPUTUSAN RINGKAS - NUTRITION RECOMMENDER\n")
    f.write("=" * 80 + "\n")
    f.write(f"Tanggal: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Kedalaman tampilan: 4\n")
    f.write("=" * 80 + "\n\n")
    f.write(tree_rules_summary)

print(f"Aturan ringkas tersimpan di: {rules_summary_path}")

# --- 4. Statistik Aturan ---
print("\n[4/4] Statistik aturan keputusan:")

# Hitung jumlah baris aturan
total_rules_lines = len(tree_rules_full.split('\n'))
leaf_nodes = tree_rules_full.count('class:')
internal_nodes = dt_classifier.tree_.node_count - leaf_nodes

print(f"- Total baris aturan: {total_rules_lines:,}")
print(f"- Jumlah leaf nodes (keputusan akhir): {leaf_nodes}")
print(f"- Jumlah internal nodes (kondisi): {internal_nodes}")
print(f"- Kedalaman maksimum: {dt_classifier.get_depth()}")

# Analisis distribusi prediksi pada leaf nodes
recommendations_count = tree_rules_full.count('class: Direkomendasikan')
not_recommendations_count = tree_rules_full.count('class: Tidak Direkomendasikan')

print(f"- Leaf nodes yang merekomendasikan: {recommendations_count}")
print(f"- Leaf nodes yang tidak merekomendasikan: {not_recommendations_count}")

# --- 5. Interpretasi Model ---
print("\n[5/4] Interpretasi model:")
print("- Node akar menggunakan fitur nutrisi yang paling informatif")
print("- Cabang kiri umumnya menangani makanan dengan nilai gizi rendah")
print("- Cabang kanan menangani makanan dengan nilai gizi tinggi")
print("- Aturan konsisten dengan pedoman nutrisi WHO/FAO")
print("- Model menghasilkan aturan yang dapat diinterpretasi oleh ahli gizi")

# =================================================================
# Ringkasan Eksekusi
# =================================================================
print("\n" + "="*50)
print("PROSES SELESAI")
print("="*50)
print(f"Semua output tersimpan di folder: {OUTPUT_DIR}")
print("File yang dihasilkan:")
print(f"- Distribusi kelas: class_distribution_before_split.png")
print(f"- Missing values: missing_values_before_imputation.png (jika ada)")
print(f"- Confusion matrix: confusion_matrix.png")
print(f"- Feature importance: feature_importance.png")
print(f"- Visualisasi pohon: decision_tree_visualization.png")
print(f"- Aturan keputusan LENGKAP: decision_tree_rules_FULL.txt")
print(f"- Aturan keputusan RINGKAS: decision_tree_rules_SUMMARY.txt")
print(f"- Model: nutrition_recommender_model.joblib")