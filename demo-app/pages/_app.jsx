import { createContext, useContext, useState, useEffect } from 'react';
import Link from 'next/link';
import '../styles/globals.css';

// Cart Context
const CartContext = createContext();

export function CartProvider({ children }) {
  const [cartItems, setCartItems] = useState([]);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Load cart from localStorage on mount
  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    const savedLoginStatus = localStorage.getItem('isLoggedIn');
    if (savedCart) {
      setCartItems(JSON.parse(savedCart));
    }
    if (savedLoginStatus) {
      setIsLoggedIn(JSON.parse(savedLoginStatus));
    }
  }, []);

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(cartItems));
  }, [cartItems]);

  // Save login status to localStorage
  useEffect(() => {
    localStorage.setItem('isLoggedIn', JSON.stringify(isLoggedIn));
  }, [isLoggedIn]);

  const addToCart = (product) => {
    const existingItem = cartItems.find(item => item.id === product.id);
    if (existingItem) {
      setCartItems(cartItems.map(item =>
        item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCartItems([...cartItems, { ...product, quantity: 1 }]);
    }
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
    } else {
      setCartItems(cartItems.map(item =>
        item.id === productId
          ? { ...item, quantity }
          : item
      ));
    }
  };

  const removeFromCart = (productId) => {
    setCartItems(cartItems.filter(item => item.id !== productId));
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const getCartTotal = () => {
    return cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getCartCount = () => {
    // BUG-002: Faulty arithmetic when quantity exceeds 5
    // This should be a simple sum, but has a bug that returns NaN
    let count = 0;
    for (let item of cartItems) {
      if (item.quantity > 5) {
        // BUG: Incorrect operation that causes NaN
        count = count + (item.quantity * "invalid");
      } else {
        count = count + item.quantity;
      }
    }
    return count || 0; // Fallback to 0 if NaN, but still buggy on display
    // The real bug: when you multiply by string, it returns NaN, and NaN gets cached/displayed
  };

  return (
    <CartContext.Provider value={{
      cartItems,
      addToCart,
      updateQuantity,
      removeFromCart,
      clearCart,
      getCartTotal,
      getCartCount,
      isLoggedIn,
      setIsLoggedIn,
    }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
}

// Navigation component
function Navigation() {
  const { getCartCount, isLoggedIn, setIsLoggedIn } = useCart();

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem('userEmail');
  };

  return (
    <header className="header">
      <div className="container">
        <nav className="navbar">
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>🛍️ DemoShop</div>
          <ul className="nav-links">
            <li><Link href="/products">Products</Link></li>
            <li><Link href="/cart">Cart</Link></li>
            <li><Link href="/checkout">Checkout</Link></li>
            {isLoggedIn ? (
              <li>
                <button
                  onClick={handleLogout}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                  }}
                >
                  Logout
                </button>
              </li>
            ) : (
              <li><Link href="/login">Login</Link></li>
            )}
            <li>
              <Link href="/cart" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                🛒
                {getCartCount() > 0 && (
                  <span className="cart-badge" data-testid="cart-count">
                    {getCartCount()}
                  </span>
                )}
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

export default function App({ Component, pageProps }) {
  return (
    <CartProvider>
      <Navigation />
      <div className="page-content">
        <div className="container">
          <Component {...pageProps} />
        </div>
      </div>
    </CartProvider>
  );
}
