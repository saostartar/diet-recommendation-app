import './globals.css';
import { Inter } from 'next/font/google';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { AuthProvider } from '@/context/AuthContext';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({ children }) {
  return (
    <html lang="id" className="scroll-smooth">
      <body className={`${inter.className} min-h-screen flex flex-col bg-gradient-to-b from-green-50 to-white text-gray-800`}>
      <AuthProvider>
        <Navbar />
        <main className="flex-grow">
          {children}
        </main>
        <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}

export const metadata = {
  title: 'Sistem Rekomendasi Diet',
  description: 'Sistem rekomendasi makanan sehat berbasis diet goals',
};