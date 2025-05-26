import joblib
import os
import pandas as pd
import pickle
import numpy as np

# Konstanta konversi kJ ke kkal
KJ_TO_KCAL = 1 / 4.184

class VersionCompatibleLoader:
    @staticmethod
    def load(file_path):
        """Memuat model scikit-learn dengan penanganan kompatibilitas versi."""
        try:
            return joblib.load(file_path)
        except (ValueError, KeyError, pickle.UnpicklingError) as e:
            if "node array" in str(e) and "incompatible dtype" in str(e):
                print(f"Menangani kompatibilitas versi untuk {file_path}")
                
                class CustomUnpickler(pickle.Unpickler):
                    def find_class(self, module, name):
                        return super().find_class(module, name)

                with open(file_path, 'rb') as f:
                    unpickler = CustomUnpickler(f)
                    model = unpickler.load()

                if hasattr(model, 'tree_') or (hasattr(model, 'estimators_') and len(model.estimators_) > 0):
                    if hasattr(model, 'estimators_'):
                        for i, estimator in enumerate(model.estimators_):
                            if hasattr(estimator, 'tree_'):
                                tree = estimator.tree_
                                if not hasattr(tree, 'missing_go_to_left'):
                                    tree.missing_go_to_left = np.zeros(tree.node_count, dtype=np.bool_)
                    elif hasattr(model, 'tree_'):
                        tree = model.tree_
                        if not hasattr(tree, 'missing_go_to_left'):
                            tree.missing_go_to_left = np.zeros(tree.node_count, dtype=np.bool_)
                return model
            else:
                if 'meal_type_classifier.joblib' in file_path: # Hanya untuk meal_type
                    print(f"Error memuat model {file_path}: {e}. Akan mengandalkan heuristik.")
                    return None 
                else:
                    raise 

class FoodMLClassifier:
    def __init__(self):
        # Path ke direktori tempat model disimpan (sesuai skrip pelatihan)
        model_dir = 'model_output' # Pastikan ini konsisten dengan tempat Anda menyimpan model
        
        # Path lengkap ke file model dan encoder
        meal_type_model_path = os.path.join(model_dir, 'meal_type_classifier.joblib')
        meal_type_encoder_path = os.path.join(model_dir, 'meal_type_label_encoder.joblib')

        self.meal_type_classifier = None
        self.meal_type_encoder = None

        if os.path.exists(meal_type_model_path) and os.path.exists(meal_type_encoder_path):
            try:
                self.meal_type_classifier = VersionCompatibleLoader.load(meal_type_model_path)
                self.meal_type_encoder = joblib.load(meal_type_encoder_path)
                if self.meal_type_classifier is None:
                    print(f"Peringatan: Model meal_type_classifier tidak dapat dimuat dengan benar dari {meal_type_model_path}. Menggunakan heuristik.")
                else:
                    print(f"Berhasil memuat model klasifikasi jenis makanan dari {meal_type_model_path}.")
            except Exception as e:
                print(f"Error memuat model jenis makanan (meal type) dari {model_dir}: {e}. Menggunakan heuristik.")
        else:
            print(f"Peringatan: File model atau encoder jenis makanan tidak ditemukan di direktori '{model_dir}'. Akan menggunakan heuristik.")
        
        # Keyword untuk klasifikasi heuristik (jika model ML gagal atau tidak ada)
        self.breakfast_keywords = [
            'telur', 'roti', 'bubur', 'oatmeal', 'sereal', 'granola', 'susu', 'yogurt', 
            'pancake', 'wafel', 'kopi', 'teh', 'lontong', 'nasi uduk', 'nasi kuning', 
            'energen', 'havermout', 'muesli', 'sandwich', 'croissant', 'martabak manis',
            'soto', 'mie instan'
        ]
        self.lunch_dinner_keywords = [
            'nasi', 'mie', 'bihun', 'pasta', 'sup', 'soto', 'gulai', 'kari', 'bakso', 
            'sayur', 'tumis', 'ayam', 'daging', 'ikan', 'udang', 'tahu', 'tempe', 
            'goreng', 'bakar', 'pepes', 'rendang', 'opor', 'semur', 'capcay', 'lodeh',
            'steak', 'burger', 'pizza', 'rawon', 'gudeg', 'pempek', 'sate', 'geprek',
            'penyet', 'balado', 'rica-rica', 'kwetiau', 'iga', 'buntut'
        ]
        self.snack_keywords = [
            'kue', 'coklat', 'permen', 'biskuit', 'keripik', 'kerupuk', 'buah', 'jelly', 
            'wafer', 'cookies', 'puding', 'es', 'jus', 'risoles', 'gorengan', 'martabak', 
            'pisang goreng', 'bakwan', 'onde-onde', 'klepon', 'lemper', 'lumpia', 'bolu',
            'brownie', 'batagor', 'siomay', 'seblak', 'cilok', 'cireng', 'cimol', 'kebab',
            'popcorn', 'kacang', 'yogurt buah', 'nastar', 'pastel', 'semprong', 'getuk', 'cenil'
        ]
            
    def predict_meal_type(self, food_name, calories_kj, protein_g, fat_g, carbs_g):
        """
        Memprediksi jenis makanan (Sarapan, Makan Siang, Makan Malam, Cemilan).
        Input adalah nilai nutrisi per porsi dari database (Food model).
        """
        calories_kcal = float(calories_kj if calories_kj is not None else 0) * KJ_TO_KCAL
        protein_g_val = float(protein_g if protein_g is not None else 0)
        fat_g_val = float(fat_g if fat_g is not None else 0)
        carbs_g_val = float(carbs_g if carbs_g is not None else 0)
        
        total_calories_for_ratio = max(1, calories_kcal)
        protein_ratio = (protein_g_val * 4 / total_calories_for_ratio) * 100 if total_calories_for_ratio > 0 else 0
        fat_ratio = (fat_g_val * 9 / total_calories_for_ratio) * 100 if total_calories_for_ratio > 0 else 0
        carb_ratio = (carbs_g_val * 4 / total_calories_for_ratio) * 100 if total_calories_for_ratio > 0 else 0
        
        name_lower = str(food_name).lower()
        is_breakfast_keyword = int(any(kw in name_lower for kw in self.breakfast_keywords))
        is_lunch_dinner_keyword = int(any(kw in name_lower for kw in self.lunch_dinner_keywords))
        is_snack_keyword = int(any(kw in name_lower for kw in self.snack_keywords))
        
        # DataFrame fitur harus SAMA PERSIS dengan yang digunakan saat pelatihan
        features_df = pd.DataFrame({
            'calories': [calories_kcal],
            'protein_g': [protein_g_val], # Ditambahkan sesuai output pelatihan
            'fat_g': [fat_g_val],         # Ditambahkan sesuai output pelatihan
            'carbs_g': [carbs_g_val],       # Ditambahkan sesuai output pelatihan
            'protein_ratio': [protein_ratio], 
            'fat_ratio': [fat_ratio],
            'carb_ratio': [carb_ratio],
            'is_breakfast_keyword': [is_breakfast_keyword],
            'is_lunch_dinner_keyword': [is_lunch_dinner_keyword],
            'is_snack_keyword': [is_snack_keyword]
        })
        
        try:
            if self.meal_type_classifier and self.meal_type_encoder:
                prediction = self.meal_type_classifier.predict(features_df)
                return self.meal_type_encoder.inverse_transform(prediction)[0]
            else:
                # print("Model meal_type tidak tersedia atau gagal dimuat, menggunakan heuristik.")
                return self._predict_meal_type_heuristic(food_name, calories_kcal, protein_g_val, fat_g_val, carbs_g_val)
        except Exception as e:
            print(f"Error saat prediksi jenis makanan dengan model: {e}. Menggunakan heuristik.")
            return self._predict_meal_type_heuristic(food_name, calories_kcal, protein_g_val, fat_g_val, carbs_g_val)
            
    def _predict_meal_type_heuristic(self, food_name, calories_kcal, protein_g, fat_g, carbs_g):
        """Klasifikasi jenis makanan berbasis heuristik jika model ML gagal."""
        name_lower = str(food_name).lower()

        if any(kw in name_lower for kw in self.breakfast_keywords):
            if calories_kcal < 500 and calories_kcal > 50: # Batas kalori sarapan, >50 untuk hindari minuman/bumbu
                return 'Sarapan'
        
        if any(kw in name_lower for kw in self.snack_keywords):
            if calories_kcal < 350 and calories_kcal > 30: # Batas kalori cemilan
                 # Cek apakah ini martabak telur (bukan snack)
                if "martabak" in name_lower and "telur" in name_lower:
                     return 'Makan Malam' if calories_kcal > 200 else 'Makan Siang' # Martabak telur bisa jadi makan berat
                return 'Cemilan'
        
        if calories_kcal < 50 and protein_g < 2 and carbs_g < 10 and fat_g < 2 : # Kriteria untuk minuman/bumbu ringan
             # Jika nama mengandung kata 'kopi', 'teh', 'jus', 'es' dan bukan es krim
            if any(kw in name_lower for kw in ['kopi', 'teh', 'jus', 'susu']) or ('es' in name_lower and not 'krim' in name_lower):
                return 'Cemilan' # Anggap sebagai minuman/cemilan ringan
        
        if calories_kcal < 200 and calories_kcal > 30: # Lebih ketat untuk cemilan non-keyword
            return 'Cemilan'
        elif calories_kcal >= 200 and calories_kcal < 450:
            if protein_g > 10 and carbs_g > 20: 
                # Jika ada keyword makan siang/malam, prioritaskan itu
                if any(kw in name_lower for kw in self.lunch_dinner_keywords):
                    return 'Makan Siang' 
                return 'Sarapan'
            else: # Kurang nutrisi untuk makanan utama, mungkin cemilan berat
                return 'Cemilan' 
        elif calories_kcal >= 450 and calories_kcal < 750:
            return 'Makan Siang' # Bisa juga makan malam ringan
        elif calories_kcal >= 750:
            return 'Makan Malam'
        
        # Default jika sangat ambigu, bisa juga 'Perlu Review' jika ada sistem seperti itu
        # Untuk sekarang, default ke kategori yang paling umum atau butuh kalori sedang
        return 'Makan Siang'
