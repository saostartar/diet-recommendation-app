"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

export default function Navbar() {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <nav className={`fixed w-full z-50 transition-all duration-300 ${
      scrolled ? 'bg-white/90 backdrop-blur-md shadow-lg' : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="flex justify-between h-20">
          <Link href="/" className="flex items-center gap-3">
            <div className="relative w-10 h-10 overflow-hidden rounded-full bg-gradient-to-br from-green-400 to-green-600 p-0.5">
              <div className="absolute inset-0 w-full h-full bg-white rounded-full transform scale-[0.96]"></div>
              <div className="relative w-full h-full flex items-center justify-center">
                <Image
                  src="/images/logo.png"
                  alt="Logo Diet Recommendation"
                  width={100}
                  height={100}
                  className="object-contain"
                />
              </div>
            </div>
            <div>
              <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-green-800 text-xl">DietPlan</span>
              <span className="hidden sm:block text-xs text-gray-500 -mt-1">Rekomendasi Diet Sehat</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {isAuthenticated ? (
              <div className="flex items-center space-x-1">
                <div className="bg-gray-50 rounded-full p-1 flex space-x-1">
                  <Link
                    href="/dashboard"
                    className="py-2 px-4 text-gray-600 hover:text-green-700 rounded-full transition-all duration-300 hover:bg-white hover:shadow-sm">
                    Dashboard
                  </Link>
                  <Link
                    href="/recommendations"
                    className="py-2 px-4 text-gray-600 hover:text-green-700 rounded-full transition-all duration-300 hover:bg-white hover:shadow-sm">
                    Rekomendasi
                  </Link>
                  <Link
                    href="/progress-tracking"
                    className="py-2 px-4 text-gray-600 hover:text-green-700 rounded-full transition-all duration-300 hover:bg-white hover:shadow-sm">
                    Progress
                  </Link>
                </div>
                
                <div className="flex items-center space-x-2 ml-2">
                  <div className="relative group">
                    <button className="flex items-center space-x-1 bg-white rounded-full py-2 px-4 shadow-sm hover:shadow-md transition-all duration-300">
                      <span className="text-gray-700">Akun</span>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-2xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 transform origin-top-right">
                      <div className="py-2">
                        <Link href="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-green-50 hover:text-green-700">
                          <div className="flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            Profil Saya
                          </div>
                        </Link>
                        <Link href="/diet-goals" className="block px-4 py-2 text-sm text-gray-700 hover:bg-green-50 hover:text-green-700">
                          <div className="flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                            Tujuan Diet
                          </div>
                        </Link>
                        <div className="border-t border-gray-100 my-1"></div>
                        <button 
                          onClick={handleLogout} 
                          className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                        >
                          <div className="flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                            Keluar
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  href="/login"
                  className="py-2 px-5 text-gray-600 hover:text-green-700 border border-transparent hover:border-green-200 rounded-full transition-all duration-300">
                  Masuk
                </Link>
                <Link
                  href="/register"
                  className="py-2 px-5 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-full shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-300">
                  Daftar
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="rounded-full p-2 text-gray-500 hover:text-green-700 hover:bg-gray-100 focus:outline-none transition-colors">
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor">
                {isMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden bg-white border-t border-gray-100 shadow-lg overflow-hidden"
          >
            <div className="px-4 py-3 space-y-2">
              {isAuthenticated ? (
                <>
                  <div className="bg-gray-50 rounded-xl p-3 mb-4">
                    <div className="text-sm font-medium text-gray-500 mb-2">Menu Utama</div>
                    <Link
                      href="/dashboard"
                      className="flex items-center py-2.5 px-3 text-gray-700 hover:bg-white hover:shadow-sm hover:text-green-700 rounded-lg transition-all">
                      <svg className="w-5 h-5 mr-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                      </svg>
                      Dashboard
                    </Link>
                    <Link
                      href="/recommendations"
                      className="flex items-center py-2.5 px-3 text-gray-700 hover:bg-white hover:shadow-sm hover:text-green-700 rounded-lg transition-all">
                      <svg className="w-5 h-5 mr-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      Rekomendasi Menu
                    </Link>
                    <Link
                      href="/progress-tracking"
                      className="flex items-center py-2.5 px-3 text-gray-700 hover:bg-white hover:shadow-sm hover:text-green-700 rounded-lg transition-all">
                      <svg className="w-5 h-5 mr-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Track Progress
                    </Link>
                  </div>
                  
                  <div className="bg-gray-50 rounded-xl p-3">
                    <div className="text-sm font-medium text-gray-500 mb-2">Pengaturan</div>
                    <Link
                      href="/profile"
                      className="flex items-center py-2.5 px-3 text-gray-700 hover:bg-white hover:shadow-sm hover:text-green-700 rounded-lg transition-all">
                      <svg className="w-5 h-5 mr-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      Profil
                    </Link>
                    <Link
                      href="/diet-goals"
                      className="flex items-center py-2.5 px-3 text-gray-700 hover:bg-white hover:shadow-sm hover:text-green-700 rounded-lg transition-all">
                      <svg className="w-5 h-5 mr-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      Tujuan Diet
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center py-2.5 px-3 text-red-600 hover:bg-red-50 rounded-lg transition-all">
                      <svg className="w-5 h-5 mr-3 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Keluar
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex flex-col space-y-3 py-4">
                  <Link
                    href="/login"
                    className="flex justify-center items-center py-3 px-4 text-gray-700 border border-gray-200 hover:border-green-200 hover:text-green-700 rounded-xl transition-all">
                    Masuk
                  </Link>
                  <Link
                    href="/register"
                    className="flex justify-center items-center py-3 px-4 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl shadow-md">
                    Daftar Sekarang
                  </Link>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}