"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DietGoals() {
  const router = useRouter();
  const [activeGoal, setActiveGoal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    target_weight: '',
    target_date: '',
    medical_condition: 'none'
  });

  // Disease conditions with descriptions
  const medicalConditions = [
    { 
      value: 'none',
      label: 'Tidak Ada',
      description: 'Tidak memiliki kondisi medis metabolik khusus'
    },
    {
      value: 'diabetes',
      label: 'Diabetes Mellitus', 
      description: 'Diet dengan pengaturan karbohidrat untuk mengelola kadar gula darah'
    },
    {
      value: 'hypertension',
      label: 'Hipertensi',
      description: 'Diet rendah garam dan lemak untuk mengontrol tekanan darah'
    },
    {
      value: 'obesity',
      label: 'Obesitas',
      description: 'Diet dengan fokus pada kebutuhan kalori dan protein untuk menangani obesitas'
    }
  ];

  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/diet-goals`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!res.ok) throw new Error('Gagal memuat tujuan diet');
      
      const data = await res.json();
      if (data.has_active_goal) {
        setActiveGoal(data.goal);
        setFormData({
          target_weight: data.goal.target_weight,
          target_date: data.goal.target_date,
          medical_condition: data.goal.medical_condition
        });
      }
      setLoading(false);
    } catch (err) {
      setError('Terjadi kesalahan saat memuat data. Silakan coba lagi.');
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const weight = parseFloat(formData.target_weight);
      if (isNaN(weight) || weight < 30 || weight > 200) {
        throw new Error('Berat badan target harus antara 30-200 kg');
      }

      const targetDate = new Date(formData.target_date);
      const today = new Date();
      if (targetDate <= today) {
        throw new Error('Tanggal target harus di masa depan');
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/diet-goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          target_weight: weight,
          target_date: formData.target_date,
          medical_condition: formData.medical_condition || 'none'
        })
      });

      if (!res.ok) throw new Error('Gagal menyimpan tujuan diet');
      
      // Redirect to recommendations page after success
      router.push('/recommendations');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Memuat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            {activeGoal ? 'Tujuan Diet Penurunan Berat Badan Anda' : 'Tetapkan Tujuan Diet Penurunan Berat Badan'}
          </h1>
          <p className="mt-2 text-gray-600">
            {activeGoal 
              ? 'Berikut adalah tujuan diet penurunan berat badan Anda saat ini.'
              : 'Tentukan target penurunan berat badan untuk mendapatkan rekomendasi makanan Indonesia yang sesuai.'}
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
            <div className="flex items-center">
              <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
              </svg>
              <p>{error}</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-xl p-6">
          {activeGoal ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-green-600">Kondisi Medis</h3>
                  <p className="mt-1 text-gray-900">
                    {medicalConditions.find(cond => cond.value === activeGoal.medical_condition)?.label || 'Tidak Ada'}
                  </p>
                  <p className="mt-1 text-sm text-gray-500">
                    {medicalConditions.find(cond => cond.value === activeGoal.medical_condition)?.description}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-green-600">Target Berat Badan</h3>
                  <p className="mt-1 text-gray-900">{activeGoal.target_weight} kg</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-green-600">Target Tanggal</h3>
                  <p className="mt-1 text-gray-900">
                    {new Date(activeGoal.target_date).toLocaleDateString('id-ID', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-green-600">Dibuat Pada</h3>
                  <p className="mt-1 text-gray-900">
                    {new Date(activeGoal.created_at).toLocaleDateString('id-ID', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-4">
                <button
                  type="button"
                  onClick={() => router.push('/recommendations')}
                  className="inline-flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  Lihat Rekomendasi Menu
                </button>
                <button
                  type="button"
                  onClick={() => setActiveGoal(null)}
                  className="inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  Buat Tujuan Diet Baru
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Kondisi Medis (Opsional)
                </label>
                <select
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
                  value={formData.medical_condition}
                  onChange={(e) => setFormData({...formData, medical_condition: e.target.value})}
                >
                  {medicalConditions.map((condition) => (
                    <option key={condition.value} value={condition.value}>
                      {condition.label}
                    </option>
                  ))}
                </select>
                {formData.medical_condition && (
                  <p className="mt-2 text-sm text-gray-500">
                    {medicalConditions.find(cond => cond.value === formData.medical_condition)?.description}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Target Berat Badan (kg)
                  </label>
                  <input
                    type="number"
                    required
                    min="30"
                    max="200"
                    step="0.1"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
                    value={formData.target_weight}
                    onChange={(e) => setFormData({...formData, target_weight: e.target.value})}
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    Masukkan target berat badan antara 30-200 kg
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Target Tanggal
                  </label>
                  <input
                    type="date"
                    required
                    min={new Date(Date.now() + 86400000).toISOString().split('T')[0]}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
                    value={formData.target_date}
                    onChange={(e) => setFormData({...formData, target_date: e.target.value})}
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    Pilih tanggal target pencapaian tujuan diet
                  </p>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                      </svg>
                      Menyimpan...
                    </>
                  ) : 'Simpan dan Lihat Rekomendasi'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}