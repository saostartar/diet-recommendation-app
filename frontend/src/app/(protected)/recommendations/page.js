"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function DailyMenu() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [preferences, setPreferences] = useState({
    diet_type: "",
    allergies: [],
  });
  const [medicalCondition, setMedicalCondition] = useState("none");
  const [dailyMenu, setDailyMenu] = useState(null);
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [activeFood, setActiveFood] = useState(null);
  const [foodStatusFilter, setFoodStatusFilter] = useState("all"); // New state for food status filtering

  // Updated to include only vegetarian and halal as food preferences
  const dietTypes = [
    { value: "general", label: "Umum", icon: "🍽️" },
    { value: "vegetarian", label: "Vegetarian", icon: "🥗" },
    { value: "halal", label: "Halal", icon: "🍖" },
  ];

  // Food status options for filtering
  const foodStatusOptions = [
    { value: "all", label: "Semua" },
    { value: "Mentah", label: "Mentah" },
    { value: "Olahan", label: "Olahan" },
  ];

  // Medical conditions for metabolic diseases
  const medicalConditions = [
    { value: "none", label: "Tidak Ada Kondisi", icon: "👍" },
    { value: "diabetes", label: "Diabetes", icon: "🩸" },
    { value: "hypertension", label: "Hipertensi", icon: "❤️" },
    { value: "obesity", label: "Obesitas", icon: "⚖️" },
  ];

  // Updated allergies based on the requirements
  const commonAllergies = [
    { value: "dairy_free", label: "Susu & Produk Susu", icon: "🥛" },
    { value: "nut_free", label: "Kacang-kacangan", icon: "🥜" },
    { value: "seafood_free", label: "Makanan Laut", icon: "🦐" },
    { value: "egg_free", label: "Telur", icon: "🥚" },
    { value: "soy_free", label: "Kedelai", icon: "🫘" },
  ];

  // Define meal types in the desired order
  const mealTypes = {
    breakfast: { name: "Sarapan", icon: "☕", order: 1 },
    lunch: { name: "Makan Siang", icon: "🍲", order: 2 },
    dinner: { name: "Makan Malam", icon: "🍽️", order: 3 },
    snacks: { name: "Cemilan", icon: "🍌", order: 4 },
  };

  // Order to sort meal types
  const mealTypeOrder = ["breakfast", "lunch", "dinner", "snacks"];

  const mealGradients = {
    breakfast: "from-orange-500 to-yellow-500",
    lunch: "from-green-500 to-emerald-600",
    dinner: "from-indigo-500 to-purple-600",
    snacks: "from-pink-400 to-rose-500",
  };

  useEffect(() => {
    checkExistingPreferences();
    fetchMedicalCondition();
  }, []);

  const fetchMedicalCondition = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/diet-goals`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!res.ok) return; // Silently fail

      const data = await res.json();
      if (data.has_active_goal && data.goal.medical_condition) {
        setMedicalCondition(data.goal.medical_condition);
      }
    } catch (err) {
      console.error("Error fetching medical condition:", err);
    }
  };

  const checkExistingPreferences = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/preferences`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!res.ok) throw new Error("Gagal memuat preferensi");

      const data = await res.json();
      if (data.has_preferences) {
        setPreferences({
          diet_type: data.preferences.diet_type || "",
          allergies: data.preferences.allergies || [],
        });
        await fetchDailyMenu();
        setStep(2);
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSubmitPreferences = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/preferences`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            diet_type: preferences.diet_type,
            allergies: preferences.allergies,
          }),
        }
      );

      if (!res.ok) throw new Error("Gagal menyimpan preferensi");
      await fetchDailyMenu();
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const fetchDailyMenu = async () => {
    try {
      setLoading(true);
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/recommend/daily-menu`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!res.ok) throw new Error("Gagal memuat rekomendasi menu");

      const data = await res.json();
      setDailyMenu(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleFeedback = async (food, isConsumed, rating) => {
    try {
      setActiveFood(food.id);

      if (!food.recommendation_id) {
        toast.error("ID rekomendasi tidak ditemukan");
        return;
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          recommendation_id: food.recommendation_id,
          is_consumed: isConsumed,
          rating: rating,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || "Gagal mengirim feedback");
      }

      toast.success(
        rating
          ? `Berhasil memberi rating ${rating} bintang`
          : "Berhasil menandai makanan sebagai dimakan",
        {
          position: "bottom-right",
          autoClose: 3000,
          hideProgressBar: false,
        }
      );

      // If server indicates we should refresh the menu
      if (data.should_refresh) {
        await fetchDailyMenu();
      } else {
        // Just update local state with animation
        setTimeout(() => {
          setDailyMenu((prevMenu) => {
            const newMenu = { ...prevMenu };
            Object.keys(newMenu).forEach((mealType) => {
              newMenu[mealType] = newMenu[mealType].filter(
                (item) => item.id !== food.id
              );
            });
            return newMenu;
          });
          setActiveFood(null);
        }, 500);
      }
    } catch (err) {
      toast.error(`Error: ${err.message}`);
      setActiveFood(null);
    }
  };

  // New function to filter foods by food status
  const filterFoodsByStatus = (foods) => {
    if (!foods || foodStatusFilter === "all") return foods;
    return foods.filter((food) => food.food_status === foodStatusFilter);
  };

  if (loading) {
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
            Memuat Rekomendasi Menu Makanan Indonesia...
          </h3>
        </div>
      </div>
    );
  }

  const getImageSource = (food) => {
    if (!food)
      return "https://via.placeholder.com/64x64.png?text=Tidak+ada+gambar";

    try {
      // If no image URL is provided, use a placeholder
      if (!food.image_url) {
        return "https://via.placeholder.com/64x64.png?text=Tidak+ada+gambar";
      }

      // If the image URL is already a valid path
      if (
        food.image_url.startsWith("/static/") ||
        food.image_url.startsWith("http://") ||
        food.image_url.startsWith("https://")
      ) {
        return food.image_url;
      }

      // If we have an ID and name, try to construct a local path
      if (food.id && food.name) {
        // Create filename using a consistent pattern
        const safeFilename = food.name
          .replace(/[^a-zA-Z0-9._\- ]/g, "")
          .replace(/ /g, "_")
          .substring(0, 40);

        return `/static/food_images/${food.id}_${safeFilename}.jpg`;
      }

      // Default to placeholder
      return "https://via.placeholder.com/64x64.png?text=Tidak+ada+gambar";
    } catch (e) {
      console.error("Error generating image source:", e);
      return "https://via.placeholder.com/64x64.png?text=Tidak+ada+gambar";
    }
  };

  // Get food status icon and style
  const getFoodStatusInfo = (status) => {
    if (status === "Mentah") {
      return {
        icon: "🥬",
        bgColor: "bg-green-100",
        textColor: "text-green-800",
      };
    } else {
      return {
        icon: "🍳",
        bgColor: "bg-orange-100",
        textColor: "text-orange-800",
      };
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 py-12 px-4 sm:px-6 lg:px-8">
      <ToastContainer />
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10">
          <div className="inline-flex items-center justify-center p-2 bg-green-100 rounded-full mb-4">
            <span className="text-2xl mr-2">{step === 1 ? "🍽️" : "📋"}</span>
            <h2 className="text-green-800 font-medium text-sm px-3 py-1 rounded-full bg-green-50">
              {step === 1 ? "Langkah 1: Preferensi" : "Langkah 2: Menu Anda"}
            </h2>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            {step === 1
              ? "Preferensi Makanan Anda"
              : "Menu Makanan Indonesia Hari Ini"}
          </h1>

          <p className="mt-2 text-lg text-gray-600 max-w-2xl mx-auto">
            {step === 1
              ? "Tentukan preferensi makanan Anda untuk rekomendasi yang lebih akurat dan sesuai dengan kebutuhan diet penurunan berat badan Anda"
              : "Berikut adalah rekomendasi menu makanan Indonesia yang disesuaikan dengan preferensi dan tujuan diet penurunan berat badan Anda"}
          </p>

          {medicalCondition !== "none" && (
            <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full bg-yellow-100 text-yellow-800">
              <span className="mr-1">
                {
                  medicalConditions.find((c) => c.value === medicalCondition)
                    ?.icon
                }
              </span>
              <span className="text-sm font-medium">
                Menyesuaikan dengan kondisi:{" "}
                {
                  medicalConditions.find((c) => c.value === medicalCondition)
                    ?.label
                }
              </span>
            </div>
          )}
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl shadow-sm flex items-center">
            <div className="mr-3 bg-red-100 p-2 rounded-full">
              <svg
                className="w-5 h-5 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
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
                <label className="block text-gray-700 font-medium mb-3">
                  Tipe Diet Anda
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {dietTypes.map((type) => (
                    <label
                      key={type.value}
                      className={`flex items-center p-4 rounded-xl border-2 transition-all cursor-pointer 
                        ${
                          preferences.diet_type === type.value
                            ? "border-green-500 bg-green-50 shadow-md"
                            : "border-gray-200 hover:border-green-200 hover:bg-green-50"
                        }`}>
                      <input
                        type="radio"
                        value={type.value}
                        name="diet_type"
                        checked={preferences.diet_type === type.value}
                        onChange={(e) =>
                          setPreferences({
                            ...preferences,
                            diet_type: e.target.value,
                          })
                        }
                        className="sr-only"
                      />
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{type.icon}</span>
                        <div>
                          <span className="block font-medium text-gray-900">
                            {type.label}
                          </span>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-gray-700 font-medium mb-3">
                  Alergi Makanan
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {commonAllergies.map((allergy) => (
                    <label
                      key={allergy.value}
                      className={`flex items-center p-3 rounded-lg border transition-all cursor-pointer
                        ${
                          preferences.allergies.includes(allergy.value)
                            ? "border-yellow-400 bg-yellow-50"
                            : "border-gray-200 hover:border-yellow-200 hover:bg-yellow-50"
                        }`}>
                      <input
                        type="checkbox"
                        checked={preferences.allergies.includes(allergy.value)}
                        onChange={(e) => {
                          const newAllergies = e.target.checked
                            ? [...preferences.allergies, allergy.value]
                            : preferences.allergies.filter(
                                (a) => a !== allergy.value
                              );
                          setPreferences({
                            ...preferences,
                            allergies: newAllergies,
                          });
                        }}
                        className="sr-only"
                      />
                      <div className="flex items-center">
                        <span className="text-xl mr-3">{allergy.icon}</span>
                        <span className="text-gray-800">{allergy.label}</span>
                      </div>
                      {preferences.allergies.includes(allergy.value) && (
                        <svg
                          className="ml-auto w-5 h-5 text-yellow-500"
                          fill="currentColor"
                          viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </label>
                  ))}
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  Pilih alergi yang Anda miliki sehingga kami dapat memberikan
                  rekomendasi yang aman untuk diet penurunan berat badan Anda
                </p>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={submitting || !preferences.diet_type}
                  className={`relative overflow-hidden px-6 py-3 rounded-xl font-medium text-white
                    transition-all duration-300 transform hover:scale-[1.02]
                    ${
                      preferences.diet_type
                        ? "bg-gradient-to-r from-green-500 to-emerald-600 shadow-lg shadow-green-500/30"
                        : "bg-gray-400 cursor-not-allowed"
                    }`}>
                  {submitting ? (
                    <div className="flex items-center">
                      <svg
                        className="animate-spin -ml-1 mr-2 h-5 w-5 text-white"
                        fill="none"
                        viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Menyimpan...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      Lihat Menu Rekomendasi
                      <svg
                        className="ml-2 w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M13 7l5 5m0 0l-5 5m5-5H6"
                        />
                      </svg>
                    </div>
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        ) : (
          <>
            {/* Food Status Filter */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-6 flex justify-center">
              <div className="inline-flex bg-white rounded-lg shadow-md p-1.5">
                {foodStatusOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setFoodStatusFilter(option.value)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200
                      ${foodStatusFilter === option.value
                        ? "bg-green-50 text-green-700 shadow-sm"
                        : "text-gray-600 hover:text-green-600 hover:bg-green-50"
                      }`}
                  >
                    {option.value === "Mentah" && "🥬 "}
                    {option.value === "Olahan" && "🍳 "}
                    {option.label}
                  </button>
                ))}
              </div>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {dailyMenu &&
                mealTypeOrder.map((mealType, index) => {
                  const allFoods = dailyMenu[mealType] || [];
                  const foods = filterFoodsByStatus(allFoods);
                  
                  return foods && foods.length > 0 ? (
                    <motion.div
                      key={mealType}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
                      <div
                        className={`bg-gradient-to-r ${mealGradients[mealType]} px-4 py-4 text-white`}>
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">
                            {mealTypes[mealType].icon}
                          </span>
                          <h2 className="text-xl font-bold">
                            {mealTypes[mealType].name}
                          </h2>
                        </div>
                      </div>
                      <div className="p-4 space-y-4">
                        {foods.map((food) => (
                          <motion.div
                            key={food.id}
                            initial={{ opacity: 1 }}
                            animate={
                              activeFood === food.id
                                ? { opacity: 0.7, scale: 0.98 }
                                : { opacity: 1 }
                            }
                            exit={{ opacity: 0, height: 0, margin: 0 }}
                            className="group bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100 shadow-sm hover:shadow-md transition-all duration-300 relative">
                            {activeFood === food.id && (
                              <div className="absolute inset-0 bg-white/60 flex items-center justify-center rounded-xl z-10">
                                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-600"></div>
                              </div>
                            )}

                            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-3">
                              {/* Food Image */}
                              {food.image_url ? (
                                <div className="relative w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
                                  <img
                                    src={getImageSource(food)}
                                    alt={food.name}
                                    className="object-cover w-full h-full"
                                    onError={(e) => {
                                      e.target.onerror = null;
                                      e.target.src =
                                        "https://via.placeholder.com/64x64.png?text=Tidak+ada+gambar";
                                    }}
                                  />
                                </div>
                              ) : (
                                <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                                  <svg
                                    className="w-8 h-8 text-gray-400"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24">
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth="1.5"
                                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                                    />
                                  </svg>
                                </div>
                              )}

                              <div>
                                <h3 className="font-semibold text-gray-900 group-hover:text-green-700 transition-colors">
                                  {food.name}
                                </h3>
                                <div className="flex items-center mt-1">
                                  <p className="text-sm text-gray-500 mr-2">
                                    {food.calories} kkal
                                  </p>
                                  {/* Food Status Badge */}
                                  {food.food_status && (
                                    <span className={`text-xs px-2 py-1 rounded-full ${getFoodStatusInfo(food.food_status).bgColor} ${getFoodStatusInfo(food.food_status).textColor}`}>
                                      {getFoodStatusInfo(food.food_status).icon} {food.food_status}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div className="mt-3 grid grid-cols-3 gap-2">
                              <div className="bg-white/80 rounded-lg p-2 text-center">
                                <span className="block text-xs text-gray-500">
                                  Protein
                                </span>
                                <span className="font-medium text-gray-800">
                                  {food.protein}g
                                </span>
                              </div>
                              <div className="bg-white/80 rounded-lg p-2 text-center">
                                <span className="block text-xs text-gray-500">
                                  Karbohidrat
                                </span>
                                <span className="font-medium text-gray-800">
                                  {food.carbs}g
                                </span>
                              </div>
                              <div className="bg-white/80 rounded-lg p-2 text-center">
                                <span className="block text-xs text-gray-500">
                                  Lemak
                                </span>
                                <span className="font-medium text-gray-800">
                                  {food.fat}g
                                </span>
                              </div>
                            </div>

                            <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                              <button
                                onClick={() => handleFeedback(food, true, null)}
                                disabled={activeFood === food.id}
                                className="w-full sm:w-auto text-sm px-4 py-2 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:shadow-md transition-all duration-300 disabled:opacity-50 flex items-center justify-center">
                                <svg
                                  className="w-4 h-4 mr-1"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24">
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M5 13l4 4L19 7"
                                  />
                                </svg>
                                Sudah Dimakan
                              </button>

                              <div className="flex items-center space-x-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <button
                                    key={star}
                                    onClick={() =>
                                      handleFeedback(food, true, star)
                                    }
                                    disabled={activeFood === food.id}
                                    className="text-gray-300 hover:text-yellow-400 transition-colors duration-200 disabled:opacity-50 transform hover:scale-110">
                                    <svg
                                      className="w-6 h-6"
                                      fill="currentColor"
                                      viewBox="0 0 20 20">
                                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                    </svg>
                                  </button>
                                ))}
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  ) : null;
                })}

              {dailyMenu && 
                ((foodStatusFilter === "all" && Object.values(dailyMenu).every((foods) => foods.length === 0)) ||
                 (foodStatusFilter !== "all" && mealTypeOrder.every(mealType => 
                    filterFoodsByStatus(dailyMenu[mealType] || []).length === 0))) && (
                <div className="col-span-1 md:col-span-2 lg:col-span-4 text-center bg-white rounded-2xl shadow-md p-10">
                  <div className="mx-auto w-20 h-20 bg-yellow-50 rounded-full flex items-center justify-center mb-4">
                    <span className="text-3xl">🍽️</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">
                    {foodStatusFilter === "all" 
                      ? "Belum Ada Rekomendasi"
                      : `Tidak Ada Makanan ${foodStatusFilter}`}
                  </h3>
                  <p className="text-gray-600 mb-6">
                    {foodStatusFilter === "all"
                      ? "Anda belum memiliki rekomendasi makanan atau sudah memberikan feedback untuk semua rekomendasi hari ini."
                      : `Tidak ada rekomendasi makanan ${foodStatusFilter.toLowerCase()} yang tersedia. Coba tampilkan semua jenis makanan.`}
                  </p>
                  <div className="flex flex-col sm:flex-row justify-center gap-4">
                    {foodStatusFilter !== "all" && (
                      <button
                        onClick={() => setFoodStatusFilter("all")}
                        className="px-6 py-3 bg-blue-500 text-white font-medium rounded-lg shadow hover:shadow-xl transition-all duration-300">
                        Tampilkan Semua
                      </button>
                    )}
                    <button
                      onClick={() => setStep(1)}
                      className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-lg shadow-lg shadow-green-500/30 hover:shadow-xl transition-all duration-300">
                      Ubah Preferensi Makanan
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {step === 2 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-10 text-center">
            <button
              onClick={() => setStep(1)}
              className="inline-flex items-center text-green-600 hover:text-green-700 font-medium">
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              Ubah Preferensi Makanan
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}