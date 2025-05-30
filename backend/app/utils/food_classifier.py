from app import db
from app.models.food import Food
import click

class FoodClassifier:
    def __init__(self):
        # Keywords for vegetarian classification (kept for edge cases)
        self.vegetarian_keywords = [
            'sayur', 'sayuran', 'vegetarian', 'vegan', 'tahu', 'tempe', 'tauhu',
            'kacang', 'buah', 'salad', 'lalapan', 'daun', 'jamur', 'cendawan',
            'umbi', 'singkong', 'kentang', 'talas', 'ubi', 'keladi',
            'jagung', 'gandum', 'beras', 'kembang', 'bunga', 'kecipir',
            'kangkung', 'bayam', 'ketela', 'tauge', 'toge',
            'melinjo', 'mlinjo', 'buncis', 'tomat', 'wortel', 'terong', 'terung',
            'ketimun', 'timun', 'gadung', 'ganyong', 'gembili', 'irut', 'uwi', 'kimpul',
            'cantel', 'sorgum', 'sagu', 'maizena', 'arrowroot', 'tepung beras', 
            'tepung tapioka', 'tepung terigu', 'pati', 'tepung',
            'oyek', 'gaplek', 'temu', 'kunyit', 'kunir', 'jahe', 'laos', 'kencur', 
            'lengkuas', 'labu', 'waluh', 'pare', 'peria', 'oyong', 'gambas',
            'selada', 'cesim', 'sawi', 'caisim', 'genjer', 'kenikir', 'beluntas',
            'kemangi', 'kelor', 'rebung', 'lobak', 'asparagus',
            'bawang merah', 'bawang putih', 'bawang bombay', 'daun bawang', 'loncang', 'kucai',
            'nangka muda', 'gori', 'jantung pisang', 'kembang turi', 'bunga pepaya',
            'bihun', 'soun', 'misoa', 'sohun', 'papeda',
            'getuk', 'tiwul', 'cenil', 'ondal-andil', 'ciwel', 'blendung', 'brontol', 'growol', 'gatot',
            'cincau', 'kolang kaling', 'kolang-kaling', 'rumput laut', 'pepaya muda',
            'kulit melinjo', 'daun melinjo', 'daun singkong', 'daun ubi', 'daun pepaya', 
            'daun talas', 'daun katuk', 'asam jawa', 'belimbing wuluh',
            'mentimun', 'sukini', 'zucchini', 'kubis', 'kol', 'brokoli', 'kembang kol', 
            'bunga kol', 'kailan', 'seledri', 'peterseli', 'daun ketumbar', 'mint', 'dill',
            'paprika', 'cabai', 'cabe', 'lombok',
            'wijen', 'biji labu', 'biji bunga matahari', 'chia seed', 'flax seed'
        ]

        # Keywords for non-halal classification
        self.non_halal_keywords = [
            'babi', 'babi hutan', 'bacon', 'ham', 'pork', 'swine', 'lard', 'gelatin babi',
            'arak', 'alkohol', 'wine', 'beer', 'spirit', 'tuak', 'sake', 'rhum', 'ciu', 
            'brem', 'mirin', 'cognac', 'vodka', 'whiskey', 'miras',
            'lapcheong', 'char siu', 'bak kut teh', 'chasiu', 'saucisson', 'ngohiong', 'baikut',
            'babi daging', 'babi ginjal', 'babi hati', 'babi hutan masak',
            'empal goreng (babi)', 'saren (dideh babi)', 'sekba', 'babi panggang', 
            'babi rica', 'babi kecap', 'babi hong',
            'bir', 'anggur (minuman)', 'arak masak', 'angciu'
        ]

        # Allergen keywords
        self.dairy_keywords = [
            'susu', 'keju', 'yogurt', 'yoghurt', 'krim', 'mentega', 'dairy', 'milk', 'ghee',
            'cheese', 'butter', 'cream', 'margarin', 'whey', 'buttermilk', 'dadih', 'custard', 
            'kasein', 'laktosa', 'kefir', 'ice cream', 'es krim', 'gelato', 'sour cream',
            'condensed milk', 'evaporated milk', 'tepung susu', 'susu bubuk', 'susu kental', 
            'susu formula', 'skm', 'milo', 'ovaltine', 'dancow', 'sgm', 'lactogen', 'bebelac', 
            'chilmil', 'enfamil', 'frisian flag', 'indomilk', 'breastmilk', 'asi'
        ]

        self.nuts_keywords = [
            'kacang', 'almond', 'kenari', 'hazelnut', 'kacang tanah', 'peanut', 'kacang mede',
            'kacang mete', 'cashew', 'kacang almond', 'walnut', 'pecan', 'pistachio', 
            'macadamia', 'pistacio', 'kemiri', 'candlenut', 'jawawut', 'biji jambu mete',
            'kwaci', 'kuaci', 'wijen', 'sesame', 'ketapang', 'biji bunga matahari', 'biji labu', 
            'biji chia', 'biji rami', 'flaxseed', 'sunflower seed', 'pumpkin seed',
            'gucang', 'sukro', 'kacang atom', 'kacang telur', 'nougat', 'selai kacang', 
            'peanut butter', 'bumbu kacang', 'saus kacang', 'sambal kacang'
        ]

        self.seafood_keywords = [
            'ikan', 'udang', 'cumi', 'cumi-cumi', 'kerang', 'kepiting', 'lobster', 'tiram', 
            'scallop', 'simping', 'remis', 'kerang dara', 'kerang hijau', 'keong',
            'seafood', 'cakalang', 'tuna', 'salmon', 'tongkol', 'kakap', 'bawal', 'mujair', 'mujaer',
            'pindang', 'rajungan', 'belut', 'unagi', 'sidat', 'cue', 'gabus', 'lemuru', 'teri', 
            'rebon', 'ebi', 'sepat', 'tenggiri', 'mackerel', 'dendeng ikan', 'bakasang', 'bekasam',
            'kembung', 'patin', 'bandeng', 'gindara', 'baronang', 'cod', 'haddock', 'halibut',
            'pepes ikan', 'ikan bakar', 'ikan goreng', 'ikan asin', 'ikan asap', 'sarden', 
            'sardines', 'surimi', 'ikan mas', 'ikan lele', 'ikan nila', 'ikan gurame', 'gurami',
            'gurita', 'octopus', 'sotong', 'catfish', 'hiu', 'shark', 'pari', 'stingray',
            'yuyu', 'tude', 'siomay', 'somay', 'batagor', 'pempek', 'otak-otak', 'tekwan', 
            'mpek-mpek', 'model', 'terasi', 'petis', 'undur-undur',
            'rumput laut', 'nori', 'wakame', 'kombu', 'telur ikan', 'fish roe', 'caviar', 
            'ikura', 'tobiko', 'mentaiko'
        ]

        self.egg_keywords = [
            'telur', 'omelette', 'egg', 'telor', 'kuning telur', 'putih telur', 'telur ceplok',
            'telur dadar', 'telur mata sapi', 'scrambled egg', 'poached egg',
            'martabak telur', 'rendang telur', 'telur asin', 'telur balado', 'telur pindang',
            'orak arik telur', 'telur gabus', 'mayones', 'mayonnaise', 'aioli',
            'kue sus', 'cake', 'bolu', 'bika ambon', 'nastar', 'kue lapis', 'kue', 'biskuit',
            'cookies', 'muffin', 'brownies', 'cupcake', 'pastry', 'wafer',
            'frittata', 'quiche', 'meringue', 'creme brulee', 'custard', 'pancake', 'wafel',
            'crepe', 'semprong', 'lekker', 'pasta telur', 'bihun telur', 'mie telur'
        ]

        self.soy_keywords = [
            'kedelai', 'kedele', 'tahu', 'tempe', 'soy', 'soya', 'susu kedelai', 'soy milk', 'susu soya',
            'soy sauce', 'kecap', 'tauco', 'miso', 'edamame', 'oncom', 'tauge kedelai',
            'tempe bungkil', 'bungkil kedelai', 'kembang tahu', 'yuba', 'fucuk', 'tahwa',
            'protein kedelai', 'lesitin kedelai', 'minyak kedelai', 'tepung kedelai', 'tvp',
            'natto', 'tempeh', 'doenjang', 'gochujang', 'susu sgm'
        ]

        # Strong non-vegetarian identifiers
        self.strict_non_veg_identifiers = [
            'daging', 'ayam', 'sapi', 'kambing', 'kerbau', 'domba', 'itik', 'bebek', 'burung', 
            'puyuh', 'kelinci', 'biawak', 'kelelawar', 'tupai', 'kodok', 'ular',
            'jeroan', 'ati', 'ampela', 'limpa', 'babat', 'usus', 'paru', 'kikil', 'sumsum', 
            'rempelo', 'jantung', 'otak', 'gajih', 'lemak hewan', 'kulit ayam', 'kulit sapi', 
            'dideh', 'marus', 'kaldu ayam', 'kaldu sapi', 'kaldu daging', 'beef broth', 'chicken stock',
            'bakso daging', 'sosis daging', 'kornet sapi', 'abon sapi', 'rendang daging', 
            'gulai ayam', 'semur daging', 'sate ayam', 'bistik', 'steak',
            'bacon', 'ham', 'pork', 'swine', 'babi'
        ] + [sf for sf in self.seafood_keywords if sf not in ['rumput laut', 'nori', 'wakame', 'kombu']]

        # Food group mappings for classification
        self.vegetarian_food_groups = {
            'Sayur', 'Buah', 'Kacang', 'Serealia', 'Umbi'
        }
        
        self.non_vegetarian_food_groups = {
            'Daging', 'Ikan dsb'
        }
        
        self.dairy_food_groups = {
            'Susu'
        }
        
        self.egg_food_groups = {
            'Telur'
        }

    def classify_foods(self):
        """Classify all Indonesian foods based on dietary preferences and allergies"""
        foods = Food.query.all()
        total = len(foods)
        classified = 0
        click.echo(f"Starting classification for {total} foods...")

        for food_idx, food in enumerate(foods):
            name_lower = food.name.lower()
            food_group = food.food_group or ""
            food_status = food.food_status or ""
            
            # --- Vegetarian Classification ---
            # Start with food group classification (more reliable)
            is_vegetarian_flag = True
            
            # Check food group first
            if food_group in self.non_vegetarian_food_groups:
                is_vegetarian_flag = False
            elif food_group in self.vegetarian_food_groups:
                is_vegetarian_flag = True
            else:
                # Fall back to keyword-based classification for mixed or unknown groups
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
                        ("gulai" in name_lower and any(veg_kw in name_lower for veg_kw in ['nangka', 'jamur', 'tahu', 'tempe', 'pakis', 'daun singkong', 'sayur', 'telur']) and not any(meat_kw in name_lower for meat_kw in ['ikan', 'ayam', 'daging', 'kambing'])) or
                        ("semur" in name_lower and any(veg_kw in name_lower for veg_kw in ['tahu', 'tempe', 'jengkol', 'kentang', 'terong', 'telur']) and not any(meat_kw in name_lower for meat_kw in ['daging', 'ayam', 'sapi'])) or
                        ("opor" in name_lower and any(veg_kw in name_lower for veg_kw in ['tahu', 'tempe', 'nangka', 'telur', 'labu']) and not any(meat_kw in name_lower for meat_kw in ['ayam', 'daging'])) or
                        ("kari" in name_lower and any(veg_kw in name_lower for veg_kw in ['sayuran', 'tahu', 'tempe', 'kentang', 'nangka', 'telur']) and not any(meat_kw in name_lower for meat_kw in ['ayam', 'daging', 'ikan'])) or
                        ("bistik" in name_lower and any(veg_kw in name_lower for veg_kw in ['tempe', 'tahu', 'jamur', 'kentang']))):
                        is_vegetarian_flag = True
                
                # If no strict non-veg identifiers and contains vegetarian keywords
                elif any(keyword in name_lower for keyword in self.vegetarian_keywords):
                    is_vegetarian_flag = True

            food.is_vegetarian = is_vegetarian_flag

            # --- Halal Classification ---
            # Use food group and keyword-based classification
            is_halal_flag = True
            
            # Check for non-halal keywords
            if any(keyword in name_lower for keyword in self.non_halal_keywords):
                is_halal_flag = False
            
            food.is_halal = is_halal_flag

            # --- Allergen Classification ---
            # Dairy classification
            contains_dairy = False
            if food_group in self.dairy_food_groups:
                contains_dairy = True
            elif any(keyword in name_lower for keyword in self.dairy_keywords):
                contains_dairy = True
            food.contains_dairy = contains_dairy

            # Nuts classification
            contains_nuts = False
            if food_group == 'Kacang':
                # Be more specific for nuts vs legumes
                if any(nut_kw in name_lower for nut_kw in ['almond', 'kenari', 'hazelnut', 'mete', 'cashew', 'walnut', 'pecan', 'pistachio', 'macadamia', 'kemiri', 'wijen', 'sesame']):
                    contains_nuts = True
                elif 'kacang tanah' in name_lower or 'peanut' in name_lower:
                    contains_nuts = True
            elif any(keyword in name_lower for keyword in self.nuts_keywords):
                contains_nuts = True
            food.contains_nuts = contains_nuts

            # Seafood classification
            contains_seafood = False
            if food_group == 'Ikan dsb':
                contains_seafood = True
            elif any(keyword in name_lower for keyword in self.seafood_keywords):
                contains_seafood = True
            food.contains_seafood = contains_seafood

            # Egg classification
            contains_eggs = False
            if food_group in self.egg_food_groups:
                contains_eggs = True
            elif any(keyword in name_lower for keyword in self.egg_keywords):
                contains_eggs = True
            food.contains_eggs = contains_eggs

            # Soy classification
            contains_soy = False
            if any(keyword in name_lower for keyword in self.soy_keywords):
                contains_soy = True
            food.contains_soy = contains_soy

            classified += 1
            if classified % 100 == 0 or classified == total:
                click.echo(f"Classified {classified}/{total} foods. Last: {food.name} -> Veg: {food.is_vegetarian}, Halal: {food.is_halal}, Nuts: {food.contains_nuts}, Seafood: {food.contains_seafood}, Dairy: {food.contains_dairy}, Eggs: {food.contains_eggs}, Soy: {food.contains_soy}")

        db.session.commit()
        click.echo(f"Successfully classified {classified} foods.")

    def predict_food_status(self, name, caloric_value, protein, fat, carbohydrates, food_group=None, food_status=None):
        """Predict food classification for a single food item"""
        name_lower = name.lower()
        food_group = food_group or ""
        
        # Vegetarian classification
        is_vegetarian = True
        if food_group in self.non_vegetarian_food_groups:
            is_vegetarian = False
        elif food_group in self.vegetarian_food_groups:
            is_vegetarian = True
        else:
            if any(keyword in name_lower for keyword in self.strict_non_veg_identifiers):
                is_vegetarian = False
            elif any(keyword in name_lower for keyword in self.vegetarian_keywords):
                is_vegetarian = True

        # Halal classification
        is_halal = not any(keyword in name_lower for keyword in self.non_halal_keywords)

        # Allergen classifications
        contains_dairy = (food_group in self.dairy_food_groups or 
                         any(keyword in name_lower for keyword in self.dairy_keywords))
        
        contains_nuts = (food_group == 'Kacang' and 
                        any(nut_kw in name_lower for nut_kw in ['almond', 'kenari', 'hazelnut', 'mete', 'cashew', 'walnut', 'pecan', 'pistachio', 'macadamia', 'kemiri', 'wijen', 'sesame', 'kacang tanah', 'peanut']) or
                        any(keyword in name_lower for keyword in self.nuts_keywords))
        
        contains_seafood = (food_group == 'Ikan dsb' or 
                           any(keyword in name_lower for keyword in self.seafood_keywords))
        
        contains_eggs = (food_group in self.egg_food_groups or 
                        any(keyword in name_lower for keyword in self.egg_keywords))
        
        contains_soy = any(keyword in name_lower for keyword in self.soy_keywords)

        return {
            'is_vegetarian': is_vegetarian,
            'is_halal': is_halal,
            'contains_nuts': contains_nuts,
            'contains_seafood': contains_seafood,
            'contains_dairy': contains_dairy,
            'contains_eggs': contains_eggs,
            'contains_soy': contains_soy
        }