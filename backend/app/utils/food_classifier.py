from app import db
from app.models.food import Food # Pastikan Food sudah diupdate sesuai langkah sebelumnya
import click

class FoodClassifier:
    def __init__(self):
        # Keywords for vegetarian classification
        self.vegetarian_keywords = [
            'sayur', 'sayuran', 'vegetarian', 'vegan', 'tahu', 'tempe', 'tauhu', # tahu alias
            'kacang', # Perlu hati-hati karena bisa ambigu dengan alergen
            'buah', 'salad', 'lalapan', 'daun', 'jamur', 'cendawan', # jamur alias
            'umbi', 'singkong', 'kentang', 'talas', 'ubi', 'keladi', # ubi alias
            'jagung', 'gandum', 'beras', 'kembang', 'bunga', 'kecipir',
            'kangkung', 'bayam', 'ketela', 'tauge', 'toge', # tauge alias
            'melinjo', 'mlinjo', # melinjo alias
            'buncis', 'tomat', 'wortel', 'terong', 'terung', # terong alias
            'ketimun', 'timun',
            'gadung', 'ganyong', 'gembili', 'irut', 'uwi', 'kimpul', 
            'cantel', 'sorgum', # cantel alias
            'sagu', 'maizena', 'arrowroot', 'tepung beras', 'tepung tapioka', 'tepung terigu', 'pati', 'tepung', 
            'oyek', 'gaplek', 
            'temu', 'kunyit', 'kunir', # kunyit alias
            'jahe', 'laos', 'kencur', 'lengkuas', 
            'labu', 'waluh', 
            'pare', 'peria', # pare alias
            'oyong', 'gambas', 
            'selada', 
            'cesim', 'sawi', 'caisim', # sawi alias
            'genjer', 'kenikir',
            'beluntas',
            'kemangi', 
            'kelor', 
            'rebung', 
            'lobak', 
            'asparagus',
            'bawang merah', 'bawang putih', 'bawang bombay', 'daun bawang', 'loncang', 'kucai',
            'nangka muda', 'gori', 
            'jantung pisang', 'kembang turi', 'bunga pepaya',
            'bihun', 'soun', 'misoa', 'sohun', # soun alias
            'papeda', 
            'getuk', 'tiwul', 'cenil', 'ondal-andil', 'ciwel', 'blendung', 'brontol', 'growol', 'gatot',
            'cincau', 
            'kolang kaling', 'kolang-kaling',
            'rumput laut', # Vegetarian, tapi bisa jadi alergen seafood
            'pepaya muda', 
            'kulit melinjo', 'daun melinjo', 'daun singkong', 'daun ubi', 'daun pepaya', 'daun talas', 'daun katuk',
            'asam jawa', 'belimbing wuluh', 
            'mentimun', 'sukini', 'zucchini', 'kubis', 'kol', # kubis alias
            'brokoli', 'kembang kol', 'bunga kol', # kembang kol alias
            'kailan',
            'seledri', 'peterseli', 'daun ketumbar', 'mint', 'dill',
            'paprika', 'cabai', 'cabe', 'lombok', # cabai alias
            'wijen', 'biji labu', 'biji bunga matahari', 'chia seed', 'flax seed' # flaxseed
        ]

        # Keywords for non-halal classification
        self.non_halal_keywords = [
            'babi', 'babi hutan', 'bacon', 'ham', 'pork', 'swine', 'lard', 'gelatin babi', 'samsu',
            'arak', 'alkohol', 'wine', 'beer', 'spirit', 'tuak', 'sake', 'rhum', 'ciu', 'brem', 'mirin', 'cognac', 'vodka', 'whiskey', 'miras',
            'lapcheong', 'char siu', 'bak kut teh', 'chasiu', 'saucisson', 'ngohiong', 'baikut',
            'babi daging', 'babi ginjal', 'babi hati', 'babi hutan masak',
            'empal goreng (babi)', 'saren (dideh babi)', 'sekba', 'babi panggang', 'babi rica', 'babi kecap', 'babi hong',
            'bir', 'anggur (minuman)', 'arak masak', 'angciu' # Specify 'anggur' as beverage
        ]

        # Keywords for allergens
        self.dairy_keywords = [
            'susu', 'keju', 'yogurt', 'yoghurt', 'krim', 'mentega', 'dairy', 'milk', 'ghee',
            'cheese', 'butter', 'cream', 'margarin', 'whey', 'buttermilk', 'dadih', 'custard', 'kasein', 'laktosa',
            'kefir', 'ice cream', 'es krim', 'gelato', 'sour cream', 'condensed milk', 'evaporated milk',
            'tepung susu', 'susu bubuk', 'susu kental', 'susu formula', 'skm',
            'milo', 'ovaltine', 'dancow', 'sgm', 'lactogen', 'bebelac', 'chilmil', 'enfamil', 'frisian flag', 'indomilk', # Common milk-based products/brands
            'breastmilk', 'asi'
        ]

        self.nuts_keywords = [
            'kacang', 'almond', 'kenari', 'hazelnut', 'kacang tanah', 'peanut', 'kacang mede', # mede alias
            'kacang mete', 'cashew', 'kacang almond', 'walnut', 'pecan', 'pistachio', 'macadamia', 'pistacio',
            # 'kacang merah', 'kacang hijau', 'kacang bogor', 'kacang kedelai', # Ini lebih ke legumes, bisa dipisah jika perlu detail
            'kacang gude', 'kemiri', 'candlenut', 'jawawut', 'biji jambu mete',
            'kwaci', 'kuaci', 
            'wijen', 'sesame', 
            'ketapang', 
            'biji bunga matahari', 'biji labu', 'biji chia', 'biji rami', 'flaxseed', 'sunflower seed', 'pumpkin seed',
            'gucang', 'sukro', 'kacang atom', 'kacang telur', 'nougat', 'selai kacang', 'peanut butter',
            'bumbu kacang', 'saus kacang', 'sambal kacang' # Saus/bumbu
        ]

        self.seafood_keywords = [
            'ikan', 'udang', 'cumi', 'cumi-cumi', 'kerang', 'kepiting', 'lobster', 'tiram', 'scallop', 'simping', 'remis', 'kerang dara', 'kerang hijau', 'keong',
            'seafood', 'cakalang', 'tuna', 'salmon', 'tongkol', 'kakap', 'bawal', 'mujair', 'mujaer',
            'pindang', 'rajungan', 'belut', 'unagi', 'sidat', # sidat alias belut
            'cue', 'gabus', 'lemuru', 'teri', 'rebon', 'ebi', 'sepat', 'tenggiri', 'mackerel',
            'dendeng ikan', 'bakasang', 'bekasam', 'kembung', 'patin', 'bandeng', 'gindara', 'baronang', 'cod', 'haddock', 'halibut',
            'pepes ikan', 'ikan bakar', 'ikan goreng', 'ikan asin', 'ikan asap', 'sarden', 'sardines', 'surimi',
            'ikan mas', 'ikan lele', 'ikan nila', 'ikan gurame', 'gurami',
            'gurita', 'octopus', 'sotong', 'catfish', 
            'hiu', 'shark', 'pari', 'stingray', 
            'yuyu', 
            'tude', 
            'siomay', 'somay', 'batagor', # Seringkali seafood based
            'pempek', 'otak-otak', 'tekwan', 'mpek-mpek', 'model', # Fishcakes
            'terasi', 'petis', 
            'undur-undur', 
            'rumput laut', 'nori', 'wakame', 'kombu', # Seaweed (bisa jadi alergen)
            'telur ikan', 'fish roe', 'caviar', 'ikura', 'tobiko', 'mentaiko'
        ]

        self.egg_keywords = [
            'telur', 'omelette', 'egg', 'telor', 
            'kuning telur', 'putih telur', 'telur ceplok', 'telur dadar', 'telur mata sapi', 'scrambled egg', 'poached egg',
            'martabak telur', 'rendang telur', 'telur asin', 'telur balado', 'telur pindang', 'orak arik telur', 'telur gabus',
            'mayones', 'mayonnaise', 'aioli',
            'kue sus', 'cake', 'bolu', 'bika ambon', 'nastar', 'kue lapis', 'kue', 'biskuit', 'cookies', 'muffin', 'brownies', 'cupcake', 'pastry', 'wafer',
            'frittata', 'quiche', 'meringue', 'creme brulee', 'custard', 'pancake', 'wafel', 'crepe', 'semprong', 'lekker',
            'pasta telur', 'bihun telur', 'mie telur' # Noodles made with egg
        ]

        self.soy_keywords = [
            'kedelai', 'kedele', 'tahu', 'tempe', 'soy', 'soya', 'susu kedelai', 'soy milk', 'susu soya',
            'soy sauce', 'kecap', 'tauco', 'miso', 'edamame', 'oncom', 'tauge kedelai',
            'tempe bungkil', 'bungkil kedelai', 'kembang tahu', 'yuba', 'fucuk', 'tahwa', 'kembang tahu',
            'protein kedelai', 'lesitin kedelai', 'minyak kedelai', 'tepung kedelai', 'tvp',
            'natto', 'tempeh', 'doenjang', 'gochujang',
            'susu sgm' # Beberapa varian SGM berbasis soya
        ]

        # Keywords that strongly indicate a non-vegetarian item for internal logic.
        # Seafood (kecuali rumput laut) sudah termasuk di sini.
        self.strict_non_veg_identifiers = [
            'daging', 'ayam', 'sapi', 'kambing', 'kerbau', 'domba', 'itik', 'bebek', 'burung', 'puyuh', 'kelinci',
            'biawak', 'kelelawar', 'tupai', 'kodok', 'ular', # 'belut' dikeluarkan karena bisa ambigu, akan ditangani seafood
            'jeroan', 'ati', 'ampela', 'limpa', 'babat', 'usus', 'paru', 'kikil', 'sumsum', 'rempelo', 'jantung', 'otak', 'gajih', 'lemak hewan', 'kulit ayam', 'kulit sapi', 'dideh', 'marus',
            'kaldu ayam', 'kaldu sapi', 'kaldu daging', 'beef broth', 'chicken stock', 
            'bakso daging', 'sosis daging', 'kornet sapi', 'abon sapi', 'rendang daging', 'gulai ayam', 'semur daging', 'sate ayam', 'bistik', 'steak',
            'bacon', 'ham', 'pork', 'swine', 'babi' # Sudah ada di non_halal tapi penting untuk non-veg
        ] + [sf for sf in self.seafood_keywords if sf not in ['rumput laut', 'nori', 'wakame', 'kombu', 'terasi', 'petis']] # Terasi/petis bisa jadi hanya bumbu

    def classify_foods(self):
        """Classify all Indonesian foods based on dietary preferences and allergies"""
        foods = Food.query.all()
        total = len(foods)
        classified = 0
        click.echo(f"Starting classification for {total} foods...")

        for food_idx, food in enumerate(foods):
            name_lower = food.name.lower()

            # --- Vegetarian Classification ---
            is_vegetarian_flag = True 
            if any(keyword in name_lower for keyword in self.strict_non_veg_identifiers):
                is_vegetarian_flag = False
                
                # Exception for known plant-based alternatives
                if (("sate" in name_lower and any(veg_kw in name_lower for veg_kw in ['jamur', 'tempe', 'tahu', 'sayur', 'buah', 'kikil jamur'])) or
                    ("rendang" in name_lower and any(veg_kw in name_lower for veg_kw in ['nangka', 'jamur', 'daun singkong', 'kentang', 'jengkol', 'pakis']) and not any(meat_kw in name_lower for meat_kw in ['daging', 'sapi', 'ayam'])) or
                    ("bakso" in name_lower and any(veg_kw in name_lower for veg_kw in ['aci', 'sayur', 'jamur', 'tahu', 'tepung', 'cilok', 'kanji']) and not any(meat_kw in name_lower for meat_kw in ['daging', 'sapi', 'ikan', 'ayam'])) or
                    ("abon" in name_lower and any(veg_kw in name_lower for veg_kw in ['jamur', 'pepaya', 'nangka', 'jantung pisang', 'tempe', 'tahu'])) or
                    ("sosis" in name_lower and any(veg_kw in name_lower for veg_kw in ['tempe', 'jamur', 'kedelai', 'sayur', 'tahu'])) or
                    ("nugget" in name_lower and any(veg_kw in name_lower for veg_kw in ['tempe', 'tahu', 'jamur', 'sayur'])) or
                    ("burger" in name_lower and any(veg_kw in name_lower for veg_kw in ['tempe', 'jamur', 'sayur', 'tahu', 'kentang'])) or
                    ("dendeng" in name_lower and any(veg_kw in name_lower for veg_kw in ['jamur', 'daun singkong', 'tempe', 'kimpul', 'gadung'])) or
                    ("gulai" in name_lower and any(veg_kw in name_lower for veg_kw in ['nangka', 'jamur', 'tahu', 'tempe', 'pakis', 'daun singkong', 'sayur', 'telur']) and not any(meat_kw in name_lower for meat_kw in ['ikan', 'ayam', 'daging', 'kambing'])) or # gulai telur bisa vegetarian
                    ("semur" in name_lower and any(veg_kw in name_lower for veg_kw in ['tahu', 'tempe', 'jengkol', 'kentang', 'terong', 'telur']) and not any(meat_kw in name_lower for meat_kw in ['daging', 'ayam', 'sapi'])) or # semur telur bisa vegetarian
                    ("opor" in name_lower and any(veg_kw in name_lower for veg_kw in ['tahu', 'tempe', 'nangka', 'telur', 'labu']) and not any(meat_kw in name_lower for meat_kw in ['ayam', 'daging'])) or # opor telur bisa vegetarian
                    ("kari" in name_lower and any(veg_kw in name_lower for veg_kw in ['sayuran', 'tahu', 'tempe', 'kentang', 'nangka', 'telur']) and not any(meat_kw in name_lower for meat_kw in ['ayam', 'daging', 'ikan'])) or # kari telur bisa vegetarian
                    ("bistik" in name_lower and any(veg_kw in name_lower for veg_kw in ['tempe', 'tahu', 'jamur', 'kentang']))):
                    is_vegetarian_flag = True
            
            # Jika tidak ada identifier non-veg yang ketat, DAN mengandung keyword vegetarian, maka vegetarian
            elif any(keyword in name_lower for keyword in self.vegetarian_keywords):
                 is_vegetarian_flag = True
            
            # Jika tidak ada identifier non-veg DAN tidak ada keyword vegetarian (misal: air putih, gula)
            # defaultnya vegetarian karena tidak mengandung produk hewani dari list kita.
            # Ini sudah ditangani oleh inisialisasi is_vegetarian_flag = True dan tidak ada strict_non_veg

            food.is_vegetarian = is_vegetarian_flag

            # --- Halal Classification ---
            food.is_halal = not any(
                keyword in name_lower for keyword in self.non_halal_keywords)

            # --- Allergen Classification ---
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
            if classified % 100 == 0 or classified == total:
                click.echo(f"Classified {classified}/{total} foods. Last: {food.name} -> Veg: {food.is_vegetarian}, Halal: {food.is_halal}, Nuts: {food.contains_nuts}, Seafood: {food.contains_seafood}, Dairy: {food.contains_dairy}, Eggs: {food.contains_eggs}, Soy: {food.contains_soy}")

        db.session.commit()
        click.echo(f"Successfully classified {classified} foods.")

