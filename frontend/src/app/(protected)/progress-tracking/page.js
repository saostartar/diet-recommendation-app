"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export default function ProgressTracking() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [weightData, setWeightData] = useState(null);
  const [caloriesData, setCaloriesData] = useState(null);
  const [nutritionData, setNutritionData] = useState(null);
  const [streakData, setStreakData] = useState(null);
  const [newWeight, setNewWeight] = useState('');
  const [weightSubmitLoading, setWeightSubmitLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('weight');
  const [timeRange, setTimeRange] = useState(7); // Default 7 days

  useEffect(() => {
    fetchAllData();
  }, [timeRange]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchWeightData(),
        fetchCaloriesData(),
        fetchNutritionData(),
        fetchStreakData()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchWeightData = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/progress/weight`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!res.ok) throw new Error('Gagal memuat data berat badan');
    const data = await res.json();
    setWeightData(data);
    return data;
  };

  const fetchCaloriesData = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/progress/calories?days=${timeRange}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!res.ok) throw new Error('Gagal memuat data kalori');
    const data = await res.json();
    setCaloriesData(data);
    return data;
  };

  const fetchNutritionData = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/progress/nutrition`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!res.ok) throw new Error('Gagal memuat data nutrisi');
    const data = await res.json();
    setNutritionData(data);
    return data;
  };

  const fetchStreakData = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/progress/streak`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!res.ok) throw new Error('Gagal memuat data streak');
    const data = await res.json();
    setStreakData(data);
    return data;
  };

  const handleSubmitWeight = async (e) => {
    e.preventDefault();
    setWeightSubmitLoading(true);
    setError('');

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/progress/weight`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ weight: parseFloat(newWeight) })
      });

      if (!res.ok) throw new Error('Gagal menyimpan berat badan');
      
      await fetchWeightData();
      setNewWeight('');
    } catch (err) {
      setError(err.message);
    } finally {
      setWeightSubmitLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
  };

  // Prepare chart data
  const weightChartData = {
    labels: weightData?.progress.map(p => formatDate(p.date)) || [],
    datasets: [
      {
        label: 'Berat (kg)',
        data: weightData?.progress.map(p => p.weight) || [],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        tension: 0.3,
      }
    ]
  };

  const caloriesChartData = {
    labels: caloriesData?.map(day => formatDate(day.date)) || [],
    datasets: [
      {
        label: 'Kalori (kkal)',
        data: caloriesData?.map(day => day.calories) || [],
        backgroundColor: 'rgba(99, 102, 241, 0.6)',
        borderColor: 'rgb(99, 102, 241)',
        borderWidth: 1
      }
    ]
  };

  const nutritionChartData = {
    labels: ['Protein', 'Karbohidrat', 'Lemak'],
    datasets: [
      {
        data: nutritionData ? [
          nutritionData.daily_average.protein,
          nutritionData.daily_average.carbs,
          nutritionData.daily_average.fat
        ] : [0, 0, 0],
        backgroundColor: [
          'rgba(255, 99, 132, 0.7)',
          'rgba(54, 162, 235, 0.7)',
          'rgba(255, 206, 86, 0.7)'
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)'
        ],
        borderWidth: 1
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  // Calculate progress percentage
  const calculateWeightProgress = () => {
    if (!weightData?.starting_weight || !weightData?.target_weight) return 0;
    
    const totalToLose = weightData.starting_weight - weightData.target_weight;
    const lost = weightData.starting_weight - weightData.current_weight;
    
    if (totalToLose <= 0) return 0; // Handle weight gain goals differently
    
    return Math.min(100, Math.round((lost / totalToLose) * 100));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Pelacakan Kemajuan</h1>
          <p className="mt-2 text-gray-600">
            Pantau perkembangan diet dan kesehatan Anda dari waktu ke waktu
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 text-red-500 p-4 rounded-lg">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Weight Card */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">Berat Badan</h3>
              <span className="text-sm text-gray-500">Saat ini</span>
            </div>
            <div className="flex items-end">
              <span className="text-3xl font-bold text-green-600">
                {weightData?.current_weight || '-'} kg
              </span>
            </div>
            <div className="mt-2">
              <span className="text-sm text-gray-600">Target: {weightData?.target_weight || '-'} kg</span>
            </div>
            <div className="mt-3 h-2.5 w-full bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500 rounded-full"
                style={{ width: `${calculateWeightProgress()}%` }}
              ></div>
            </div>
            <div className="mt-1 text-xs text-gray-500 text-right">
              {calculateWeightProgress()}% dari target
            </div>
          </div>

          {/* Calories Card */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">Konsumsi Kalori</h3>
              <span className="text-sm text-gray-500">Hari ini</span>
            </div>
            <div className="flex items-end">
              <span className="text-3xl font-bold text-indigo-600">
                {caloriesData && caloriesData[caloriesData.length - 1]?.calories || 0} kkal
              </span>
            </div>
            <div className="mt-2">
              <span className="text-sm text-gray-600">
                Rata-rata {timeRange} hari: {caloriesData ? 
                  Math.round(caloriesData.reduce((sum, day) => sum + day.calories, 0) / caloriesData.length) : 0
                } kkal
              </span>
            </div>
          </div>

          {/* Streak Card */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">Konsistensi</h3>
              <span className="text-sm text-gray-500">Streak</span>
            </div>
            <div className="flex items-end">
              <span className="text-3xl font-bold text-yellow-500">
                {streakData?.current_streak || 0} hari
              </span>
            </div>
            <div className="mt-2">
              <span className="text-sm text-gray-600">
                Streak terlama: {streakData?.longest_streak || 0} hari
              </span>
            </div>
            <div className="mt-3 flex">
              {[...Array(7)].map((_, i) => (
                <div key={i} className={`h-6 w-5 mx-0.5 rounded-sm ${
                  i < (streakData?.current_streak % 7) ? 'bg-yellow-500' : 'bg-gray-200'
                }`}></div>
              ))}
            </div>
          </div>

          {/* Nutrition Card */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">Nutrisi Harian</h3>
              <span className="text-sm text-gray-500">Rata-rata</span>
            </div>
            <div className="space-y-2 mt-2">
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span>Protein</span>
                  <span className="font-medium">{nutritionData?.daily_average.protein || 0}g</span>
                </div>
                <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: '70%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span>Karbohidrat</span>
                  <span className="font-medium">{nutritionData?.daily_average.carbs || 0}g</span>
                </div>
                <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: '60%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span>Lemak</span>
                  <span className="font-medium">{nutritionData?.daily_average.fat || 0}g</span>
                </div>
                <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500 rounded-full" style={{ width: '40%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Weight Input Form */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Perbarui Berat Badan Anda</h2>
          <form onSubmit={handleSubmitWeight} className="flex flex-col sm:flex-row items-end gap-4">
            <div className="w-full sm:w-64">
              <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-1">
                Berat Badan (kg)
              </label>
              <input
                type="number"
                id="weight"
                required
                step="0.1"
                min="30"
                max="200"
                value={newWeight}
                onChange={(e) => setNewWeight(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:ring-green-500 focus:border-green-500"
                placeholder="Masukkan berat badan"
              />
            </div>
            <button
              type="submit"
              disabled={weightSubmitLoading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400"
            >
              {weightSubmitLoading ? 'Menyimpan...' : 'Simpan Berat Badan'}
            </button>
          </form>
        </div>

        {/* Tabs */}
        <div className="mb-4">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-6">
              <button
                onClick={() => setActiveTab('weight')}
                className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'weight'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Berat Badan
              </button>
              <button
                onClick={() => setActiveTab('calories')}
                className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'calories'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Kalori
              </button>
              <button
                onClick={() => setActiveTab('nutrition')}
                className={`pb-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'nutrition'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Nutrisi
              </button>
            </nav>
          </div>
        </div>

        {/* Time Range Selector (for calories tab) */}
        {activeTab === 'calories' && (
          <div className="flex justify-end mb-4">
            <div className="inline-flex rounded-md shadow-sm" role="group">
              <button
                type="button"
                onClick={() => setTimeRange(7)}
                className={`px-4 py-2 text-sm font-medium ${
                  timeRange === 7 
                    ? 'bg-green-600 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                } border border-gray-200 rounded-l-lg`}
              >
                7 Hari
              </button>
              <button
                type="button"
                onClick={() => setTimeRange(14)}
                className={`px-4 py-2 text-sm font-medium ${
                  timeRange === 14 
                    ? 'bg-green-600 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                } border border-gray-200`}
              >
                14 Hari
              </button>
              <button
                type="button"
                onClick={() => setTimeRange(30)}
                className={`px-4 py-2 text-sm font-medium ${
                  timeRange === 30 
                    ? 'bg-green-600 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                } border border-gray-200 rounded-r-lg`}
              >
                30 Hari
              </button>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          {activeTab === 'weight' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Tren Berat Badan</h2>
                <div className="text-sm text-gray-500">30 hari terakhir</div>
              </div>
              {weightData?.progress.length > 0 ? (
                <div className="h-80">
                  <Line data={weightChartData} options={chartOptions} />
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-60 text-gray-500">
                  <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                  <p>Belum ada data berat badan</p>
                  <p className="text-sm">Perbarui berat badan Anda untuk melihat grafiknya</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'calories' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Konsumsi Kalori</h2>
                <div className="text-sm text-gray-500">
                  {timeRange} hari terakhir
                </div>
              </div>
              {caloriesData && caloriesData.some(day => day.calories > 0) ? (
                <div className="h-80">
                  <Bar data={caloriesChartData} options={chartOptions} />
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-60 text-gray-500">
                  <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <p>Belum ada data konsumsi makanan</p>
                  <p className="text-sm">Tandai rekomendasi makanan yang sudah Anda konsumsi</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'nutrition' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Komposisi Nutrisi</h2>
                <div className="text-sm text-gray-500">Rata-rata harian</div>
              </div>
              {nutritionData && (
                nutritionData.daily_average.protein > 0 || 
                nutritionData.daily_average.carbs > 0 || 
                nutritionData.daily_average.fat > 0
              ) ? (
                <div className="flex flex-col md:flex-row">
                  <div className="w-full md:w-1/2 h-80">
                    <Doughnut data={nutritionChartData} options={{...chartOptions, cutout: '70%'}} />
                  </div>
                  <div className="w-full md:w-1/2 p-4">
                    <div className="mb-6">
                      <h3 className="text-base font-medium text-gray-900 mb-2">Rata-rata Konsumsi Harian</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-red-50 p-3 rounded-lg">
                          <div className="text-xs text-red-700 mb-1">Protein</div>
                          <div className="text-lg font-semibold text-red-600">{nutritionData.daily_average.protein || 0}g</div>
                        </div>
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <div className="text-xs text-blue-700 mb-1">Karbo</div>
                          <div className="text-lg font-semibold text-blue-600">{nutritionData.daily_average.carbs || 0}g</div>
                        </div>
                        <div className="bg-yellow-50 p-3 rounded-lg">
                          <div className="text-xs text-yellow-700 mb-1">Lemak</div>
                          <div className="text-lg font-semibold text-yellow-600">{nutritionData.daily_average.fat || 0}g</div>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-medium text-gray-900 mb-2">Total Mingguan</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <div className="text-xs text-gray-700 mb-1">Protein</div>
                          <div className="text-lg font-semibold text-gray-700">{nutritionData.weekly_total.protein || 0}g</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <div className="text-xs text-gray-700 mb-1">Karbo</div>
                          <div className="text-lg font-semibold text-gray-700">{nutritionData.weekly_total.carbs || 0}g</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <div className="text-xs text-gray-700 mb-1">Lemak</div>
                          <div className="text-lg font-semibold text-gray-700">{nutritionData.weekly_total.fat || 0}g</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-60 text-gray-500">
                  <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                  <p>Belum ada data nutrisi</p>
                  <p className="text-sm">Tandai rekomendasi makanan yang sudah Anda konsumsi</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}