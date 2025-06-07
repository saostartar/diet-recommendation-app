"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [userData, setUserData] = useState(null);
  const [nutritionInfo, setNutritionInfo] = useState(null);
  const [lastWeightUpdate, setLastWeightUpdate] = useState(null);

  useEffect(() => {
    fetchUserData();
    fetchDietGoal();
    fetchNutritionInfo();
    fetchLastWeightUpdate();
  }, []);

  const fetchUserData = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!res.ok) throw new Error("Gagal memuat data pengguna");

      const data = await res.json();
      setUserData(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchDietGoal = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/diet-goals`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!res.ok) throw new Error("Gagal memuat tujuan diet");

      const data = await res.json();

      if (data.has_active_goal) {
        setUserData((prevData) => ({
          ...prevData,
          diet_goal: data.goal,
        }));
      }
    } catch (err) {
      // Silently handle error
      console.error("Error fetching diet goal:", err);
    }
  };

  const fetchNutritionInfo = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/preferences`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        setNutritionInfo(data);
      }
    } catch (err) {
      console.error("Error fetching nutrition info:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLastWeightUpdate = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/progress/weight`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        if (data.progress && data.progress.length > 0) {
          const lastUpdate = data.progress[data.progress.length - 1];
          setLastWeightUpdate(lastUpdate);
        }
      }
    } catch (err) {
      console.error("Error fetching last weight update:", err);
    }
  };

  const calculateDailyCalories = (user) => {
    if (!user || !user.height || !user.weight || !user.age || !user.gender) {
      return 2000; // Default value
    }

    // Calculate BMR using Harris-Benedict formula
    let bmr = 0;
    if (user.gender === "M") {
      bmr =
        88.362 + 13.397 * user.weight + 4.799 * user.height - 5.677 * user.age;
    } else {
      bmr =
        447.593 + 9.247 * user.weight + 3.098 * user.height - 4.33 * user.age;
    }

    // Activity multiplier
    const activityMultipliers = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9,
    };

    const multiplier = activityMultipliers[user.activity_level] || 1.2;

    // Apply multiplier and adjust for weight loss goal (20% deficit)
    let dailyCalories = bmr * multiplier * 0.8;

    // Further adjustment based on medical condition
    if (user.diet_goal?.medical_condition) {
      switch (user.diet_goal.medical_condition) {
        case 'diabetes':
          // For diabetes, slightly lower carbs impact
          dailyCalories *= 0.95;
          break;
        case 'hypertension':
          // For hypertension, slightly lower calories
          dailyCalories *= 0.9;
          break;
        case 'obesity':
          // For obesity, more aggressive deficit
          dailyCalories *= 0.85;
          break;
      }
    }

    return Math.round(dailyCalories);
  };

  const calculateBMI = (weight, height) => {
    if (!weight || !height) return 0;
    const heightInMeters = height / 100;
    return (weight / (heightInMeters * heightInMeters)).toFixed(1);
  };

  const getBMICategory = (bmi) => {
    if (bmi < 18.5) return { category: "Kurus", color: "text-blue-600" };
    if (bmi < 25) return { category: "Normal", color: "text-green-600" };
    if (bmi < 30) return { category: "Berlebih", color: "text-yellow-600" };
    return { category: "Obesitas", color: "text-red-600" };
  };

  const getDaysUntilTarget = () => {
    if (!userData?.diet_goal?.target_date) return null;
    const targetDate = new Date(userData.diet_goal.target_date);
    const today = new Date();
    const diffTime = targetDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-green-50">
        <div className="relative">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-16 w-16 rounded-full border-4 border-green-200"></div>
          </div>
          <div className="animate-spin h-16 w-16 rounded-full border-t-4 border-b-4 border-green-600"></div>
          <p className="absolute -bottom-8 w-full text-center text-green-800 font-medium">
            Memuat...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="bg-white rounded-3xl shadow-xl overflow-hidden mb-8 transform transition-all hover:shadow-2xl">
          <div className="bg-gradient-to-r from-green-500 to-green-700 px-8 py-10 relative">
            {/* Abstract decorative circles */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-10 rounded-full -translate-y-1/2 translate-x-1/4"></div>
            <div className="absolute bottom-0 left-20 w-40 h-40 bg-white opacity-10 rounded-full translate-y-1/2"></div>

            <div className="flex flex-col md:flex-row md:items-center md:justify-between relative z-10">
              <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-6 mb-4 md:mb-0">
                <div className="relative h-24 w-24 rounded-xl overflow-hidden border-4 border-white shadow-inner transform transition-transform hover:scale-105">
                  <Image
                    src={
                      userData?.avatar_url
                        ? userData.avatar_url.startsWith("http")
                          ? userData.avatar_url
                          : `${process.env.NEXT_PUBLIC_API_URL}${userData.avatar_url}`
                        : "/images/default_avatar.png"
                    }
                    alt="Profile"
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="text-white">
                  <div className="flex items-center space-x-2 mb-1">
                    <div className="w-2 h-2 rounded-full bg-green-300 animate-pulse"></div>
                    <p className="text-green-100 text-sm font-medium">Online</p>
                  </div>
                  <h1 className="text-3xl font-bold">
                    Halo, {userData?.username || "Pengguna"}!
                  </h1>
                  <div className="flex items-center mt-2">
                    <div className="flex items-center bg-white/20 rounded-full px-3 py-1 text-sm">
                      <svg
                        className="w-4 h-4 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                          clipRule="evenodd"></path>
                      </svg>
                      <span>
                        Target: {userData?.diet_goal?.target_weight || "0"} kg
                      </span>
                    </div>
                    <div className="bg-white/20 rounded-full px-3 py-1 ml-2 text-sm flex items-center">
                      <svg
                        className="w-4 h-4 mr-1"
                        fill="currentColor"
                        viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                          clipRule="evenodd"></path>
                      </svg>
                      <span>
                        Mulai:{" "}
                        {new Date(
                          userData?.diet_goal?.created_at || Date.now()
                        ).toLocaleDateString("id-ID", {
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
            {/* Daily Calories Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all hover:scale-[1.02] hover:shadow-xl">
              <div className="bg-gradient-to-br from-green-400 to-green-600 p-3 flex items-center space-x-2">
                <div className="bg-white/20 p-2 rounded-lg">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="currentColor"
                    viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <h3 className="text-white font-medium">Kalori Harian</h3>
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-gray-800">
                      {calculateDailyCalories(userData)}
                    </p>
                    <p className="text-sm text-gray-500">kilokalori</p>
                  </div>
                  <div className="bg-green-100 rounded-full p-2">
                    <svg
                      className="w-8 h-8 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="mt-4 h-1 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="bg-green-500 h-1 rounded-full"
                    style={{
                      width: `${Math.min(
                        calculateDailyCalories(userData) / 30,
                        100
                      )}%`,
                    }}></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Berdasarkan profil dan aktivitas Anda
                </p>
              </div>
            </div>

            {/* Current Weight Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all hover:scale-[1.02] hover:shadow-xl">
              <div className="bg-gradient-to-br from-blue-400 to-blue-600 p-3 flex items-center space-x-2">
                <div className="bg-white/20 p-2 rounded-lg">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                    />
                  </svg>
                </div>
                <h3 className="text-white font-medium">Berat Saat Ini</h3>
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-3xl font-bold text-gray-800">
                      {userData?.weight || "0"}
                    </p>
                    <p className="text-sm text-gray-500">kilogram</p>
                  </div>
                  <div className="bg-blue-100 rounded-full p-2">
                    <svg
                      className="w-8 h-8 text-blue-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                </div>
                {userData?.diet_goal && (
                  <>
                    <div className="flex items-center justify-between mt-2 text-sm">
                      <span className="text-gray-500">Target</span>
                      <span className="font-medium text-gray-800">
                        {userData.diet_goal.target_weight} kg
                      </span>
                    </div>
                    <div className="mt-2 h-1 w-full bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="bg-blue-500 h-1 rounded-full"
                        style={{
                          width: `${Math.min(
                            Math.max(
                              ((userData.weight -
                                userData.diet_goal.target_weight) /
                                (userData.weight * 0.2)) *
                                100,
                              0
                            ),
                            100
                          )}%`,
                        }}></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Progres menuju target
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Activity Level Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all hover:scale-[1.02] hover:shadow-xl">
              <div className="bg-gradient-to-br from-purple-400 to-purple-600 p-3 flex items-center space-x-2">
                <div className="bg-white/20 p-2 rounded-lg">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
                <h3 className="text-white font-medium">Tingkat Aktivitas</h3>
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold text-gray-800">
                      {(() => {
                        const activityMap = {
                          sedentary: "Rendah",
                          light: "Ringan",
                          moderate: "Sedang",
                          active: "Aktif",
                          very_active: "Sangat Aktif",
                        };
                        return (
                          activityMap[userData?.activity_level] || "Sedang"
                        );
                      })()}
                    </p>
                    <p className="text-sm text-gray-500">tingkat aktivitas</p>
                  </div>
                  <div className="bg-purple-100 rounded-full p-2">
                    <svg
                      className="w-8 h-8 text-purple-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                      />
                    </svg>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex items-center space-x-1">
                    {[
                      "sedentary",
                      "light",
                      "moderate",
                      "active",
                      "very_active",
                    ].map((level, index) => (
                      <div
                        key={level}
                        className={`flex-1 h-1.5 rounded-full ${
                          userData?.activity_level === level
                            ? "bg-purple-500"
                            : "bg-gray-200"
                        }`}></div>
                    ))}
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-gray-500">Rendah</span>
                    <span className="text-xs text-gray-500">Sangat Aktif</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Berdasarkan data profil Anda
                </p>
              </div>
            </div>

            {/* Medical Condition Card */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden transform transition-all hover:scale-[1.02] hover:shadow-xl">
              <div className="bg-gradient-to-br from-yellow-400 to-yellow-600 p-3 flex items-center space-x-2">
                <div className="bg-white/20 p-2 rounded-lg">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                    />
                  </svg>
                </div>
                <h3 className="text-white font-medium">Status Kesehatan</h3>
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    {(() => {
                      // Display medical condition
                      const conditionMap = {
                        'none': 'Tidak Ada',
                        'diabetes': 'Diabetes',
                        'hypertension': 'Hipertensi',
                        'obesity': 'Obesitas'
                      };
                      
                      const medicalCondition = userData?.diet_goal?.medical_condition || 'none';
                      const conditionDisplay = conditionMap[medicalCondition];
                      
                      const conditionColor = medicalCondition === 'none' ? 
                        '#047857' : 
                        (medicalCondition === 'obesity' ? '#b91c1c' : '#9f580a');
                      
                      return (
                        <>
                          <p className="text-2xl font-bold text-gray-800">
                            {conditionDisplay}
                          </p>
                          <p className="text-sm text-gray-500">status kesehatan</p>
                        </>
                      );
                    })()}
                  </div>
                  <div className="bg-yellow-100 rounded-full p-2">
                    <svg
                      className="w-8 h-8 text-yellow-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex items-center mt-2 bg-yellow-50 p-2 rounded-lg text-yellow-800 text-xs">
                    <svg 
                      className="w-4 h-4 mr-1 text-yellow-600" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor">
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth="2" 
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                      />
                    </svg>
                    <span>
                      Rekomendasi diet khusus disesuaikan dengan kondisi kesehatan Anda
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Indikator kesehatan untuk diet yang tepat
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Informasi Berguna */}
        <h2 className="text-xl font-bold text-gray-800 mb-4 px-1 flex items-center">
          <svg
            className="w-5 h-5 mr-2 text-green-600"
            fill="currentColor"
            viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          Informasi Berguna
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          {/* BMI Information */}
          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="mr-4 bg-indigo-100 p-3 rounded-xl">
                <svg
                  className="w-6 h-6 text-indigo-700"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">BMI Anda</h3>
                <p className="text-2xl font-bold text-indigo-600">
                  {calculateBMI(userData?.weight, userData?.height)}
                </p>
              </div>
            </div>
            <div className="text-center">
              <span className={`text-sm font-medium ${getBMICategory(calculateBMI(userData?.weight, userData?.height)).color}`}>
                Kategori: {getBMICategory(calculateBMI(userData?.weight, userData?.height)).category}
              </span>
            </div>
          </div>

          {/* Diet Type Information */}
          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="mr-4 bg-green-100 p-3 rounded-xl">
                <svg
                  className="w-6 h-6 text-green-700"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Tipe Diet</h3>
                <p className="text-sm text-gray-600">
                  {nutritionInfo?.has_preferences 
                    ? (nutritionInfo.preferences.diet_type || 'Umum')
                    : 'Belum diatur'}
                </p>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {nutritionInfo?.has_preferences && nutritionInfo.preferences.allergies?.length > 0
                ? `Alergi: ${nutritionInfo.preferences.allergies.length} item`
                : 'Tidak ada alergi yang tercatat'}
            </div>
          </div>

          {/* Target Date Information */}
          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="mr-4 bg-orange-100 p-3 rounded-xl">
                <svg
                  className="w-6 h-6 text-orange-700"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Target Waktu</h3>
                <p className="text-lg font-bold text-orange-600">
                  {getDaysUntilTarget() !== null ? `${getDaysUntilTarget()} hari` : 'Belum diatur'}
                </p>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {userData?.diet_goal?.target_date 
                ? `Target: ${new Date(userData.diet_goal.target_date).toLocaleDateString('id-ID')}`
                : 'Belum ada target tanggal'}
            </div>
          </div>

          {/* Last Weight Update */}
          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="mr-4 bg-purple-100 p-3 rounded-xl">
                <svg
                  className="w-6 h-6 text-purple-700"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Update Terakhir</h3>
                <p className="text-sm font-medium text-purple-600">
                  {lastWeightUpdate 
                    ? `${lastWeightUpdate.weight} kg`
                    : 'Belum ada data'}
                </p>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {lastWeightUpdate 
                ? new Date(lastWeightUpdate.date).toLocaleDateString('id-ID', { 
                    day: 'numeric', 
                    month: 'short', 
                    year: 'numeric' 
                  })
                : 'Perbarui berat badan Anda'}
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl flex items-center">
            <svg
              className="w-5 h-5 mr-2 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <p>{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}