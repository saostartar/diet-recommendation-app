from app import db
from app.models.food import Food


class FoodClassifier:
    def __init__(self):
        # Keywords for vegetarian classification
        self.vegetarian_keywords = [
            'sayur', 'sayuran', 'vegetarian', 'vegan', 'tahu', 'tempe',
            'kacang', 'buah', 'salad', 'lalapan', 'daun', 'jamur', 'umbi', 'singkong', 'kentang', 'talas',
            'jagung', 'gandum', 'beras', 'kembang', 'bunga', 'kecipir',
            'kangkung', 'bayam', 'ubi', 'ketela', 'tauge', 'melinjo',
            'buncis', 'tomat', 'wortel', 'terong', 'ketimun'
        ]

        # Keywords for non-halal classification
        self.non_halal_keywords = [
            'babi', 'babi hutan', 'bacon', 'ham', 'pork', 'arak', 'alkohol',
            'wine', 'beer', 'spirit', 'tuak', 'babi daging', 'babi ginjal', 'babi hati', 'babi hutan masak',
            'empal goreng (babi)', 'bir', 'anggur'
        ]

        # Keywords for allergens
        self.dairy_keywords = [
            'susu', 'keju', 'yogurt', 'krim', 'mentega', 'dairy', 'milk',
            'cheese', 'butter', 'cream', 'margarin', 'whey', 'buttermilk', 'dadih', 'custard',
            'keju kacang tanah', 'corned beef'
        ]

        self.nuts_keywords = [
            'kacang', 'almond', 'kenari', 'hazelnut', 'kacang tanah',
            'kacang mete', 'kacang almond', 'walnut', 'pecan', 'kacang merah', 'kacang hijau', 'kacang bogor', 'kacang kedelai',
            'kacang gude', 'kemiri', 'jawawut', 'biji jambu mete',
            'kwaci'
        ]

        self.seafood_keywords = [
            'ikan', 'udang', 'cumi', 'kerang', 'kepiting', 'lobster',
            'seafood', 'cakalang', 'tuna', 'salmon', 'tongkol', 'kakap',
            'laut', 'gurita', 'sotong', 'bandeng', 'bawal', 'mujair', 'pindang', 'asin', 'rajungan',
            'belut', 'cue', 'gabus', 'lemuru', 'teri', 'sepat', 'tenggiri',
            'dendeng ikan', 'bakasang', 'bekasam', 'cakalang', 'kembung',
            'pepes', 'ikan bakar', 'ikan goreng', 'ikan asin', 'ikan teri',
            'ikan mas', 'ikan lele', 'ikan nila', 'ikan mujair', 'ikan patin', 'goreng'
        ]

        self.egg_keywords = [
            'telur', 'omelette', 'egg', 'kuning telur', 'putih telur',     'dadar', 'martabak telur', 'rendang telur', 'telur asin',
            'mayones', 'kue sus', 'cake'
        ]

        self.soy_keywords = [
            'kedelai', 'tahu', 'tempe', 'soy', 'soya', 'susu kedelai',
            'soy sauce', 'kecap',  'tauji', 'tauco', 'kecap manis', 'kecap asin', 'oncom',
            'tempe bungkil', 'bungkil kedelai'
        ]

    def classify_foods(self):
        """Classify all Indonesian foods based on dietary preferences and allergies"""
        foods = Food.query.all()
        total = len(foods)
        classified = 0

        for food in foods:
            name_lower = food.name.lower()

            # Classify vegetarian
            food.is_vegetarian = (
                any(keyword in name_lower for keyword in self.vegetarian_keywords) or
                not any(keyword in name_lower for keyword in self.seafood_keywords +
                        ['daging', 'ayam', 'sapi'])
            )

            # Classify halal
            food.is_halal = not any(
                keyword in name_lower for keyword in self.non_halal_keywords)

            # Classify allergens
            food.contains_nuts = any(
                keyword in name_lower for keyword in self.nuts_keywords)
            food.contains_seafood = any(
                keyword in name_lower for keyword in self.seafood_keywords)
            food.contains_dairy = any(
                keyword in name_lower for keyword in self.dairy_keywords)
            food.contains_eggs = any(
                keyword in name_lower for keyword in self.egg_keywords)
            food.contains_soy = any(
                keyword in name_lower for keyword in self.soy_keywords)

            classified += 1
            if classified % 100 == 0:
                print(f"Classified {classified}/{total} foods")

        db.session.commit()
        print(f"Successfully classified {classified} foods")
