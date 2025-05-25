"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ProtectedLayout({ children }) {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    }
  }, []);

  return <>{children}</>;
}