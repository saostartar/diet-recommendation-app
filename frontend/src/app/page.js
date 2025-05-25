"use client"
import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <>
      {/* Hero Section - Modernized */}
      <section className="py-20 md:py-28 px-4 md:px-8 overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="lg:w-1/2 space-y-6 z-10"
            >
              <h1 className="text-4xl md:text-5xl font-bold leading-tight bg-clip-text text-transparent bg-gradient-to-r from-green-700 to-green-900">
                Selamat Datang di Sistem Rekomendasi Diet
              </h1>
              <p className="text-lg text-gray-600">
                Dapatkan rekomendasi makanan sehat dan rencana diet personal yang disesuaikan dengan kebutuhan dan tujuan Anda.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <Link href="/register" className="group relative overflow-hidden rounded-lg btn-primary shadow-lg shadow-green-600/20">
                  <span className="absolute inset-0 bg-gradient-to-r from-green-400 to-green-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
                  <span className="relative z-10">Mulai Sekarang</span>
                </Link>
                <Link href="/learn" className="btn-secondary hover:shadow-md transform hover:scale-105 transition-transform duration-200">
                  Pelajari Lebih Lanjut
                </Link>
              </div>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:w-1/2 relative"
            >
              <div className="absolute -top-20 -left-20 w-64 h-64 bg-green-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
              <div className="absolute -bottom-8 -right-20 w-64 h-64 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
              <div className="aspect-video w-full relative rounded-2xl overflow-hidden shadow-2xl transform hover:scale-[0.98] transition-transform duration-500 bg-gradient-to-r from-green-50 to-green-100 p-1">
                <div className="rounded-xl overflow-hidden h-full">
                  <Image 
                    src="/images/hero-section.png"
                    alt="Makanan sehat"
                    fill
                    className="object-cover"
                    priority
                  />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section - Modernized */}
      <section className="py-20 bg-gradient-to-b from-green-50 to-white px-4 md:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="bg-green-100 text-green-800 text-sm font-medium px-4 py-1.5 rounded-full inline-block mb-4">Fitur Unggulan</span>
            <h2 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-green-700 to-green-900 mb-4">
              Fitur Utama
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Sistem rekomendasi diet kami menggunakan pendekatan personalisasi untuk membantu Anda mencapai tujuan diet dan kesehatan.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                key={index} 
                className="bg-white rounded-xl border border-gray-100 shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 p-6 group"
              >
                <div className="w-14 h-14 flex items-center justify-center rounded-lg bg-gradient-to-br from-green-400 to-green-600 text-white mb-6 transform group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works - Modernized */}
      <section className="py-20 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <span className="bg-blue-100 text-blue-800 text-sm font-medium px-4 py-1.5 rounded-full inline-block mb-4">Proses Sederhana</span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Bagaimana Cara Kerjanya
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Dalam 4 langkah sederhana, Anda akan mendapatkan rekomendasi diet yang sesuai dengan kebutuhan Anda.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <motion.div 
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: index * 0.2 }}
              viewport={{ once: true }}
              key={index} 
              className="flex flex-col items-center text-center relative"
            >
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-8 left-[60%] w-full h-0.5 bg-gradient-to-r from-green-300 to-green-100"></div>
              )}
              <div className="w-16 h-16 mb-6 rounded-full bg-gradient-to-br from-green-600 to-green-700 text-white flex items-center justify-center text-2xl font-bold shadow-lg shadow-green-200 z-10">
                {index + 1}
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">{step.title}</h3>
              <p className="text-gray-600">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Testimonials - Modernized */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white px-4 md:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="bg-purple-100 text-purple-800 text-sm font-medium px-4 py-1.5 rounded-full inline-block mb-4">Pendapat Pengguna</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Testimoni Pengguna
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Lihat apa kata pengguna tentang sistem rekomendasi diet kami.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: index * 0.15 }}
                viewport={{ once: true }}
                key={index} 
                className="bg-white p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-50"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-green-600 p-1 shadow-inner overflow-hidden">
                    <div className="rounded-full overflow-hidden h-full w-full relative">
                      <Image
                        src={testimonial.avatar}
                        alt={testimonial.name}
                        fill
                        className="object-cover"
                      />
                    </div>
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 text-lg">{testimonial.name}</h4>
                    <p className="text-sm text-green-600">{testimonial.title}</p>
                  </div>
                </div>
                <div className="relative">
                  <svg className="absolute -top-3 -left-2 w-8 h-8 text-green-100" fill="currentColor" viewBox="0 0 32 32">
                    <path d="M10 8c-2.2 0-4 1.8-4 4v10c0 2.2 1.8 4 4 4h10c2.2 0 4-1.8 4-4v-6.586l6.293-6.293c0.391-0.391 0.391-1.023 0-1.414s-1.023-0.391-1.414 0l-4.879 4.879v-0.586c0-2.2-1.8-4-4-4h-10zM10 10h10c1.103 0 2 0.897 2 2v10c0 1.103-0.897 2-2 2h-10c-1.103 0-2-0.897-2-2v-10c0-1.103 0.897-2 2-2z"></path>
                  </svg>
                  <p className="text-gray-600 italic leading-relaxed">{testimonial.quote}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section - Modernized */}
      <section className="py-20 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-green-600 to-green-900 rounded-3xl p-8 md:p-12 shadow-2xl overflow-hidden relative">
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 -mt-20 -mr-20 w-80 h-80 rounded-full bg-green-500 opacity-20"></div>
          <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-80 h-80 rounded-full bg-green-700 opacity-20"></div>
          
          <div className="relative z-10 text-center">
            <motion.h2 
              initial={{ opacity: 0, y: -20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="text-3xl md:text-4xl font-bold text-white mb-6 leading-tight"
            >
              Mulai Perjalanan Diet Anda Sekarang
            </motion.h2>
            <motion.p 
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              viewport={{ once: true }}
              className="text-xl text-green-100 max-w-3xl mx-auto mb-10"
            >
              Daftar sekarang dan dapatkan rekomendasi diet yang dipersonalisasi untuk kebutuhan Anda.
            </motion.p>
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              viewport={{ once: true }}
              className="flex flex-col sm:flex-row justify-center gap-5"
            >
              <Link href="/register" className="bg-white hover:bg-green-50 text-green-800 font-semibold py-4 px-8 rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-300">
                Daftar Sekarang
              </Link>
              <Link href="/login" className="bg-transparent border-2 border-white/30 hover:bg-white/10 text-white font-semibold py-4 px-8 rounded-xl transform hover:-translate-y-0.5 transition-all duration-300">
                Masuk
              </Link>
            </motion.div>
          </div>
        </div>
      </section>
    </>
  );
}

// Data for the features section
const features = [
  {
    icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path></svg>,
    title: "Personalisasi Diet",
    description: "Dapatkan rekomendasi diet yang disesuaikan dengan kebutuhan, preferensi, dan tujuan kesehatan Anda."
  },
  {
    icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"></path></svg>,
    title: "Perencanaan Menu",
    description: "Dapatkan menu harian dan mingguan yang seimbang dan sesuai dengan kebutuhan kalori dan nutrisi Anda."
  },
  {
    icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z" clipRule="evenodd"></path></svg>,
    title: "Analisis Nutrisi",
    description: "Pantau asupan nutrisi dan kalori Anda dengan analisis rinci tentang makanan yang Anda konsumsi."
  },
  {
    icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd"></path></svg>,
    title: "Pelacakan Kemajuan",
    description: "Pantau kemajuan diet Anda dengan grafik dan statistik yang mudah dipahami."
  },
];

// Data for the steps section
const steps = [
  {
    title: "Buat Profil",
    description: "Isi informasi dasar tentang usia, berat, tinggi, dan tingkat aktivitas Anda."
  },
  {
    title: "Tetapkan Tujuan",
    description: "Pilih tujuan diet Anda, seperti menurunkan berat badan, menambah massa otot, atau menjaga kesehatan."
  },
  {
    title: "Dapatkan Rekomendasi",
    description: "Terima rencana diet dan rekomendasi makanan yang disesuaikan dengan kebutuhan Anda."
  },
  {
    title: "Pantau Kemajuan",
    description: "Lacak kemajuan dan perbarui rencana diet Anda sesuai kebutuhan untuk hasil optimal."
  }
];

// Data for the testimonials section
const testimonials = [
  {
    name: "Budi Santoso",
    title: "Pengguna sejak 2023",
    avatar: "/images/avatar-1.jpg",
    quote: "Sistem rekomendasi diet ini sangat membantu saya menurunkan 10kg dalam 3 bulan dengan cara yang sehat dan berkelanjutan."
  },
  {
    name: "Siti Rahayu",
    title: "Pengguna sejak 2022",
    avatar: "/images/avatar-2.jpg",
    quote: "Saya suka bagaimana sistem ini memberikan resep yang bervariasi dan sesuai dengan preferensi makanan saya."
  },
  {
    name: "Ahmad Hidayat",
    title: "Pengguna sejak 2023",
    avatar: "/images/avatar-3.jpg",
    quote: "Sebagai atlet, saya membutuhkan diet khusus untuk performa. Sistem ini memberikan rekomendasi nutrisi yang tepat untuk kebutuhan latihan saya."
  }
];