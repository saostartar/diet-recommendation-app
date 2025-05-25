"use client";
import Image from "next/image";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function Profile() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState("");
  const [error, setError] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    age: "",
    weight: "",
    height: "",
    gender: "",
    activity_level: "",
    medical_condition: "",
    avatar: null,
  });

  const activityLevels = [
    { value: "sedentary", label: "Tidak Aktif" },
    { value: "light", label: "Aktivitas Ringan" },
    { value: "moderate", label: "Aktivitas Sedang" },
    { value: "active", label: "Aktif" },
    { value: "very_active", label: "Sangat Aktif" },
  ];

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    // Keep existing fetch logic
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!res.ok) throw new Error("Gagal memuat profil");

      const data = await res.json();
      setProfile(data);
      setFormData({
        ...data,
        gender: data.gender === "M" ? "M" : "F",
      });
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    // Keep existing submit logic
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/profile/update`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            ...formData,
            age: parseInt(formData.age),
            weight: parseFloat(formData.weight),
            height: parseFloat(formData.height),
          }),
        }
      );

      if (!res.ok) throw new Error("Gagal memperbarui profil");

      const data = await res.json();
      const updatedProfile = {
        ...data,
        avatar_url: data.avatar_url
          ? data.avatar_url.startsWith("http")
            ? data.avatar_url
            : `${process.env.NEXT_PUBLIC_API_URL}${data.avatar_url}`
          : profile?.avatar_url,
      };

      setProfile(updatedProfile);
      setSuccessMessage("Profil berhasil diperbarui");
      setTimeout(() => setSuccessMessage(""), 3000);
      setEditMode(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("avatar", file);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/profile/avatar`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: formData,
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || "Gagal mengunggah foto profil");
      }

      const data = await res.json();

      // Handle the avatar URL correctly
      const fullAvatarUrl = data.avatar_url.startsWith("http")
        ? data.avatar_url
        : `${process.env.NEXT_PUBLIC_API_URL}${data.avatar_url}`;

      // Update both the profile state and formData state with the new avatar
      setProfile((prev) => ({
        ...prev,
        avatar_url: fullAvatarUrl,
      }));

      // Also update formData to ensure consistency
      setFormData((prev) => ({
        ...prev,
        avatar_url: fullAvatarUrl,
      }));

      // Show success message (optional)
      setSuccessMessage("Foto profil berhasil diperbarui");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      console.error("Error uploading avatar:", err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-emerald-50">
        <div className="relative">
          <div className="h-20 w-20 rounded-full border-t-4 border-b-4 border-green-500 animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-green-600 text-xl">🥗</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 py-12 px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-5xl mx-auto">
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl shadow-sm flex items-center">
            <svg
              className="w-5 h-5 mr-3 text-red-500"
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
            {error}
          </motion.div>
        )}
        {successMessage && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 bg-green-50 border border-green-200 text-green-600 p-4 rounded-xl shadow-sm flex items-center">
            <svg
              className="w-5 h-5 mr-3 text-green-500"
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
            {successMessage}
          </motion.div>
        )}

        <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
          {/* Enhanced profile header */}
          <div className="relative">
            {/* Background pattern */}
            <div className="absolute inset-0 bg-gradient-to-r from-green-600 to-green-700 opacity-90">
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.2'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
                }}></div>
            </div>

            <div className="relative px-6 py-12 md:py-16 md:px-10">
              <div className="flex flex-col md:flex-row md:items-end items-center md:space-x-8">
                <div className="relative group mb-6 md:mb-0">
                  <div className="relative h-32 w-32 rounded-full bg-white p-1.5 shadow-lg transform transition-transform group-hover:scale-105">
                    <div className="w-full h-full rounded-full overflow-hidden ring-4 ring-white ring-offset-2 ring-offset-green-500 relative">
                      <Image
                        src={
                          profile?.avatar_url
                            ? profile.avatar_url.startsWith("http")
                              ? profile.avatar_url
                              : `${process.env.NEXT_PUBLIC_API_URL}${profile.avatar_url}`
                            : "/images/default_avatar.png"
                        }
                        alt="Foto Profil"
                        fill
                        className="object-cover"
                        // Add a key prop to force re-render when avatar changes
                        key={profile?.avatar_url || "default-avatar"}
                      />
                    </div>

                    {editMode && (
                      <label className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-60 text-white rounded-full cursor-pointer opacity-0 group-hover:opacity-100 transition-all duration-300">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={handleAvatarUpload}
                        />
                        <div className="flex flex-col items-center">
                          <svg
                            className="w-8 h-8"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                          <span className="text-sm mt-1 font-medium">
                            Ubah Foto
                          </span>
                        </div>
                      </label>
                    )}
                  </div>

                  {/* Decorative elements */}
                  <div className="absolute -bottom-3 -right-3 h-8 w-8 bg-yellow-300 rounded-full opacity-75 blur-sm"></div>
                  <div className="absolute -top-4 -left-2 h-6 w-6 bg-green-400 rounded-full opacity-75 blur-sm"></div>
                </div>

                <div className="text-center md:text-left">
                  <h1 className="text-3xl md:text-4xl font-bold text-white mb-1 tracking-tight">
                    {profile?.username}
                  </h1>
                  <div className="flex items-center justify-center md:justify-start text-green-100 space-x-2">
                    <svg
                      className="w-5 h-5"
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
                    <p>
                      Member sejak{" "}
                      {new Date(profile?.created_at).toLocaleDateString(
                        "id-ID",
                        { year: "numeric", month: "long", day: "numeric" }
                      )}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6 md:p-8 bg-white">
            {!editMode ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="space-y-8">
                <h2 className="text-2xl font-bold text-gray-800 border-b-2 border-green-100 pb-2 inline-block">
                  Informasi Pribadi
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Email Card */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-blue-100 rounded-lg text-blue-700">
                        <svg
                          className="w-6 h-6"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-700">
                        Email
                      </h3>
                    </div>
                    <p className="text-gray-600 ml-11">{profile?.email}</p>
                  </motion.div>

                  {/* Age Card */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-green-100 rounded-lg text-green-700">
                        <svg
                          className="w-6 h-6"
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
                      <h3 className="text-lg font-semibold text-gray-700">
                        Usia
                      </h3>
                    </div>
                    <p className="text-gray-600 ml-11">{profile?.age} tahun</p>
                  </motion.div>

                  {/* Gender Card */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-purple-100 rounded-lg text-purple-700">
                        <svg
                          className="w-6 h-6"
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
                      <h3 className="text-lg font-semibold text-gray-700">
                        Jenis Kelamin
                      </h3>
                    </div>
                    <p className="text-gray-600 ml-11">
                      {profile?.gender === "M" ? "Laki-laki" : "Perempuan"}
                    </p>
                  </motion.div>

                  {/* Weight Card */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-yellow-100 rounded-lg text-yellow-700">
                        <svg
                          className="w-6 h-6"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2M3 16V6a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-700">
                        Berat Badan
                      </h3>
                    </div>
                    <p className="text-gray-600 ml-11">{profile?.weight} kg</p>
                  </motion.div>

                  {/* Height Card */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                        <svg
                          className="w-6 h-6"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-700">
                        Tinggi Badan
                      </h3>
                    </div>
                    <p className="text-gray-600 ml-11">{profile?.height} cm</p>
                  </motion.div>

                  {/* Activity Level Card */}
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-red-100 rounded-lg text-red-600">
                        <svg
                          className="w-6 h-6"
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
                      <h3 className="text-lg font-semibold text-gray-700">
                        Tingkat Aktivitas
                      </h3>
                    </div>
                    <p className="text-gray-600 ml-11">
                      {
                        activityLevels.find(
                          (level) => level.value === profile?.activity_level
                        )?.label
                      }
                    </p>
                  </motion.div>
                </div>

                {/* Medical Condition Card */}
                <div className="mt-8">
                  <h2 className="text-2xl font-bold text-gray-800 border-b-2 border-green-100 pb-2 inline-block mb-6">
                    Kondisi Medis
                  </h2>
                  <motion.div
                    whileHover={{ scale: 1.01 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="p-2 bg-pink-100 rounded-lg text-pink-600">
                        <svg
                          className="w-6 h-6"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M9 12h6m-6 4h6m-6-8h6M5 5a2 2 0 012-2h10a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V5z"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-700">
                        Catatan Medis
                      </h3>
                    </div>
                    <div className="pl-11 text-gray-600">
                      {profile?.medical_condition ? (
                        <p>{profile?.medical_condition}</p>
                      ) : (
                        <p className="text-gray-400 italic">
                          Tidak ada catatan kondisi medis
                        </p>
                      )}
                    </div>
                  </motion.div>
                </div>

                {/* BMI Calculation Card */}
                <div className="mt-8">
                  <h2 className="text-2xl font-bold text-gray-800 border-b-2 border-green-100 pb-2 inline-block mb-6">
                    Indeks Massa Tubuh (BMI)
                  </h2>
                  <motion.div
                    whileHover={{ scale: 1.01 }}
                    transition={{ duration: 0.2 }}
                    className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center space-x-3 mb-5">
                      <div className="p-2 bg-gradient-to-r from-blue-100 to-green-100 rounded-lg text-green-700">
                        <svg
                          className="w-6 h-6"
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
                      <h3 className="text-lg font-semibold text-gray-700">
                        BMI Anda
                      </h3>
                    </div>

                    {profile?.height && profile?.weight ? (
                      <div className="pl-11">
                        <div className="flex items-center justify-between mb-2">
                          <div className="w-full">
                            <div className="text-2xl font-bold text-gray-800 mb-2">
                              {(
                                profile.weight /
                                (profile.height / 100) ** 2
                              ).toFixed(1)}
                            </div>
                            <div className="h-2.5 bg-gray-200 rounded-full w-full">
                              <div
                                className="h-2.5 rounded-full"
                                style={{
                                  width: `${Math.min(
                                    (profile.weight /
                                      (profile.height / 100) ** 2 /
                                      40) *
                                      100,
                                    100
                                  )}%`,
                                  background: `linear-gradient(to right, #3b82f6, #10b981, #f59e0b, #ef4444)`,
                                }}></div>
                            </div>
                            <div className="flex justify-between mt-1.5 text-xs text-gray-500">
                              <span>Kurus</span>
                              <span>Normal</span>
                              <span>Kelebihan</span>
                              <span>Obesitas</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="pl-11 text-gray-400 italic">
                        Data tinggi atau berat badan tidak lengkap
                      </p>
                    )}
                  </motion.div>
                </div>

                <div className="pt-6 flex justify-end">
                  <motion.button
                    onClick={() => setEditMode(true)}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    className="px-8 py-3.5 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transform transition-all duration-300 flex items-center space-x-2">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                      />
                    </svg>
                    <span>Edit Profil</span>
                  </motion.button>
                </div>
              </motion.div>
            ) : (
              <motion.form
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                onSubmit={handleSubmit}
                className="space-y-8">
                <h2 className="text-2xl font-bold text-gray-800 border-b-2 border-green-100 pb-2 inline-block">
                  Edit Informasi Profil
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Username
                      </label>
                      <div className="relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                          <svg
                            className="w-5 h-5"
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
                        <input
                          type="text"
                          required
                          value={formData.username}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              username: e.target.value,
                            })
                          }
                          className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700"
                          placeholder="Nama Pengguna"
                        />
                      </div>
                    </div>

                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Email
                      </label>
                      <div className="relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                            />
                          </svg>
                        </div>
                        <input
                          type="email"
                          required
                          value={formData.email}
                          onChange={(e) =>
                            setFormData({ ...formData, email: e.target.value })
                          }
                          className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700"
                          placeholder="Alamat Email"
                        />
                      </div>
                    </div>

                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Usia
                      </label>
                      <div className="relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                          <svg
                            className="w-5 h-5"
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
                        <input
                          type="number"
                          required
                          min="10"
                          max="120"
                          value={formData.age}
                          onChange={(e) =>
                            setFormData({ ...formData, age: e.target.value })
                          }
                          className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700"
                          placeholder="Usia (tahun)"
                        />
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm text-gray-400">
                          tahun
                        </div>
                      </div>
                    </div>

                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Jenis Kelamin
                      </label>
                      <div className="flex space-x-4">
                        <label className="flex-1 flex items-center p-4 bg-white border border-gray-200 rounded-lg cursor-pointer hover:border-green-400 transition-colors">
                          <input
                            type="radio"
                            name="gender"
                            value="M"
                            checked={formData.gender === "M"}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                gender: e.target.value,
                              })
                            }
                            className="h-5 w-5 text-green-600 border-gray-300 focus:ring-green-500"
                          />
                          <div className="flex items-center ml-3">
                            <div className="p-1.5 bg-blue-100 rounded-full mr-3">
                              <svg
                                className="w-4 h-4 text-blue-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth="2"
                                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                              </svg>
                            </div>
                            <span className="text-sm font-medium text-gray-700">
                              Laki-laki
                            </span>
                          </div>
                        </label>

                        <label className="flex-1 flex items-center p-4 bg-white border border-gray-200 rounded-lg cursor-pointer hover:border-green-400 transition-colors">
                          <input
                            type="radio"
                            name="gender"
                            value="F"
                            checked={formData.gender === "F"}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                gender: e.target.value,
                              })
                            }
                            className="h-5 w-5 text-green-600 border-gray-300 focus:ring-green-500"
                          />
                          <div className="flex items-center ml-3">
                            <div className="p-1.5 bg-pink-100 rounded-full mr-3">
                              <svg
                                className="w-4 h-4 text-pink-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth="2"
                                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                              </svg>
                            </div>
                            <span className="text-sm font-medium text-gray-700">
                              Perempuan
                            </span>
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Berat Badan
                      </label>
                      <div className="relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2M3 16V6a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                            />
                          </svg>
                        </div>
                        <input
                          type="number"
                          required
                          min="30"
                          max="200"
                          step="0.1"
                          value={formData.weight}
                          onChange={(e) =>
                            setFormData({ ...formData, weight: e.target.value })
                          }
                          className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700"
                          placeholder="Berat Badan (kg)"
                        />
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm text-gray-400">
                          kg
                        </div>
                      </div>
                    </div>

                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Tinggi Badan
                      </label>
                      <div className="relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                            />
                          </svg>
                        </div>
                        <input
                          type="number"
                          required
                          min="100"
                          max="250"
                          value={formData.height}
                          onChange={(e) =>
                            setFormData({ ...formData, height: e.target.value })
                          }
                          className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700"
                          placeholder="Tinggi Badan (cm)"
                        />
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm text-gray-400">
                          cm
                        </div>
                      </div>
                    </div>

                    <div className="group">
                      <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                        Tingkat Aktivitas
                      </label>
                      <div className="relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                          <svg
                            className="w-5 h-5"
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
                        <select
                          value={formData.activity_level}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              activity_level: e.target.value,
                            })
                          }
                          className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700 appearance-none">
                          {activityLevels.map((level) => (
                            <option key={level.value} value={level.value}>
                              {level.label}
                            </option>
                          ))}
                        </select>
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                          <svg
                            className="h-5 w-5 text-gray-400"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 20 20"
                            fill="currentColor">
                            <path
                              fillRule="evenodd"
                              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="group">
                  <label className="block text-sm font-medium text-gray-700 mb-1 group-hover:text-green-700 transition-colors">
                    Kondisi Medis (opsional)
                  </label>
                  <div className="relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 pt-3 pointer-events-none text-gray-400">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M9 12h6m-6 4h6m-6-8h6M5 5a2 2 0 012-2h10a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V5z"
                        />
                      </svg>
                    </div>
                    <textarea
                      value={formData.medical_condition || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          medical_condition: e.target.value,
                        })
                      }
                      rows={4}
                      className="pl-10 focus:ring-green-500 focus:border-green-500 block w-full rounded-lg border-gray-200 shadow-sm py-3 text-gray-700"
                      placeholder="Catatan mengenai kondisi medis Anda (diabetes, hipertensi, alergi makanan, dll)"></textarea>
                  </div>
                </div>

                {/* Interactive BMI Preview */}
                {formData.height && formData.weight && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <h3 className="font-medium text-gray-800 mb-3 flex items-center">
                      <span className="flex items-center justify-center w-6 h-6 bg-green-100 text-green-600 rounded-full mr-2 text-sm">
                        ?
                      </span>
                      Preview BMI Anda
                    </h3>

                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between">
                      <div>
                        <div className="text-3xl font-bold text-gray-800">
                          {(
                            formData.weight /
                            (formData.height / 100) ** 2
                          ).toFixed(1)}
                        </div>
                        <div className="text-sm text-gray-500">
                          {(() => {
                            const bmi =
                              formData.weight / (formData.height / 100) ** 2;
                            if (bmi < 18.5) return "Kekurangan Berat Badan";
                            if (bmi < 25) return "Normal";
                            if (bmi < 30) return "Kelebihan Berat Badan";
                            return "Obesitas";
                          })()}
                        </div>
                      </div>

                      <div className="w-full md:w-2/3 mt-4 md:mt-0">
                        <div className="h-3 bg-gray-200 rounded-full w-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500 ease-in-out"
                            style={{
                              width: `${Math.min(
                                (formData.weight /
                                  (formData.height / 100) ** 2 /
                                  40) *
                                  100,
                                100
                              )}%`,
                              background: `linear-gradient(to right, #3b82f6, #10b981, #f59e0b, #ef4444)`,
                            }}></div>
                        </div>
                        <div className="flex justify-between mt-1 text-xs text-gray-500">
                          <span>18.5</span>
                          <span>25</span>
                          <span>30</span>
                          <span>40</span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                <div className="pt-6 flex items-center justify-between">
                  <motion.button
                    type="button"
                    onClick={() => setEditMode(false)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-5 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-all duration-300 flex items-center space-x-2">
                    <svg
                      className="w-5 h-5"
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
                    <span>Batal</span>
                  </motion.button>

                  <motion.button
                    type="submit"
                    disabled={loading}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    className="px-8 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transition-all duration-300 flex items-center space-x-2 disabled:opacity-70">
                    {loading ? (
                      <>
                        <svg
                          className="animate-spin -ml-1 mr-2 h-5 w-5 text-white"
                          xmlns="http://www.w3.org/2000/svg"
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
                        <span>Memperbarui...</span>
                      </>
                    ) : (
                      <>
                        <svg
                          className="w-5 h-5"
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
                        <span>Simpan Perubahan</span>
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.form>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
