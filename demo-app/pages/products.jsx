import { useState } from 'react';
import { useCart } from './_app';

const PRODUCTS = [
  {
    id: 1,
    name: 'Wireless Headphones',
    price: 79.99,
    emoji: '🎧',
    description: 'Premium sound quality with noise cancellation',
  },
  {
    id: 2,
    name: 'USB-C Cable',
    price: 12.99,
    emoji: '🔌',
    description: 'Fast charging, 3-meter length',
  },
  {
    id: 3,
    name: 'Phone Stand',
    price: 19.99,
    emoji: '📱',
    description: 'Adjustable, universal compatibility',
  },
  {
    id: 4,
    name: 'Portable Charger',
    price: 39.99,
    emoji: '🔋',
    description: '20000mAh capacity, dual USB ports',
  },
  {
    id: 5,
    name: 'Screen Protector',
    price: 9.99,
    emoji: '🛡️',
    description: 'Tempered glass, 2-pack',
  },
  {
    id: 6,
    name: 'Phone Case',
    price: 24.99,
    emoji: '📦',
    description: 'Durable silicone, multiple colors',
  },
];

export default function Products() {
  const { addToCart, getCartCount } = useCart();
  const [justAdded, setJustAdded] = useState(null);

  const handleAddToCart = (product) => {
    addToCart(product);
    setJustAdded(product.id);
    setTimeout(() => setJustAdded(null), 2000);
  };

  return (
    <div>
      <h1 style={{ marginBottom: '32px' }}>Our Products</h1>

      {/* Display cart count - BUG-002: Can show NaN when adding same product 6+ times */}
      <div
        style={{
          background: '#f0f0f0',
          padding: '12px',
          borderRadius: '4px',
          marginBottom: '24px',
          fontSize: '14px',
        }}
        data-testid="product-page-cart-count"
      >
        Items in cart: <strong data-testid="cart-count-display">{getCartCount()}</strong>
      </div>

      <div className="product-grid">
        {PRODUCTS.map((product) => (
          <div key={product.id} className="product-card">
            <div className="product-image">{product.emoji}</div>
            <div className="product-info">
              <div className="product-name" data-testid={`product-name-${product.id}`}>
                {product.name}
              </div>
              <div className="product-price" data-testid={`product-price-${product.id}`}>
                ${product.price.toFixed(2)}
              </div>
              <div className="product-description">{product.description}</div>

              <button
                className="btn btn-primary"
                onClick={() => handleAddToCart(product)}
                data-testid={`add-to-cart-btn-${product.id}`}
                style={{ width: '100%' }}
              >
                {justAdded === product.id ? '✓ Added!' : 'Add to Cart'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Hidden bug explanation panel */}
      <div
        style={{
          marginTop: '40px',
          padding: '16px',
          background: '#fffbea',
          border: '1px solid #ffd666',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#666',
        }}
        data-testid="bug-explanation"
      >
        <strong>BUG-002 Demo:</strong> Try adding the same product (e.g., Headphones) more than 5 times. 
        After 6+ additions, the cart count in the header may display as NaN. This happens due to faulty 
        arithmetic in the cart calculation when quantity exceeds a threshold.
      </div>
    </div>
  );
}
