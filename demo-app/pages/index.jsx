import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/products');
  }, [router]);

  return (
    <div style={{ textAlign: 'center', padding: '40px 0', color: '#666' }}>
      Loading DemoShop...
    </div>
  );
}
