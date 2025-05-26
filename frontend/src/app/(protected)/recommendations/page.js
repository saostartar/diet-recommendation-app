"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation"; // Tetap digunakan jika ada navigasi
import { motion } from "framer-motion";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function DailyMenuPage() { // Mengganti nama komponen agar lebih deskriptif
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [preferences, setPreferences] = useState({
    diet_type: "", // Akan diisi dari GET /preferences
    allergies: [], // Akan diisi dari GET /preferences
  });
  const [medicalCondition, setMedicalCondition] = useState("none"); // Diambil dari diet-goals
  const [dailyMenu, setDailyMenu] = useState(null);
  const [step, setStep] = useState(1); // 1 untuk preferensi, 2 untuk tampilan menu
  const [submittingPreferences, setSubmittingPreferences] = useState(false);
  const [activeFoodFeedback, setActiveFoodFeedback] = useState(null); // Untuk loading state feedback

  const dietTypes = [
    { value: "general", label: "Umum", icon: "🍽️" }, // 'general' untuk tidak ada preferensi diet spesifik
    { value: "vegetarian", label: "Vegetarian", icon: "🥗" },
    { value: "halal", label: "Halal", icon: "🍖" },
  ];

  const medicalConditionsOptions = [ // Nama variabel diubah agar lebih jelas
    { value: "none", label: "Tidak Ada Kondisi", icon: "👍" },
    { value: "diabetes", label: "Diabetes", icon: "🩸" },
    { value: "hypertension", label: "Hipertensi", icon: "❤️" },
    { value: "obesity", label: "Obesitas", icon: "⚖️" },
  ];

  const commonAllergies = [
    { value: "dairy_free", label: "Susu & Produk Susu", icon: "🥛" },
    { value: "nut_free", label: "Kacang-kacangan", icon: "🥜" },
    { value: "seafood_free", label: "Makanan Laut", icon: "🦐" },
    { value: "egg_free", label: "Telur", icon: "🥚" },
    { value: "soy_free", label: "Kedelai", icon: "🫘" },
  ];
  
  // Urutan dan ikon untuk meal types
  const mealTypeDisplayOrder = ['breakfast', 'lunch', 'dinner', 'snacks'];
  const mealTypeDetails = {
    breakfast: { name: "Sarapan", icon: "☕", gradient: "from-orange-400 to-yellow-400" },
    lunch: { name: "Makan Siang", icon: "🍲", gradient: "from-green-400 to-emerald-500" },
    dinner: { name: "Makan Malam", icon: "🍽️", gradient: "from-indigo-400 to-purple-500" },
    snacks: { name: "Cemilan", icon: "🍌", gradient: "from-pink-400 to-rose-400" },
  };


  useEffect(() => {
    const initializePage = async () => {
      setLoading(true);
      await fetchExistingPreferencesAndGoal();
      // Jika sudah ada preferensi, coba langsung fetch menu
      // Pengecekan `preferences.diet_type` dilakukan di fetchExistingPreferencesAndGoal
      setLoading(false);
    };
    initializePage();
  }, []);

  const fetchExistingPreferencesAndGoal = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push('/login');
        return;
      }

      // Ambil preferensi yang ada
      const prefRes = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/preferences`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      let hasExistingPrefs = false;
      if (prefRes.ok) {
        const prefData = await prefRes.json();
        if (prefData.has_preferences && prefData.preferences) {
          setPreferences({
            diet_type: prefData.preferences.diet_type || "general", // Default ke general jika kosong
            allergies: prefData.preferences.allergies || [],
          });
          hasExistingPrefs = true; // Tandai bahwa preferensi sudah ada
        } else {
           setPreferences({ diet_type: "general", allergies: [] }); // Set default jika tidak ada
        }
      } else {
        console.error("Gagal memuat preferensi:", await prefRes.text());
        setPreferences({ diet_type: "general", allergies: [] }); // Set default jika error
      }

      // Ambil kondisi medis dari tujuan diet aktif
      const goalRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/diet-goals`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (goalRes.ok) {
        const goalData = await goalRes.json();
        if (goalData.has_active_goal && goalData.goal.medical_condition) {
          setMedicalCondition(goalData.goal.medical_condition);
        } else if (!goalData.has_active_goal) {
          // Jika tidak ada tujuan diet aktif, mungkin arahkan pengguna atau tampilkan pesan
          toast.info("Anda belum memiliki tujuan diet aktif. Harap tetapkan tujuan diet Anda terlebih dahulu.", { autoClose: 5000 });
          router.push('/diet-goals'); // Arahkan ke halaman tujuan diet
          return; // Hentikan eksekusi lebih lanjut jika tidak ada goal
        }
      } else {
        console.error("Gagal memuat tujuan diet:", await goalRes.text());
        toast.error("Gagal memuat tujuan diet Anda.");
        // Pertimbangkan untuk mengarahkan ke halaman diet-goals jika ini krusial
      }
      
      // Jika preferensi sudah ada (atau default 'general' sudah diset), langsung coba fetch menu
      if (hasExistingPrefs || preferences.diet_type === "general") {
        await fetchDailyMenuInternal(token); // Gunakan fungsi internal agar bisa dipanggil dari sini
        setStep(2); // Langsung ke step 2 jika berhasil fetch menu
      } else {
        setStep(1); // Tetap di step 1 jika belum ada preferensi yang signifikan
      }

    } catch (err) {
      setError(err.message || "Terjadi kesalahan saat inisialisasi halaman.");
      console.error("Error inisialisasi:", err);
    }
  };
  
  // Fungsi internal untuk fetch daily menu
  const fetchDailyMenuInternal = async (token) => {
    try {
      setLoading(true); // Set loading true sebelum fetch
      const menuRes = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/recommend/daily-menu`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (!menuRes.ok) {
        const errorData = await menuRes.json();
        throw new Error(errorData.message || "Gagal memuat rekomendasi menu harian.");
      }
      const menuData = await menuRes.json();
      setDailyMenu(menuData);
      setError(""); // Bersihkan error jika berhasil
    } catch (err) {
      console.error("Error fetching daily menu:", err);
      setError(err.message);
      setDailyMenu(null); // Set menu jadi null jika error
    } finally {
      setLoading(false); // Set loading false setelah selesai
    }
  };


  const handleSubmitPreferences = async (e) => {
    e.preventDefault();
    setSubmittingPreferences(true);
    setError("");
    const token = localStorage.getItem("token");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/preferences`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            diet_type: preferences.diet_type === "general" ? "" : preferences.diet_type, // Kirim string kosong jika 'general'
            allergies: preferences.allergies,
          }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || "Gagal menyimpan preferensi makanan.");
      }
      
      toast.success("Preferensi berhasil disimpan!");
      await fetchDailyMenuInternal(token); // Panggil fungsi internal
      setStep(2); // Pindah ke tampilan menu

    } catch (err) {
      setError(err.message);
      toast.error(err.message || "Gagal menyimpan preferensi.");
    } finally {
      setSubmittingPreferences(false);
    }
  };

  const handleFeedback = async (foodItem, isConsumed, rating = null) => {
    setActiveFoodFeedback(foodItem.recommendation_id); // Gunakan recommendation_id
    const token = localStorage.getItem("token");
    try {
      const payload = {
        recommendation_id: foodItem.recommendation_id,
        is_consumed: isConsumed,
      };
      if (rating !== null) {
        payload.rating = rating;
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || "Gagal mengirim feedback.");
      }

      toast.success(data.message || "Feedback berhasil dikirim.", { autoClose: 2000 });
      
      // Update UI untuk item yang diberi feedback (misalnya, membuatnya terlihat "dimakan" atau menampilkan rating)
      // Tidak perlu fetch ulang seluruh menu jika backend tidak menyuruh (should_refresh: false)
      // Namun, kita perlu update state lokal untuk item ini.
      setDailyMenu(prevMenu => {
        if (!prevMenu) return null;
        const newMenu = { ...prevMenu };
        for (const mealKey in newMenu) {
          newMenu[mealKey] = newMenu[mealKey].map(food => {
            if (food.recommendation_id === foodItem.recommendation_id) {
              return { ...food, is_consumed: isConsumed, rating: rating !== null ? rating : food.rating };
            }
            return food;
          });
        }
        return newMenu;
      });

    } catch (err) {
      toast.error(err.message || "Gagal mengirim feedback.");
    } finally {
      setActiveFoodFeedback(null);
    }
  };
  
  // Fungsi getImageSource tidak lagi relevan karena image_url dihapus dari model Food
  // dan respons API. Frontend akan menampilkan placeholder.

  // Filter makanan berdasarkan status sudah dihapus.

  if (loading && step === 1 && !dailyMenu) { // Tampilkan loading hanya jika benar-benar memuat awal
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-green-50 to-emerald-50">
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-4">
            <div className="absolute top-0 w-full h-full rounded-full border-4 border-t-green-500 border-r-green-400 border-b-green-300 border-l-green-200 animate-spin"></div>
            <div className="absolute top-0 w-full h-full flex items-center justify-center">
              <span className="text-green-600 text-2xl">🥗</span>
            </div>
          </div>
          <h3 className="text-green-800 font-medium">
            Memuat preferensi dan tujuan diet Anda...
          </h3>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 py-12 px-4 sm:px-6 lg:px-8">
      <ToastContainer position="bottom-right" autoClose={3000} />
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10">
          <div className="inline-flex items-center justify-center p-2 bg-green-100 rounded-full mb-4">
            <span className="text-2xl mr-2">{step === 1 ? "🍽️" : "📋"}</span>
            <h2 className="text-green-800 font-medium text-sm px-3 py-1 rounded-full bg-green-50">
              {step === 1 ? "Langkah 1: Preferensi Makanan" : "Langkah 2: Menu Harian Anda"}
            </h2>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            {step === 1 ? "Sesuaikan Preferensi Makanan Anda" : "Rekomendasi Menu Makanan Harian"}
          </h1>
          <p className="mt-2 text-lg text-gray-600 max-w-2xl mx-auto">
            {step === 1
              ? "Pilih tipe diet dan informasikan alergi Anda untuk rekomendasi yang lebih personal."
              : "Berikut adalah rekomendasi menu yang disesuaikan dengan preferensi dan tujuan diet Anda."}
          </p>
          {medicalCondition !== "none" && step === 2 && (
            <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full bg-yellow-100 text-yellow-800">
              <span className="mr-1">
                {medicalConditionsOptions.find((c) => c.value === medicalCondition)?.icon}
              </span>
              <span className="text-sm font-medium">
                Disarankan untuk kondisi: {medicalConditionsOptions.find((c) => c.value === medicalCondition)?.label}
              </span>
            </div>
          )}
        </motion.div>

        {error && step === 1 && ( // Hanya tampilkan error preferensi di step 1
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl shadow-sm flex items-center">
            <div className="mr-3 bg-red-100 p-2 rounded-full">
              <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <p>{error}</p>
          </motion.div>
        )}

        {step === 1 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <form onSubmit={handleSubmitPreferences} className="space-y-8">
              <div>
                <label className="block text-gray-700 font-medium mb-3">Tipe Diet Anda</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {dietTypes.map((type) => (
                    <label
                      key={type.value}
                      className={`flex items-center p-4 rounded-xl border-2 transition-all cursor-pointer 
                        ${preferences.diet_type === type.value ? "border-green-500 bg-green-50 shadow-md" : "border-gray-200 hover:border-green-300 hover:bg-green-50"}`}>
                      <input
                        type="radio"
                        value={type.value}
                        name="diet_type"
                        checked={preferences.diet_type === type.value}
                        onChange={(e) => setPreferences({ ...preferences, diet_type: e.target.value })}
                        className="sr-only"
                      />
                      <span className="text-2xl mr-3">{type.icon}</span>
                      <span className="block font-medium text-gray-900">{type.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-gray-700 font-medium mb-3">Alergi Makanan (Pilih yang relevan)</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {commonAllergies.map((allergy) => (
                    <label
                      key={allergy.value}
                      className={`flex items-center p-3 rounded-lg border transition-all cursor-pointer
                        ${preferences.allergies.includes(allergy.value) ? "border-yellow-400 bg-yellow-50 ring-2 ring-yellow-300" : "border-gray-200 hover:border-yellow-300 hover:bg-yellow-50"}`}>
                      <input
                        type="checkbox"
                        checked={preferences.allergies.includes(allergy.value)}
                        onChange={(e) => {
                          const newAllergies = e.target.checked
                            ? [...preferences.allergies, allergy.value]
                            : preferences.allergies.filter((a) => a !== allergy.value);
                          setPreferences({ ...preferences, allergies: newAllergies });
                        }}
                        className="sr-only"
                      />
                      <span className="text-xl mr-3">{allergy.icon}</span>
                      <span className="text-gray-800">{allergy.label}</span>
                      {preferences.allergies.includes(allergy.value) && (
                        <svg className="ml-auto w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                      )}
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={submittingPreferences}
                  className={`relative overflow-hidden px-6 py-3 rounded-xl font-medium text-white
                    transition-all duration-300 transform hover:scale-[1.02]
                    ${preferences.diet_type ? "bg-gradient-to-r from-green-500 to-emerald-600 shadow-lg shadow-green-500/30" : "bg-gray-400 cursor-not-allowed"}`}>
                  {submittingPreferences ? (
                    <div className="flex items-center"><svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Menyimpan...</div>
                  ) : (
                    <div className="flex items-center">Lihat Menu Rekomendasi <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg></div>
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        ) : (
          <>
            {/* Filter makanan berdasarkan status sudah dihapus */}
            {loading && !dailyMenu && ( // Tampilkan loading spesifik saat menu sedang diambil
                 <div className="min-h-[300px] flex items-center justify-center bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
                    <div className="text-center">
                        <div className="relative w-16 h-16 mx-auto mb-3">
                            <div className="absolute top-0 w-full h-full rounded-full border-4 border-t-green-500 border-r-green-400 border-b-green-300 border-l-green-200 animate-spin"></div>
                            <div className="absolute top-0 w-full h-full flex items-center justify-center">
                                <span className="text-green-600 text-xl">🍲</span>
                            </div>
                        </div>
                        <h3 className="text-green-800 font-medium">Menyiapkan menu harian Anda...</h3>
                    </div>
                </div>
            )}

            {error && !loading && ( // Tampilkan error jika ada dan tidak sedang loading
                <div className="col-span-1 md:col-span-2 lg:col-span-4 text-center bg-white rounded-2xl shadow-md p-10 border border-red-200">
                    <div className="mx-auto w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mb-4">
                        <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-2">Oops! Terjadi Kesalahan</h3>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button
                        onClick={() => { setError(""); setLoading(true); fetchDailyMenuInternal(localStorage.getItem("token")); }}
                        className="px-6 py-3 bg-red-500 text-white font-medium rounded-lg shadow hover:shadow-xl transition-all duration-300">
                        Coba Lagi
                    </button>
                </div>
            )}

            {!loading && dailyMenu && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {mealTypeDisplayOrder.map((mealKey, index) => {
                  const mealData = mealTypeDetails[mealKey];
                  const foods = dailyMenu[mealKey] || [];
                  
                  return (
                    <motion.div
                      key={mealKey}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.05 }}
                      className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 flex flex-col">
                      <div className={`bg-gradient-to-r ${mealData.gradient} px-4 py-4 text-white`}>
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">{mealData.icon}</span>
                          <h2 className="text-xl font-bold">{mealData.name}</h2>
                        </div>
                      </div>
                      <div className="p-4 space-y-4 flex-grow">
                        {foods.length > 0 ? (
                          foods.map((food) => (
                            <motion.div
                              key={food.recommendation_id} // Gunakan recommendation_id sebagai key
                              layout // Untuk animasi saat item dihapus (jika ada)
                              initial={{ opacity: 1 }}
                              animate={activeFoodFeedback === food.recommendation_id ? { opacity: 0.7, scale: 0.98 } : { opacity: 1 }}
                              className="group bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-3 border border-green-100 shadow-sm hover:shadow-md transition-all duration-300 relative">
                              {activeFoodFeedback === food.recommendation_id && (
                                <div className="absolute inset-0 bg-white/60 flex items-center justify-center rounded-xl z-10">
                                  <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-green-600"></div>
                                </div>
                              )}
                              <div className="flex items-start gap-3 mb-2">
                                <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center text-gray-400 text-xl flex-shrink-0">
                                  {/* Placeholder untuk gambar, karena image_url sekarang None */}
                                  🍲 
                                </div>
                                <div>
                                  <h3 className="font-semibold text-sm text-gray-900 group-hover:text-green-700 transition-colors leading-tight">
                                    {food.name}
                                  </h3>
                                  <p className="text-xs text-gray-500">{food.calories} kkal</p>
                                </div>
                              </div>
                              <div className="grid grid-cols-3 gap-1.5 text-xs mb-3">
                                <div className="bg-white/70 rounded p-1.5 text-center"><span className="block text-gray-500 text-[10px] uppercase tracking-wider">Protein</span> <span className="font-medium text-gray-700">{food.protein}g</span></div>
                                <div className="bg-white/70 rounded p-1.5 text-center"><span className="block text-gray-500 text-[10px] uppercase tracking-wider">Karbo</span> <span className="font-medium text-gray-700">{food.carbs}g</span></div>
                                <div className="bg-white/70 rounded p-1.5 text-center"><span className="block text-gray-500 text-[10px] uppercase tracking-wider">Lemak</span> <span className="font-medium text-gray-700">{food.fat}g</span></div>
                              </div>
                              <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
                                <button
                                  onClick={() => handleFeedback(food, true, null)}
                                  disabled={activeFoodFeedback === food.recommendation_id}
                                  className={`w-full sm:w-auto text-xs px-3 py-1.5 rounded-md transition-all duration-300 disabled:opacity-50 flex items-center justify-center
                                    ${food.is_consumed ? "bg-green-600 text-white" : "bg-white border border-green-600 text-green-700 hover:bg-green-600 hover:text-white"}`}>
                                  <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                  {food.is_consumed ? "Dimakan" : "Tandai Dimakan"}
                                </button>
                                <div className="flex items-center space-x-0.5">
                                  {[1, 2, 3, 4, 5].map((star) => (
                                    <button
                                      key={star}
                                      onClick={() => handleFeedback(food, true, star)}
                                      disabled={activeFoodFeedback === food.recommendation_id}
                                      className={`p-1 rounded-full transition-colors duration-200 disabled:opacity-50 transform hover:scale-110
                                        ${(food.rating || 0) >= star ? "text-yellow-400" : "text-gray-300 hover:text-yellow-300"}`}>
                                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                                    </button>
                                  ))}
                                </div>
                              </div>
                            </motion.div>
                          ))
                        ) : (
                          <div className="text-center text-gray-500 py-8">
                            <svg className="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
                            <p className="text-sm">Belum ada rekomendasi untuk {mealData.name.toLowerCase()} saat ini.</p>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}

                {/* Pesan jika semua kategori kosong */}
                {dailyMenu && Object.values(dailyMenu).every(foods => foods.length === 0) && !error && (
                    <div className="col-span-1 md:col-span-2 lg:col-span-4 text-center bg-white rounded-2xl shadow-md p-10">
                        <div className="mx-auto w-20 h-20 bg-yellow-50 rounded-full flex items-center justify-center mb-4">
                            <span className="text-3xl">🍽️</span>
                        </div>
                        <h3 className="text-xl font-semibold text-gray-800 mb-2">
                            Tidak Ada Rekomendasi Tersedia
                        </h3>
                        <p className="text-gray-600 mb-6">
                            Kami tidak dapat menemukan rekomendasi yang cocok untuk Anda saat ini. Coba ubah preferensi Anda.
                        </p>
                        <button
                            onClick={() => { setStep(1); setDailyMenu(null); setError(""); }}
                            className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-lg shadow-lg shadow-green-500/30 hover:shadow-xl transition-all duration-300">
                            Ubah Preferensi Makanan
                        </button>
                    </div>
                )}
              </div>
            )}
          </>
        )}

        {step === 2 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-10 text-center">
            <button
              onClick={() => { setStep(1); setDailyMenu(null); setError(""); }} // Reset menu dan error saat kembali
              className="inline-flex items-center text-green-600 hover:text-green-700 font-medium py-2 px-4 rounded-lg hover:bg-green-50 transition-colors">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
              Ubah Preferensi Makanan
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}

