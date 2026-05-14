import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useCart } from './_app';

export default function Login() {
  const router = useRouter();
  const { setIsLoggedIn } = useCart();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      // BUG-001: Password validation is missing
      // This should validate that password is not empty, but it doesn't
      // The form will submit even with empty password
      
      if (!email) {
        setError('Email is required');
        setLoading(false);
        return;
      }

      // BUG STARTS HERE: No check for empty password
      // A correct implementation would have:
      // if (!password) {
      //   setError('Password is required');
      //   setLoading(false);
      //   return;
      // }

      // Simulate successful login
      localStorage.setItem('userEmail', email);
      setIsLoggedIn(true);
      setLoading(false);
      router.push('/products');
    }, 500);
  };

  return (
    <div style={{ maxWidth: '400px', margin: '40px auto' }}>
      <div className="card">
        <h1 style={{ marginBottom: '24px', textAlign: 'center' }}>Login</h1>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              data-testid="email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              data-testid="password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
            {/* BUG-001: No error message shown when password is empty */}
          </div>

          {error && <div className="error-message" data-testid="error-message">{error}</div>}

          <button
            type="submit"
            className="btn btn-primary"
            data-testid="login-button"
            style={{ width: '100%', marginTop: '16px' }}
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div style={{ marginTop: '16px', textAlign: 'center' }}>
          <Link href="#" style={{ color: '#667eea', textDecoration: 'none', fontSize: '14px' }}>
            Forgot password?
          </Link>
        </div>

        <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid #eee', textAlign: 'center', fontSize: '12px', color: '#666' }}>
          <p>Demo credentials (but bug allows login without password):</p>
          <p>Email: demo@example.com</p>
          <p>Password: demo123</p>
        </div>
      </div>
    </div>
  );
}
