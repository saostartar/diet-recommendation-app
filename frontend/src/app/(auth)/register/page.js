"use client";
import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

export default function Register() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    age: '',
    weight: '',
    height: '',
    gender: '',
    activity_level: '',
    medical_condition: 'none'
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  // Updated to match the backend enum values
  const activityLevels = [
    { value: 'sedentary', label: 'Tidak Aktif (Jarang Berolahraga)' },
    { value: 'light', label: 'Ringan (1-3x Olahraga/Minggu)' },
    { value: 'moderate', label: 'Sedang (3-5x Olahraga/Minggu)' },
    { value: 'active', label: 'Aktif (6-7x Olahraga/Minggu)' },
    { value: 'very_active', label: 'Sangat Aktif (Atlet/Pekerja Fisik)' }
  ];

  // Medical conditions matching the backend model
  const medicalConditions = [
    { value: 'none', label: 'Tidak Ada Kondisi Medis' },
    { value: 'diabetes', label: 'Diabetes' },
    { value: 'hypertension', label: 'Hipertensi' },
    { value: 'obesity', label: 'Obesitas' }
  ];

  // Client-side validation functions
  const validateStep1 = () => {
    const newErrors = {};

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Nama pengguna wajib diisi';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Nama pengguna minimal 3 karakter';
    } else if (formData.username.length > 50) {
      newErrors.username = 'Nama pengguna maksimal 50 karakter';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Nama pengguna hanya boleh mengandung huruf, angka, dan underscore';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email wajib diisi';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Format email tidak valid';
    } else if (formData.email.length > 100) {
      newErrors.email = 'Email maksimal 100 karakter';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Kata sandi wajib diisi';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Kata sandi minimal 8 karakter';
    } else if (!/(?=.*[A-Za-z])/.test(formData.password)) {
      newErrors.password = 'Kata sandi harus mengandung minimal satu huruf';
    } else if (!/(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Kata sandi harus mengandung minimal satu angka';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Konfirmasi kata sandi wajib diisi';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Konfirmasi kata sandi tidak cocok';
    }

    return newErrors;
  };

  const validateStep2 = () => {
    const newErrors = {};

    // Age validation
    const age = parseInt(formData.age);
    if (!formData.age) {
      newErrors.age = 'Usia wajib diisi';
    } else if (isNaN(age) || age < 18 || age > 65) {
      newErrors.age = 'Usia harus antara 12-100 tahun';
    }

    // Weight validation
    const weight = parseFloat(formData.weight);
    if (!formData.weight) {
      newErrors.weight = 'Berat badan wajib diisi';
    } else if (isNaN(weight) || weight < 30 || weight > 300) {
      newErrors.weight = 'Berat badan harus antara 30-300 kg';
    }

    // Height validation
    const height = parseFloat(formData.height);
    if (!formData.height) {
      newErrors.height = 'Tinggi badan wajib diisi';
    } else if (isNaN(height) || height < 100 || height > 250) {
      newErrors.height = 'Tinggi badan harus antara 100-250 cm';
    }

    // Gender validation
    if (!formData.gender) {
      newErrors.gender = 'Jenis kelamin wajib dipilih';
    }

    // Activity level validation
    if (!formData.activity_level) {
      newErrors.activity_level = 'Tingkat aktivitas wajib dipilih';
    }

    return newErrors;
  };

  const handleNextStep = () => {
    const step1Errors = validateStep1();
    setErrors(step1Errors);
    
    if (Object.keys(step1Errors).length === 0) {
      setCurrentStep(2);
    }
  };

  const handlePrevStep = () => {
    setCurrentStep(1);
    setErrors({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Validate step 2
    const step2Errors = validateStep2();
    setErrors(step2Errors);

    if (Object.keys(step2Errors).length > 0) {
      setLoading(false);
      return;
    }

    try {
      // Register the user
      const registerRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          age: parseInt(formData.age),
          weight: parseFloat(formData.weight),
          height: parseFloat(formData.height),
          medical_condition: formData.medical_condition === 'none' ? '' : formData.medical_condition
        }),
      });

      const registerData = await registerRes.json();

      if (!registerRes.ok) {
        if (registerData.errors) {
          // Handle validation errors from backend
          const backendErrors = {};
          registerData.errors.forEach(error => {
            // Map backend errors to form fields
            if (error.includes('username') || error.includes('Nama pengguna')) {
              backendErrors.username = error;
            } else if (error.includes('email') || error.includes('Email')) {
              backendErrors.email = error;
            } else if (error.includes('password') || error.includes('Kata sandi')) {
              backendErrors.password = error;
            } else if (error.includes('age') || error.includes('Usia')) {
              backendErrors.age = error;
            } else if (error.includes('weight') || error.includes('Berat')) {
              backendErrors.weight = error;
            } else if (error.includes('height') || error.includes('Tinggi')) {
              backendErrors.height = error;
            } else if (error.includes('gender') || error.includes('Jenis kelamin')) {
              backendErrors.gender = error;
            } else if (error.includes('activity') || error.includes('aktivitas')) {
              backendErrors.activity_level = error;
            }
          });
          setErrors(backendErrors);
        } else {
          setErrors({ general: registerData.message || 'Terjadi kesalahan saat mendaftar' });
        }
        setLoading(false);
        return;
      }

      // Automatically login after successful registration
      const loginRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      const loginData = await loginRes.json();

      if (!loginRes.ok) {
        throw new Error(loginData.message || 'Terjadi kesalahan saat login otomatis');
      }

      // Store the token
      localStorage.setItem('token', loginData.access_token);
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setErrors({ general: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-green-50 via-white to-emerald-50 relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-40 left-20 w-80 h-80 bg-green-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
      <div className="absolute -bottom-10 right-1/4 w-80 h-80 bg-blue-100 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" style={{animationDelay: "2s"}}></div>
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-4xl w-full space-y-8 relative z-10"
      >
        <div className="text-center">
          <motion.div 
            initial={{ scale: 0.96 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
            className="mx-auto h-16 w-16 rounded-full bg-gradient-to-r from-green-600 to-green-700 text-white flex items-center justify-center shadow-lg shadow-green-200 mb-6"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          </motion.div>

          <motion.h2 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-3xl font-bold text-gray-900 mb-2"
          >
            Mulai Perjalanan Diet Sehat Anda
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-lg text-gray-600 max-w-xl mx-auto"
          >
            Buat akun untuk mendapatkan rekomendasi diet yang disesuaikan dengan kebutuhan Anda.
          </motion.p>
        </div>

        {errors.general && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl shadow-sm flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-red-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {errors.general}
          </motion.div>
        )}

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden"
        >
          <div className="py-6 px-8 bg-gradient-to-r from-green-600 to-green-700 flex justify-between items-center">
            <h3 className="text-xl font-bold text-white">
              {currentStep === 1 ? 'Informasi Akun' : 'Detail Pribadi'}
            </h3>
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full ${currentStep === 1 ? 'bg-white' : 'bg-white/60'} flex items-center justify-center`}>
                <span className="text-xs text-green-700 font-semibold">1</span>
              </div>
              <div className={`w-8 h-0.5 ${currentStep === 1 ? 'bg-white/60' : 'bg-white'}`}></div>
              <div className={`w-4 h-4 rounded-full ${currentStep === 2 ? 'bg-white' : 'bg-white/60'} flex items-center justify-center`}>
                <span className="text-xs text-green-700 font-semibold">2</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-8">
            {currentStep === 1 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                    Nama Pengguna *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <input
                      type="text"
                      name="username"
                      id="username"
                      required
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.username ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="Masukkan nama pengguna"
                      value={formData.username}
                      onChange={(e) => setFormData({...formData, username: e.target.value})}
                    />
                  </div>
                  {errors.username && <p className="text-red-600 text-sm">{errors.username}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Alamat Email *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                      </svg>
                    </div>
                    <input
                      type="email"
                      name="email"
                      id="email"
                      required
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.email ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="nama@email.com"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                  {errors.email && <p className="text-red-600 text-sm">{errors.email}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                    Kata Sandi *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </div>
                    <input
                      type="password"
                      name="password"
                      id="password"
                      required
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.password ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="Minimal 8 karakter dengan huruf dan angka"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                    />
                  </div>
                  {errors.password && <p className="text-red-600 text-sm">{errors.password}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                    Konfirmasi Kata Sandi *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <input
                      type="password"
                      name="confirmPassword"
                      id="confirmPassword"
                      required
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.confirmPassword ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="Konfirmasi kata sandi"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                    />
                  </div>
                  {errors.confirmPassword && <p className="text-red-600 text-sm">{errors.confirmPassword}</p>}
                </div>

                <div className="md:col-span-2 flex justify-end mt-4">
                  <button
                    type="button"
                    onClick={handleNextStep}
                    className="inline-flex items-center justify-center px-6 py-3 rounded-xl text-white bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 shadow-md hover:shadow-lg transform transition-all duration-200 hover:-translate-y-0.5"
                  >
                    Selanjutnya
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="age" className="block text-sm font-medium text-gray-700">
                    Usia *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <input
                      type="number"
                      name="age"
                      id="age"
                      required
                      min="18"
                      max="65"
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.age ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="Usia (12-100 tahun)"
                      value={formData.age}
                      onChange={(e) => setFormData({...formData, age: e.target.value})}
                    />
                  </div>
                  {errors.age && <p className="text-red-600 text-sm">{errors.age}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="gender" className="block text-sm font-medium text-gray-700">
                    Jenis Kelamin *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <select
                      id="gender"
                      name="gender"
                      required
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.gender ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors appearance-none`}
                      value={formData.gender}
                      onChange={(e) => setFormData({...formData, gender: e.target.value})}
                    >
                      <option value="">Pilih Jenis Kelamin</option>
                      <option value="M">Laki-laki</option>
                      <option value="F">Perempuan</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  {errors.gender && <p className="text-red-600 text-sm">{errors.gender}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="weight" className="block text-sm font-medium text-gray-700">
                    Berat Badan (kg) *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                      </svg>
                    </div>
                    <input
                      type="number"
                      name="weight"
                      id="weight"
                      required
                      step="0.1"
                      min="30"
                      max="300"
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.weight ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="Berat badan (30-300 kg)"
                      value={formData.weight}
                      onChange={(e) => setFormData({...formData, weight: e.target.value})}
                    />
                  </div>
                  {errors.weight && <p className="text-red-600 text-sm">{errors.weight}</p>}
                </div>

                <div className="space-y-2">
                  <label htmlFor="height" className="block text-sm font-medium text-gray-700">
                    Tinggi Badan (cm) *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                    </div>
                    <input
                      type="number"
                      name="height"
                      id="height"
                      required
                      step="0.1"
                      min="100"
                      max="250"
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.height ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors`}
                      placeholder="Tinggi badan (100-250 cm)"
                      value={formData.height}
                      onChange={(e) => setFormData({...formData, height: e.target.value})}
                    />
                  </div>
                  {errors.height && <p className="text-red-600 text-sm">{errors.height}</p>}
                </div>

                <div className="md:col-span-2 space-y-2">
                  <label htmlFor="activity_level" className="block text-sm font-medium text-gray-700">
                    Tingkat Aktivitas *
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <select
                      id="activity_level"
                      name="activity_level"
                      required
                      className={`pl-10 w-full px-4 py-3 bg-gray-50 border ${errors.activity_level ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors appearance-none`}
                      value={formData.activity_level}
                      onChange={(e) => setFormData({...formData, activity_level: e.target.value})}
                    >
                      <option value="">Pilih Tingkat Aktivitas</option>
                      {activityLevels.map((level) => (
                        <option key={level.value} value={level.value}>
                          {level.label}
                        </option>
                      ))}
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  {errors.activity_level && <p className="text-red-600 text-sm">{errors.activity_level}</p>}
                </div>

                <div className="md:col-span-2 space-y-2">
                  <label htmlFor="medical_condition" className="block text-sm font-medium text-gray-700">
                    Kondisi Medis
                  </label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m-6-8h6M5 5a2 2 0 012-2h10a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V5z" />
                      </svg>
                    </div>
                    <select
                      id="medical_condition"
                      name="medical_condition"
                      className="pl-10 w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors appearance-none"
                      value={formData.medical_condition}
                      onChange={(e) => setFormData({...formData, medical_condition: e.target.value})}
                    >
                      {medicalConditions.map((condition) => (
                        <option key={condition.value} value={condition.value}>
                          {condition.label}
                        </option>
                      ))}
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500">
                    Pilih kondisi medis yang sesuai untuk mendapatkan rekomendasi diet yang tepat
                  </p>
                </div>

                <div className="md:col-span-2 flex justify-between mt-4">
                  <button
                    type="button"
                    onClick={handlePrevStep}
                    className="inline-flex items-center justify-center px-6 py-3 rounded-xl text-green-700 bg-white border border-green-500 hover:bg-green-50 shadow-sm transform transition-all duration-200 hover:-translate-y-0.5"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 10l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
                    </svg>
                    Kembali
                  </button>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="inline-flex items-center justify-center px-8 py-3 rounded-xl text-white bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 shadow-md hover:shadow-xl transform transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-70"
                  >
                    {loading ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                        </svg>
                        Mendaftar...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        Buat Akun
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                        </svg>
                      </span>
                    )}
                  </button>
                </div>
              </div>
            )}
          </form>
        </motion.div>
        
        <p className="text-center text-sm text-gray-600">
          Sudah memiliki akun?{' '}
          <Link href="/login" className="font-medium text-green-600 hover:text-green-700 transition-colors">
            Masuk di sini
          </Link>
        </p>
        
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="text-center text-xs text-gray-500 mt-8"
        >
          Dengan mendaftar, Anda menyetujui <a href="#" className="underline hover:text-green-600">Syarat & Ketentuan</a> dan <a href="#" className="underline hover:text-green-600">Kebijakan Privasi</a> kami.
        </motion.div>
      </motion.div>
    </div>
  );
}